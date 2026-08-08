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


@dataclass(frozen=True)
class PaperSessionSnapshot:
    sequence: int
    timestamp: object
    market_price: float
    cash: float
    position_quantity: float
    average_entry_price: float
    realized_pnl: float
    equity: float
    event_status: str
    event_type: str


class PaperTradingSession:
    """Stateful deterministic session over an ordered stream of market events.

    The session owns sequencing and account snapshots only. Strategy, risk and
    execution responsibilities remain delegated to PaperTradingEngine and its
    dependencies.
    """

    def __init__(self, engine):
        if engine is None:
            raise ValueError("engine is required.")
        if not isinstance(engine, PaperTradingEngine):
            raise TypeError("engine must be a PaperTradingEngine.")
        self.engine = engine
        self._snapshots = []
        self._last_timestamp = None

    @property
    def snapshot_history(self):
        return tuple(self._snapshots)

    @property
    def last_snapshot(self):
        return self._snapshots[-1] if self._snapshots else None

    def _validate_timestamp(self, timestamp):
        import pandas as pd
        try:
            ts = pd.Timestamp(timestamp)
        except Exception as exc:
            raise TypeError("Session timestamp must be datetime-like.") from exc
        if pd.isna(ts):
            raise ValueError("Session timestamp must be valid.")
        if self._last_timestamp is not None and ts <= self._last_timestamp:
            raise ValueError("Session market events must have strictly increasing timestamps.")
        return ts

    def process(self, data, stop_price=None, target_price=None, timestamp=None):
        if data is None or getattr(data, "empty", True):
            raise ValueError("Session market data cannot be empty.")
        event_timestamp = timestamp if timestamp is not None else data.index[-1]
        ts = self._validate_timestamp(event_timestamp)

        event = self.engine.process_market_event(
            data, stop_price=stop_price, target_price=target_price, timestamp=ts
        )
        account = self.engine.paper_broker.account_snapshot(mark_price=event.market_price)
        snapshot = PaperSessionSnapshot(
            sequence=len(self._snapshots) + 1,
            timestamp=ts,
            market_price=event.market_price,
            cash=account["cash"],
            position_quantity=account["position_quantity"],
            average_entry_price=account["average_entry_price"],
            realized_pnl=account["realized_pnl"],
            equity=account["equity"],
            event_status=event.status,
            event_type=event.event_type,
        )
        self._snapshots.append(snapshot)
        self._last_timestamp = ts
        return snapshot

    def run(self, events):
        """Process an iterable of event dictionaries in deterministic order.

        Each item requires ``data`` and may provide ``stop_price``,
        ``target_price`` and ``timestamp``.
        """
        if events is None:
            raise ValueError("events are required.")
        results = []
        for item in events:
            if not isinstance(item, dict) or "data" not in item:
                raise ValueError("Each session event must be a dict containing data.")
            results.append(self.process(
                item["data"],
                stop_price=item.get("stop_price"),
                target_price=item.get("target_price"),
                timestamp=item.get("timestamp"),
            ))
        return tuple(results)
