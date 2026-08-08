from dataclasses import dataclass

import pandas as pd

from src.market_data_feed import HistoricalReplayFeed
from src.paper_trading import PaperTradingSession


@dataclass(frozen=True)
class ConsistencyDifference:
    field: str
    backtest_value: object
    replay_value: object
    message: str


@dataclass(frozen=True)
class ReplayConsistencyReport:
    status: str
    differences: tuple
    backtest_signals: tuple
    replay_signals: tuple
    backtest_trade_count: int
    replay_trade_count: int
    backtest_final_equity: float
    replay_final_equity: float
    backtest_open_position: bool
    replay_open_position: bool

    @property
    def is_consistent(self):
        return self.status == "CONSISTENT"


class ReplayConsistencyValidator:
    """Compare deterministic backtest and event-driven paper replay evidence.

    V1 deliberately compares only semantics that can be made equivalent today:
    signal sequence, completed fills/trades, quantities, execution prices,
    costs/P&L and final equity. Differences are evidence, not exceptions.
    """

    def __init__(self, backtest_engine, paper_session, tolerance=1e-9):
        if backtest_engine is None:
            raise ValueError("backtest_engine is required.")
        if not isinstance(paper_session, PaperTradingSession):
            raise TypeError("paper_session must be a PaperTradingSession.")
        if not isinstance(tolerance, (int, float)) or isinstance(tolerance, bool):
            raise TypeError("tolerance must be a number.")
        if tolerance < 0:
            raise ValueError("tolerance cannot be negative.")
        self.backtest_engine = backtest_engine
        self.paper_session = paper_session
        self.tolerance = float(tolerance)

    def _different(self, left, right):
        if isinstance(left, (int, float)) and isinstance(right, (int, float)):
            return abs(float(left) - float(right)) > self.tolerance
        return left != right

    @staticmethod
    def _filled_orders(session):
        return tuple(
            order for order in session.engine.paper_broker.order_history
            if order.status == "FILLED"
        )

    @staticmethod
    def _replay_round_trips(filled_orders):
        trips = []
        entry = None
        for order in filled_orders:
            if order.side == "BUY":
                entry = order
            elif order.side == "SELL" and entry is not None:
                trips.append((entry, order))
                entry = None
        return tuple(trips)

    def _add_difference(self, differences, field, backtest_value, replay_value, message):
        if self._different(backtest_value, replay_value):
            differences.append(ConsistencyDifference(
                field, backtest_value, replay_value, message
            ))

    def run(self, data, stop_resolver=None, target_resolver=None):
        if not isinstance(data, pd.DataFrame):
            raise TypeError("Consistency data must be a pandas DataFrame.")
        if data.empty:
            raise ValueError("Consistency data cannot be empty.")
        if self.paper_session.snapshot_history:
            raise ValueError("paper_session must be fresh before consistency validation.")

        backtest_result = self.backtest_engine.run(data.copy())
        backtest_signals = tuple(int(value) for value in backtest_result["Signal"])

        feed = HistoricalReplayFeed(data)
        for event in feed:
            stop_price = stop_resolver(event) if stop_resolver is not None else None
            target_price = target_resolver(event) if target_resolver is not None else None
            self.paper_session.process(
                event.data,
                stop_price=stop_price,
                target_price=target_price,
                timestamp=event.timestamp,
            )

        replay_signals = tuple(event.signal for event in self.paper_session.engine.event_history)
        broker = self.paper_session.engine.paper_broker
        filled_orders = self._filled_orders(self.paper_session)
        replay_trips = self._replay_round_trips(filled_orders)
        backtest_trades = tuple(self.backtest_engine.trade_history)
        differences = []

        self._add_difference(
            differences, "signal_sequence", backtest_signals, replay_signals,
            "Backtest and replay emitted different signal sequences."
        )
        self._add_difference(
            differences, "trade_count", len(backtest_trades), len(replay_trips),
            "Backtest and replay completed a different number of round trips."
        )

        for index, (backtest_trade, replay_trip) in enumerate(
            zip(backtest_trades, replay_trips), start=1
        ):
            buy, sell = replay_trip
            replay_costs = buy.commission + sell.commission
            replay_pnl = (
                sell.quantity * sell.fill_price - sell.commission
                - (buy.quantity * buy.fill_price + buy.commission)
            )
            comparisons = (
                ("quantity", backtest_trade["shares"], buy.quantity),
                ("entry_fill_price", backtest_trade["entry_price"], buy.fill_price),
                ("exit_fill_price", backtest_trade["exit_price"], sell.fill_price),
                ("commission", backtest_trade["total_commission"], replay_costs),
                ("profit_loss", backtest_trade["profit_loss"], replay_pnl),
            )
            for name, left, right in comparisons:
                self._add_difference(
                    differences, f"trade_{index}.{name}", left, right,
                    f"Completed trade {index} differs for {name}."
                )

        backtest_open_position = bool(self.backtest_engine.position)
        replay_open_position = broker.position_quantity > self.tolerance
        self._add_difference(
            differences, "open_position_state", backtest_open_position, replay_open_position,
            "Backtest and replay end with different open-position state; this may expose forced-close semantics."
        )

        final_market_price = float(data["Close"].iloc[-1])
        backtest_final_equity = float(self.backtest_engine._calculate_equity(final_market_price))
        replay_final_equity = float(broker.account_snapshot(final_market_price)["equity"])
        self._add_difference(
            differences, "final_equity", backtest_final_equity, replay_final_equity,
            "Backtest and replay final equity differ."
        )

        return ReplayConsistencyReport(
            status="CONSISTENT" if not differences else "DIVERGENT",
            differences=tuple(differences),
            backtest_signals=backtest_signals,
            replay_signals=replay_signals,
            backtest_trade_count=len(backtest_trades),
            replay_trade_count=len(replay_trips),
            backtest_final_equity=backtest_final_equity,
            replay_final_equity=replay_final_equity,
            backtest_open_position=backtest_open_position,
            replay_open_position=replay_open_position,
        )
