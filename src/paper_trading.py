from dataclasses import dataclass


@dataclass(frozen=True)
class PaperTradingEvent:
    sequence: int
    timestamp: object
    event_type: str
    signal: int
    status: str
    reason: str
    order_id: str = None
    quantity: float = 0.0
    market_price: float = None
    fill_price: float = None
    risk_status: str = None


class PaperTradingEngine:
    """Deterministic orchestration boundary for forward/paper trading.

    Strategy decides direction, RiskEngine authorizes new long risk, and
    PaperBroker owns order execution/account state. This engine only
    coordinates those responsibilities and records an auditable event trail.
    """

    def __init__(self, strategy_engine, risk_engine, paper_broker):
        for dependency, name in (
            (strategy_engine, "strategy_engine"),
            (risk_engine, "risk_engine"),
            (paper_broker, "paper_broker"),
        ):
            if dependency is None:
                raise ValueError(f"{name} is required.")
        self.strategy_engine = strategy_engine
        self.risk_engine = risk_engine
        self.paper_broker = paper_broker
        self._events = []

    @property
    def event_history(self):
        return tuple(self._events)

    def _record(self, timestamp, event_type, signal, status, reason, **kwargs):
        event = PaperTradingEvent(
            sequence=len(self._events) + 1,
            timestamp=timestamp,
            event_type=event_type,
            signal=int(signal),
            status=status,
            reason=reason,
            **kwargs,
        )
        self._events.append(event)
        return event

    @staticmethod
    def _latest_price(strategy_result):
        if "Close" not in strategy_result.columns:
            raise ValueError("Strategy result must contain a 'Close' column.")
        price = strategy_result["Close"].iloc[-1]
        if price is None or price <= 0:
            raise ValueError("Latest Close price must be greater than zero.")
        return float(price)

    def process_market_event(self, data, stop_price=None, target_price=None, timestamp=None):
        """Process one deterministic market event using data available so far."""
        result = self.strategy_engine.run(data)
        if result.empty:
            raise ValueError("Strategy result cannot be empty.")

        signal = int(result["Signal"].iloc[-1])
        market_price = self._latest_price(result)
        event_timestamp = timestamp if timestamp is not None else result.index[-1]

        snapshot = self.paper_broker.account_snapshot(mark_price=market_price)
        protection = self.risk_engine.observe_equity(snapshot["equity"], event_timestamp)

        if signal == 0:
            return self._record(
                event_timestamp, "SIGNAL", signal, "NO_ACTION", "Strategy emitted HOLD.",
                market_price=market_price, risk_status=protection.status,
            )

        if signal == 1:
            if self.paper_broker.position_quantity > 0:
                return self._record(
                    event_timestamp, "SIGNAL", signal, "NO_ACTION",
                    "Long position already open.", market_price=market_price,
                    risk_status=protection.status,
                )
            if protection.status == "REJECT":
                return self._record(
                    event_timestamp, "RISK", signal, "REJECTED", protection.reason,
                    market_price=market_price, risk_status=protection.status,
                )
            if stop_price is None:
                raise ValueError("BUY signal requires stop_price for risk authorization.")

            decision = self.risk_engine.assess_long(
                snapshot["equity"], market_price, stop_price, target_price
            )
            if decision.status == "REJECT":
                return self._record(
                    event_timestamp, "RISK", signal, "REJECTED", decision.reason,
                    market_price=market_price, risk_status=decision.status,
                )

            order = self.paper_broker.submit_market_order(
                "BUY", decision.position_size, timestamp=event_timestamp
            )
            fill = self.paper_broker.execute_order(
                order.order_id, market_price, timestamp=event_timestamp
            )
            return self._record(
                event_timestamp, "ORDER", signal, fill.status,
                fill.reason or decision.reason, order_id=fill.order_id,
                quantity=fill.quantity, market_price=market_price,
                fill_price=fill.fill_price, risk_status=decision.status,
            )

        if signal == -1:
            quantity = self.paper_broker.position_quantity
            if quantity <= 0:
                return self._record(
                    event_timestamp, "SIGNAL", signal, "NO_ACTION",
                    "No long position to close.", market_price=market_price,
                    risk_status=protection.status,
                )
            order = self.paper_broker.submit_market_order(
                "SELL", quantity, timestamp=event_timestamp
            )
            fill = self.paper_broker.execute_order(
                order.order_id, market_price, timestamp=event_timestamp
            )
            return self._record(
                event_timestamp, "ORDER", signal, fill.status,
                fill.reason or "Exit order executed.", order_id=fill.order_id,
                quantity=fill.quantity, market_price=market_price,
                fill_price=fill.fill_price, risk_status=protection.status,
            )

        raise ValueError("Latest signal must be -1, 0, or 1.")
