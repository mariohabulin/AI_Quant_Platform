from dataclasses import dataclass
import argparse
import itertools
import sys

import pandas as pd

from src.coinbase_market_data import (
    CoinbaseOneMinuteBarAdapter,
    CoinbaseOneMinuteTradeAggregator,
    CoinbasePublicWebSocketTransport,
)
from src.realtime_market_data import FeedHealthError, RealTimeMarketDataFeed


@dataclass(frozen=True)
class CoinbaseDryRunResult:
    completed_bars: int
    healthy_events: int
    last_timestamp: object = None


def run_coinbase_dry_run(transport=None, max_completed_bars=1, output=print, now_fn=None):
    """Observe public BTC-USD data and emit health-gated completed 1m bars only.

    This runner has no broker/session dependency and therefore cannot submit orders.
    It exits after ``max_completed_bars`` accepted bars so the first live probe is bounded.
    """
    if max_completed_bars <= 0:
        raise ValueError("max_completed_bars must be positive.")
    transport = transport or CoinbasePublicWebSocketTransport()
    aggregator = CoinbaseOneMinuteTradeAggregator(product_id="BTC-USD")
    feed = RealTimeMarketDataFeed(
        CoinbaseOneMinuteBarAdapter(symbol="BTC/USD"),
        timeframe="1min", stale_after="2min", max_gap="2min",
    )
    now_fn = now_fn or (lambda: pd.Timestamp.now(tz="UTC"))
    completed = healthy = 0
    last_timestamp = None
    output("Coinbase dry-run: BTC-USD public market data | execution=OFF")
    for message in transport:
        for bar in aggregator.ingest_message(message):
            completed += 1
            try:
                event = feed.ingest(bar, received_at=now_fn())
            except FeedHealthError as exc:
                output(f"REJECTED {bar.timestamp}: {exc}")
                continue
            healthy += 1
            last_timestamp = event.timestamp
            row = event.data.iloc[-1]
            output(
                f"HEALTHY BTC/USD 1m {event.timestamp.isoformat()} "
                f"O={row['Open']:.2f} H={row['High']:.2f} "
                f"L={row['Low']:.2f} C={row['Close']:.2f} V={row['Volume']:.8f}"
            )
            if healthy >= max_completed_bars:
                return CoinbaseDryRunResult(completed, healthy, last_timestamp)
    return CoinbaseDryRunResult(completed, healthy, last_timestamp)


def main(argv=None):
    parser = argparse.ArgumentParser(description="Bounded Coinbase BTC-USD public market-data dry-run.")
    parser.add_argument("--bars", type=int, default=1, help="healthy completed 1m bars to observe before exit")
    args = parser.parse_args(argv)
    try:
        result = run_coinbase_dry_run(max_completed_bars=args.bars)
    except KeyboardInterrupt:
        print("Dry-run stopped by user. execution=OFF")
        return 130
    except Exception as exc:
        print(f"Dry-run failed safely: {type(exc).__name__}: {exc}", file=sys.stderr)
        return 1
    print(f"Dry-run complete: healthy_events={result.healthy_events} execution=OFF")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
