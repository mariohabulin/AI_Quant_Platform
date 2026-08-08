from dataclasses import dataclass


VALID_ORDER_STATUSES = {"SUBMITTED", "FILLED", "REJECTED", "CANCELLED"}
VALID_ORDER_SIDES = {"BUY", "SELL"}


@dataclass
class PaperOrder:
    order_id: str
    side: str
    quantity: float
    status: str = "SUBMITTED"
    submitted_at: object = None
    filled_at: object = None
    cancelled_at: object = None
    market_price: float = None
    fill_price: float = None
    commission: float = 0.0
    reason: str = None


class PaperBroker:
    """Deterministic long-only paper broker for market-order execution.

    The broker owns order lifecycle, fills and account state. It does not
    generate signals or make risk decisions. Orders are assumed to have been
    authorized before they reach this boundary.
    """

    def __init__(
        self,
        initial_cash=10000.0,
        commission_rate=0.0,
        slippage_rate=0.0,
        spread_rate=0.0,
    ):
        self.initial_cash = self._validate_positive_number(
            initial_cash, "Initial cash"
        )
        self.commission_rate = self._validate_rate(
            commission_rate, "Commission rate"
        )
        self.slippage_rate = self._validate_rate(
            slippage_rate, "Slippage rate"
        )
        self.spread_rate = self._validate_rate(spread_rate, "Spread rate")

        self.cash = self.initial_cash
        self.position_quantity = 0.0
        self.average_entry_price = 0.0
        self.position_cost_basis = 0.0
        self.realized_pnl = 0.0
        self.last_market_price = None
        self._next_order_number = 1
        self._orders = {}

    @staticmethod
    def _validate_positive_number(value, name):
        if not isinstance(value, (int, float)) or isinstance(value, bool):
            raise TypeError(f"{name} must be a number.")
        value = float(value)
        if value <= 0:
            raise ValueError(f"{name} must be greater than zero.")
        return value

    @staticmethod
    def _validate_rate(value, name):
        if not isinstance(value, (int, float)) or isinstance(value, bool):
            raise TypeError(f"{name} must be a number.")
        value = float(value)
        if value < 0:
            raise ValueError(f"{name} cannot be negative.")
        if value >= 1:
            raise ValueError(f"{name} must be less than 1.0.")
        return value

    @staticmethod
    def _validate_quantity(quantity):
        if not isinstance(quantity, (int, float)) or isinstance(quantity, bool):
            raise TypeError("Quantity must be a number.")
        quantity = float(quantity)
        if quantity <= 0:
            raise ValueError("Quantity must be greater than zero.")
        return quantity

    @staticmethod
    def _validate_market_price(market_price):
        if not isinstance(market_price, (int, float)) or isinstance(
            market_price, bool
        ):
            raise TypeError("Market price must be a number.")
        market_price = float(market_price)
        if market_price <= 0:
            raise ValueError("Market price must be greater than zero.")
        return market_price

    def _new_order_id(self):
        order_id = f"PB-{self._next_order_number:06d}"
        self._next_order_number += 1
        return order_id

    def _execution_price(self, market_price, side):
        half_spread = self.spread_rate / 2.0
        if side == "BUY":
            return market_price * (1.0 + self.slippage_rate + half_spread)
        if side == "SELL":
            return market_price * (1.0 - self.slippage_rate - half_spread)
        raise ValueError("Side must be BUY or SELL.")

    def submit_market_order(self, side, quantity, timestamp=None):
        if not isinstance(side, str):
            raise TypeError("Side must be a string.")
        side = side.upper()
        if side not in VALID_ORDER_SIDES:
            raise ValueError("Side must be BUY or SELL.")

        quantity = self._validate_quantity(quantity)
        order = PaperOrder(
            order_id=self._new_order_id(),
            side=side,
            quantity=quantity,
            submitted_at=timestamp,
        )
        self._orders[order.order_id] = order
        return order

    def get_order(self, order_id):
        if order_id not in self._orders:
            raise KeyError(f"Unknown order id: {order_id}")
        return self._orders[order_id]

    @property
    def order_history(self):
        return tuple(self._orders.values())

    def cancel_order(self, order_id, timestamp=None):
        order = self.get_order(order_id)
        if order.status != "SUBMITTED":
            raise ValueError("Only SUBMITTED orders can be cancelled.")
        order.status = "CANCELLED"
        order.cancelled_at = timestamp
        return order

    def _reject(self, order, reason, market_price, timestamp):
        order.status = "REJECTED"
        order.reason = reason
        order.market_price = market_price
        order.filled_at = timestamp
        self.last_market_price = market_price
        return order

    def execute_order(self, order_id, market_price, timestamp=None):
        order = self.get_order(order_id)
        if order.status != "SUBMITTED":
            raise ValueError("Only SUBMITTED orders can be executed.")

        market_price = self._validate_market_price(market_price)
        fill_price = self._execution_price(market_price, order.side)
        notional = order.quantity * fill_price
        commission = notional * self.commission_rate

        if order.side == "BUY":
            total_cost = notional + commission
            if total_cost > self.cash + 1e-12:
                return self._reject(
                    order,
                    "INSUFFICIENT_CASH",
                    market_price,
                    timestamp,
                )

            previous_quantity = self.position_quantity
            new_quantity = previous_quantity + order.quantity
            weighted_execution_cost = (
                self.average_entry_price * previous_quantity
                + fill_price * order.quantity
            )

            self.cash -= total_cost
            if abs(self.cash) < 1e-12:
                self.cash = 0.0
            self.position_quantity = new_quantity
            self.average_entry_price = weighted_execution_cost / new_quantity
            self.position_cost_basis += total_cost

        else:
            if order.quantity > self.position_quantity + 1e-12:
                return self._reject(
                    order,
                    "INSUFFICIENT_POSITION",
                    market_price,
                    timestamp,
                )

            quantity_before = self.position_quantity
            basis_fraction = order.quantity / quantity_before
            allocated_cost_basis = self.position_cost_basis * basis_fraction
            net_proceeds = notional - commission

            self.cash += net_proceeds
            self.realized_pnl += net_proceeds - allocated_cost_basis
            self.position_quantity -= order.quantity
            self.position_cost_basis -= allocated_cost_basis

            if self.position_quantity <= 1e-12:
                self.position_quantity = 0.0
                self.position_cost_basis = 0.0
                self.average_entry_price = 0.0

        order.status = "FILLED"
        order.market_price = market_price
        order.fill_price = fill_price
        order.commission = commission
        order.filled_at = timestamp
        self.last_market_price = market_price
        return order

    def account_snapshot(self, mark_price=None):
        if mark_price is not None:
            mark_price = self._validate_market_price(mark_price)
        elif self.last_market_price is not None:
            mark_price = self.last_market_price
        elif self.position_quantity > 0:
            raise ValueError(
                "A mark price is required when an open position has no market price."
            )
        else:
            mark_price = 0.0

        market_value = self.position_quantity * mark_price
        equity = self.cash + market_value

        return {
            "cash": self.cash,
            "position_quantity": self.position_quantity,
            "average_entry_price": self.average_entry_price,
            "position_cost_basis": self.position_cost_basis,
            "market_value": market_value,
            "realized_pnl": self.realized_pnl,
            "equity": equity,
        }
