from dataclasses import dataclass
import argparse
import sys

import pandas as pd

from src.coinbase_market_data import (
    CoinbaseOneMinuteBarAdapter,
    CoinbaseOneMinuteTradeAggregator,
    CoinbasePublicWebSocketTransport,
)
from src.operational_runtime import PaperOperationalRuntime
from src.paper_broker import PaperBroker
from src.paper_trading import PaperTradingEngine, PaperTradingSession
from src.realtime_market_data import RealTimeMarketDataFeed
from src.risk_engine import RiskEngine
from src.strategies.ema_strategy import EMAStrategy
from src.strategy_library import StrategyLibrary


@dataclass(frozen=True)
class CoinbaseLivePaperResult:
    processed_events: int
    rejected_events: int
    paper_orders: int
    final_equity: float
    final_position: float


class AccumulatingPaperSession:
    """Bridge one-row real-time events into the historical frame strategies need."""

    def __init__(self, session, stop_fraction=0.01, reward_risk=3.0):
        if session is None:
            raise ValueError("session is required.")
        if not 0 < float(stop_fraction) < 1:
            raise ValueError("stop_fraction must be between zero and one.")
        if float(reward_risk) <= 0:
            raise ValueError("reward_risk must be positive.")
        self.session = session
        self.engine = session.engine
        self.stop_fraction = float(stop_fraction)
        self.reward_risk = float(reward_risk)
        self._history = pd.DataFrame()

    @property
    def snapshot_history(self):
        return self.session.snapshot_history

    @property
    def _last_timestamp(self):
        return self.session._last_timestamp

    @_last_timestamp.setter
    def _last_timestamp(self, value):
        self.session._last_timestamp = value

    def process(self, data, stop_price=None, target_price=None, timestamp=None, reconcile_long_exit=False):
        if data is None or getattr(data, "empty", True):
            raise ValueError("Live paper market data cannot be empty.")
        self._history = pd.concat([self._history, data]).sort_index()
        self._history = self._history[~self._history.index.duplicated(keep="last")]
        close = float(self._history["Close"].iloc[-1])
        stop = close * (1.0 - self.stop_fraction)
        target = close + (close - stop) * self.reward_risk
        return self.session.process(
            self._history.copy(),
            stop_price=stop,
            target_price=target,
            timestamp=timestamp,
            reconcile_long_exit=reconcile_long_exit,
        )


def build_live_paper_runtime(initial_cash=5000.0):
    library = StrategyLibrary()
    library.register(EMAStrategy())

    # StrategyEngine currently uses a legacy top-level feature_engine import.
    # Import locally after making src visible so the existing tested engine can
    # be reused without changing package semantics in this live milestone.
    import src.strategy_engine as strategy_engine_module
    strategy = strategy_engine_module.StrategyEngine(library, "ema_crossover")

    risk = RiskEngine(
        risk_per_trade=0.01,
        max_position_fraction=0.25,
        max_drawdown_fraction=0.10,
        daily_loss_limit=0.05,
        weekly_loss_limit=0.08,
        min_reward_risk=3.0,
    )
    broker = PaperBroker(initial_cash=initial_cash)
    engine = PaperTradingEngine(strategy, risk, broker)
    session = AccumulatingPaperSession(PaperTradingSession(engine))
    feed = RealTimeMarketDataFeed(
        CoinbaseOneMinuteBarAdapter(symbol="BTC/USD"),
        timeframe="1min", stale_after="2min", max_gap="2min",
    )
    return PaperOperationalRuntime(feed, session, max_consecutive_failures=3)


def run_coinbase_live_paper(transport=None, max_processed_bars=3, output=print, now_fn=None):
    if not isinstance(max_processed_bars, int) or max_processed_bars <= 0:
        raise ValueError("max_processed_bars must be a positive integer.")
    transport = transport or CoinbasePublicWebSocketTransport()
    aggregator = CoinbaseOneMinuteTradeAggregator(product_id="BTC-USD")
    runtime = build_live_paper_runtime()
    now_fn = now_fn or (lambda: pd.Timestamp.now(tz="UTC"))

    output("Coinbase live paper: BTC-USD 1m | REAL orders=IMPOSSIBLE | paper execution=ON")
    for message in transport:
        for bar in aggregator.ingest_message(message):
            snapshot = runtime.process_provider_message(bar, received_at=now_fn())
            if snapshot is None:
                output(f"REJECTED {bar.timestamp}: {runtime.health.reason}")
                if runtime.stop_requested:
                    break
                continue
            event = runtime.session.engine.event_history[-1]
            output(
                f"PAPER {snapshot.timestamp.isoformat()} price={snapshot.market_price:.2f} "
                f"signal={event.signal} status={event.status} position={snapshot.position_quantity:.8f} "
                f"equity={snapshot.equity:.2f} orders={len(runtime.session.engine.paper_broker.order_history)}"
            )
            if runtime.health.processed_events >= max_processed_bars:
                runtime.request_shutdown("Bounded live-paper observation complete.")
                broker = runtime.session.engine.paper_broker
                return CoinbaseLivePaperResult(
                    runtime.health.processed_events,
                    runtime.health.rejected_events,
                    len(broker.order_history),
                    broker.account_snapshot(mark_price=snapshot.market_price)["equity"],
                    broker.position_quantity,
                )
        if runtime.stop_requested:
            break

    broker = runtime.session.engine.paper_broker
    mark = broker.last_market_price or 1.0
    return CoinbaseLivePaperResult(
        runtime.health.processed_events,
        runtime.health.rejected_events,
        len(broker.order_history),
        broker.account_snapshot(mark_price=mark)["equity"],
        broker.position_quantity,
    )


def main(argv=None):
    parser = argparse.ArgumentParser(description="Bounded Coinbase live-data paper-trading probe.")
    parser.add_argument("--bars", type=int, default=3, help="healthy 1m bars to process before exit")
    args = parser.parse_args(argv)
    try:
        result = run_coinbase_live_paper(max_processed_bars=args.bars)
    except KeyboardInterrupt:
        print("Live-paper probe stopped by user. REAL orders=IMPOSSIBLE")
        return 130
    except Exception as exc:
        print(f"Live-paper probe failed safely: {type(exc).__name__}: {exc}", file=sys.stderr)
        return 1
    print(
        f"Live-paper complete: processed={result.processed_events} rejected={result.rejected_events} "
        f"paper_orders={result.paper_orders} equity={result.final_equity:.2f} "
        f"position={result.final_position:.8f} REAL_orders=0"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
