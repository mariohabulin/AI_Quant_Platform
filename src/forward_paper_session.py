"""Bounded forward-paper observation with durable JSONL audit.

This module deliberately reuses the proven Coinbase live-paper bridge. It adds
operator-controlled duration and an append-only audit trail; it does not add a
real execution adapter or claim crash-transparent strategy-history recovery.
"""
from dataclasses import asdict, dataclass
import argparse
import json
from pathlib import Path
import sys

import pandas as pd

from src.coinbase_live_paper import build_live_paper_runtime
from src.coinbase_market_data import CoinbaseOneMinuteTradeAggregator, CoinbasePublicWebSocketTransport


@dataclass(frozen=True)
class ForwardPaperResult:
    processed_events: int
    rejected_events: int
    paper_orders: int
    final_equity: float
    final_position: float
    audit_path: str


class JsonlForwardAudit:
    """Append-only, line-delimited audit sink for supervised forward sessions."""

    def __init__(self, path):
        self.path = Path(path)
        if self.path.exists() and self.path.is_dir():
            raise ValueError("audit path must be a file path.")
        self.path.parent.mkdir(parents=True, exist_ok=True)

    @staticmethod
    def _json_default(value):
        if isinstance(value, pd.Timestamp):
            return value.isoformat()
        raise TypeError(f"Unsupported audit value: {type(value).__name__}")

    def append(self, record):
        if not isinstance(record, dict):
            raise TypeError("audit record must be a dict.")
        with self.path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(record, sort_keys=True, default=self._json_default) + "\n")


def run_forward_paper(
    transport=None,
    max_processed_bars=60,
    audit_path="runtime/forward_paper_audit.jsonl",
    output=print,
    now_fn=None,
):
    if not isinstance(max_processed_bars, int) or max_processed_bars <= 0:
        raise ValueError("max_processed_bars must be a positive integer.")

    audit = JsonlForwardAudit(audit_path)
    transport = transport or CoinbasePublicWebSocketTransport()
    aggregator = CoinbaseOneMinuteTradeAggregator(product_id="BTC-USD")
    runtime = build_live_paper_runtime()
    now_fn = now_fn or (lambda: pd.Timestamp.now(tz="UTC"))

    output(
        "Forward paper: BTC-USD 1m | REAL orders=IMPOSSIBLE | "
        f"paper execution=ON | max_bars={max_processed_bars}"
    )
    audit.append({"type": "SESSION_START", "at": now_fn(), "max_processed_bars": max_processed_bars})

    for message in transport:
        for bar in aggregator.ingest_message(message):
            snapshot = runtime.process_provider_message(bar, received_at=now_fn())
            if snapshot is None:
                record = {
                    "type": "REJECTED_BAR",
                    "timestamp": bar.timestamp,
                    "reason": runtime.health.reason,
                    "processed_events": runtime.health.processed_events,
                    "rejected_events": runtime.health.rejected_events,
                }
                audit.append(record)
                output(f"REJECTED {bar.timestamp}: {runtime.health.reason}")
                if runtime.stop_requested:
                    break
                continue

            event = runtime.session.engine.event_history[-1]
            broker = runtime.session.engine.paper_broker
            record = {
                "type": "PAPER_EVENT",
                "snapshot": asdict(snapshot),
                "event": asdict(event),
                "paper_orders": len(broker.order_history),
                "real_orders": 0,
            }
            audit.append(record)
            output(
                f"PAPER {snapshot.timestamp.isoformat()} price={snapshot.market_price:.2f} "
                f"signal={event.signal} status={event.status} position={snapshot.position_quantity:.8f} "
                f"equity={snapshot.equity:.2f} orders={len(broker.order_history)}"
            )

            if runtime.health.processed_events >= max_processed_bars:
                runtime.request_shutdown("Bounded forward-paper observation complete.")
                final = broker.account_snapshot(mark_price=snapshot.market_price)
                audit.append({
                    "type": "SESSION_END",
                    "reason": "MAX_BARS",
                    "processed_events": runtime.health.processed_events,
                    "rejected_events": runtime.health.rejected_events,
                    "paper_orders": len(broker.order_history),
                    "equity": final["equity"],
                    "position": broker.position_quantity,
                    "real_orders": 0,
                })
                return ForwardPaperResult(
                    runtime.health.processed_events,
                    runtime.health.rejected_events,
                    len(broker.order_history),
                    final["equity"],
                    broker.position_quantity,
                    str(audit.path),
                )
        if runtime.stop_requested:
            break

    broker = runtime.session.engine.paper_broker
    mark = broker.last_market_price or 1.0
    final = broker.account_snapshot(mark_price=mark)
    audit.append({
        "type": "SESSION_END",
        "reason": "TRANSPORT_ENDED",
        "processed_events": runtime.health.processed_events,
        "rejected_events": runtime.health.rejected_events,
        "paper_orders": len(broker.order_history),
        "equity": final["equity"],
        "position": broker.position_quantity,
        "real_orders": 0,
    })
    return ForwardPaperResult(
        runtime.health.processed_events,
        runtime.health.rejected_events,
        len(broker.order_history),
        final["equity"],
        broker.position_quantity,
        str(audit.path),
    )


def main(argv=None):
    parser = argparse.ArgumentParser(description="Supervised bounded Coinbase forward-paper session.")
    parser.add_argument("--bars", type=int, default=60, help="healthy 1m bars to process before exit")
    parser.add_argument("--audit", default="runtime/forward_paper_audit.jsonl", help="append-only JSONL audit path")
    args = parser.parse_args(argv)
    try:
        result = run_forward_paper(max_processed_bars=args.bars, audit_path=args.audit)
    except KeyboardInterrupt:
        print("Forward-paper session stopped by user. REAL orders=IMPOSSIBLE")
        return 130
    except Exception as exc:
        print(f"Forward-paper session failed safely: {type(exc).__name__}: {exc}", file=sys.stderr)
        return 1
    print(
        f"Forward-paper complete: processed={result.processed_events} rejected={result.rejected_events} "
        f"paper_orders={result.paper_orders} equity={result.final_equity:.2f} "
        f"position={result.final_position:.8f} audit={result.audit_path} REAL_orders=0"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
