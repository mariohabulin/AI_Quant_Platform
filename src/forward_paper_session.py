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
from src.operational_runtime import JsonCheckpointStore
from src.realtime_market_data import FeedHealthError


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



class ForwardContinuityStore:
    """Atomic continuity state for supervised forward-paper restarts.

    Stores the existing operational checkpoint plus the two stateful pieces that
    live outside PaperOperationalRuntime: accumulated strategy history and the
    in-progress Coinbase one-minute aggregation bucket.
    """

    VERSION = 1

    def __init__(self, path):
        self.path = Path(path)

    @staticmethod
    def _frame_to_records(frame):
        if frame.empty:
            return []
        rows = []
        for timestamp, row in frame.iterrows():
            rows.append({"timestamp": pd.Timestamp(timestamp).isoformat(), **{
                key: None if pd.isna(value) else float(value) for key, value in row.items()
            }})
        return rows

    @staticmethod
    def _records_to_frame(records):
        if not records:
            return pd.DataFrame()
        rows = []
        index = []
        for record in records:
            record = dict(record)
            index.append(pd.Timestamp(record.pop("timestamp")))
            rows.append(record)
        return pd.DataFrame(rows, index=pd.DatetimeIndex(index))

    def save(self, runtime, aggregator):
        payload = {
            "version": self.VERSION,
            "runtime": runtime.export_checkpoint(),
            "strategy_history": self._frame_to_records(runtime.session._history),
            "aggregator": aggregator.export_state(),
        }
        self.path.parent.mkdir(parents=True, exist_ok=True)
        temporary = self.path.with_suffix(self.path.suffix + ".tmp")
        temporary.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
        temporary.replace(self.path)
        return self.path

    def load_into(self, runtime, aggregator):
        if not self.path.exists():
            return False
        try:
            payload = json.loads(self.path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            raise RuntimeError("Forward continuity state cannot be read safely.") from exc
        if payload.get("version") != self.VERSION:
            raise RuntimeError("Unsupported forward continuity state version.")
        runtime.restore(payload["runtime"])
        runtime.session._history = self._records_to_frame(payload.get("strategy_history", []))
        aggregator.restore_state(payload.get("aggregator", {}))
        return True


def bootstrap_continuity_from_audit(audit_path, state_path):
    """Create the first continuity checkpoint from the proven v1 JSONL audit.

    This one-time migration exists because Forward Paper Session v1 produced an
    audited open position before continuity state existed. It fails closed when
    the audit has no usable paper event.
    """
    audit_path = Path(audit_path)
    if not audit_path.exists():
        raise RuntimeError("Cannot bootstrap continuity: audit file does not exist.")
    rows = [json.loads(line) for line in audit_path.read_text(encoding="utf-8").splitlines() if line.strip()]
    events = [row for row in rows if row.get("type") == "PAPER_EVENT"]
    if not events:
        raise RuntimeError("Cannot bootstrap continuity: audit has no PAPER_EVENT records.")

    runtime = build_live_paper_runtime()
    aggregator = CoinbaseOneMinuteTradeAggregator(product_id="BTC-USD")
    broker = runtime.session.engine.paper_broker
    latest = events[-1]["snapshot"]
    broker.cash = float(latest["cash"])
    broker.position_quantity = float(latest["position_quantity"])
    broker.average_entry_price = float(latest["average_entry_price"])
    broker.position_cost_basis = broker.position_quantity * broker.average_entry_price
    broker.realized_pnl = float(latest["realized_pnl"])
    broker.last_market_price = float(latest["market_price"])
    broker._next_order_number = int(events[-1].get("paper_orders", 0)) + 1

    history_rows = []
    history_index = []
    for row in events:
        snap = row["snapshot"]
        price = float(snap["market_price"])
        history_index.append(pd.Timestamp(snap["timestamp"]))
        history_rows.append({"Open": price, "High": price, "Low": price, "Close": price, "Volume": 0.0})
    runtime.session._history = pd.DataFrame(history_rows, index=pd.DatetimeIndex(history_index))
    last_ts = pd.Timestamp(latest["timestamp"])
    runtime.session.session._last_timestamp = last_ts
    runtime.realtime_feed._last_timestamp = last_ts
    runtime.realtime_feed._accepted = len(events)
    runtime._processed = len(events)
    runtime._last_event_at = last_ts

    risk = runtime.session.engine.risk_engine
    equities = [float(row["snapshot"]["equity"]) for row in events]
    risk.peak_equity = max(equities)
    risk.day_key = last_ts.date()
    risk.day_start_equity = equities[0]
    iso = last_ts.isocalendar()
    risk.week_key = (int(iso.year), int(iso.week))
    risk.week_start_equity = equities[0]

    store = ForwardContinuityStore(state_path)
    store.save(runtime, aggregator)
    return broker.account_snapshot(mark_price=broker.last_market_price)

def run_forward_paper(
    transport=None,
    max_processed_bars=60,
    audit_path="runtime/forward_paper_audit.jsonl",
    output=print,
    now_fn=None,
    state_path="runtime/forward_paper_state.json",
    resume=True,
):
    if not isinstance(max_processed_bars, int) or max_processed_bars <= 0:
        raise ValueError("max_processed_bars must be a positive integer.")

    audit = JsonlForwardAudit(audit_path)
    transport = transport or CoinbasePublicWebSocketTransport()
    aggregator = CoinbaseOneMinuteTradeAggregator(product_id="BTC-USD")
    runtime = build_live_paper_runtime()
    continuity = ForwardContinuityStore(state_path)
    resumed = continuity.load_into(runtime, aggregator) if resume else False
    now_fn = now_fn or (lambda: pd.Timestamp.now(tz="UTC"))

    output(
        "Forward paper: BTC-USD 1m | REAL orders=IMPOSSIBLE | "
        f"paper execution=ON | max_bars={max_processed_bars} | resumed={resumed}"
    )
    audit.append({"type": "SESSION_START", "at": now_fn(), "max_processed_bars": max_processed_bars, "resumed": resumed})
    session_processed = 0
    session_rejected = 0
    rebase_boundary_pending = resumed
    rebase_boundary_kind = "RESTART" if resumed else None

    for message in transport:
        if isinstance(message, dict) and message.get("channel") == "_coinbase_transport":
            event = str(message.get("event", "UNKNOWN"))
            audit.append({
                "type": "TRANSPORT_EVENT",
                "event": event,
                "reason": message.get("reason"),
                "attempt": message.get("attempt"),
                "reconnect_count": message.get("reconnect_count"),
                "real_orders": 0,
            })
            output(f"TRANSPORT {event}: {message.get('reason') or 'connection restored'}")
            if event == "DISCONNECTED":
                aggregator.reset_stream_boundary()
                rebase_boundary_pending = True
                rebase_boundary_kind = "RECONNECT"
                continuity.save(runtime, aggregator)
            elif event == "RECONNECTED":
                rebase_boundary_pending = True
                rebase_boundary_kind = "RECONNECT"
            continue

        for bar in aggregator.ingest_message(message):
            received_at = now_fn()
            if rebase_boundary_pending:
                try:
                    rebased = runtime.realtime_feed.reconcile_after_restart(bar, received_at=received_at)
                except FeedHealthError:
                    rebased = False
                else:
                    rebase_boundary_pending = False
                if rebased:
                    boundary_kind = rebase_boundary_kind or "RESTART"
                    continuity.save(runtime, aggregator)
                    audit.append({
                        "type": "RESTART_REBASE" if boundary_kind == "RESTART" else "RECONNECT_REBASE",
                        "timestamp": bar.timestamp,
                        "reason": runtime.realtime_feed.health.reason,
                        "paper_orders": len(runtime.session.engine.paper_broker.order_history),
                        "real_orders": 0,
                    })
                    output(f"REBASE {bar.timestamp}: {boundary_kind.lower()} gap reconciled; no trading decision")
                    rebase_boundary_kind = None
                    continue
                rebase_boundary_kind = None

            snapshot = runtime.process_provider_message(bar, received_at=received_at)
            if snapshot is None:
                session_rejected += 1
                record = {
                    "type": "REJECTED_BAR",
                    "timestamp": bar.timestamp,
                    "reason": runtime.health.reason,
                    "processed_events": session_processed,
                    "rejected_events": session_rejected,
                    "runtime_processed_events": runtime.health.processed_events,
                    "runtime_rejected_events": runtime.health.rejected_events,
                }
                audit.append(record)
                output(f"REJECTED {bar.timestamp}: {runtime.health.reason}")
                if runtime.stop_requested:
                    break
                continue

            session_processed += 1
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
            continuity.save(runtime, aggregator)
            output(
                f"PAPER {snapshot.timestamp.isoformat()} price={snapshot.market_price:.2f} "
                f"signal={event.signal} status={event.status} position={snapshot.position_quantity:.8f} "
                f"equity={snapshot.equity:.2f} orders={len(broker.order_history)}"
            )

            if session_processed >= max_processed_bars:
                runtime.request_shutdown("Bounded forward-paper observation complete.")
                final = broker.account_snapshot(mark_price=snapshot.market_price)
                audit.append({
                    "type": "SESSION_END",
                    "reason": "MAX_BARS",
                    "processed_events": session_processed,
                    "rejected_events": session_rejected,
                    "runtime_processed_events": runtime.health.processed_events,
                    "runtime_rejected_events": runtime.health.rejected_events,
                    "paper_orders": len(broker.order_history),
                    "equity": final["equity"],
                    "position": broker.position_quantity,
                    "real_orders": 0,
                })
                return ForwardPaperResult(
                    session_processed,
                    session_rejected,
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
    end_reason = "RUNTIME_HALTED" if runtime.stop_requested and runtime.health.status == "HALTED" else "TRANSPORT_ENDED"
    audit.append({
        "type": "SESSION_END",
        "reason": end_reason,
        "processed_events": session_processed,
        "rejected_events": session_rejected,
        "runtime_processed_events": runtime.health.processed_events,
        "runtime_rejected_events": runtime.health.rejected_events,
        "paper_orders": len(broker.order_history),
        "equity": final["equity"],
        "position": broker.position_quantity,
        "real_orders": 0,
    })
    return ForwardPaperResult(
        session_processed,
        session_rejected,
        len(broker.order_history),
        final["equity"],
        broker.position_quantity,
        str(audit.path),
    )


DEFAULT_SESSION_AUDIT = "runtime/forward_paper_audit.jsonl"
DEFAULT_BOOTSTRAP_AUDIT = "docs/evidence/forward_paper_first_live.jsonl"


def main(argv=None):
    parser = argparse.ArgumentParser(description="Supervised bounded Coinbase forward-paper session.")
    parser.add_argument("--bars", type=int, default=60, help="healthy 1m bars to process before exit")
    parser.add_argument("--audit", default=DEFAULT_SESSION_AUDIT, help="append-only JSONL audit path")
    parser.add_argument("--state", default="runtime/forward_paper_state.json", help="atomic continuity state path")
    parser.add_argument("--bootstrap-from-audit", action="store_true", help="one-time migration of the v1 audited position into continuity state")
    parser.add_argument(
        "--bootstrap-audit",
        default=None,
        help="source audit for one-time continuity bootstrap; defaults to docs/evidence/forward_paper_first_live.jsonl",
    )
    args = parser.parse_args(argv)
    try:
        if args.bootstrap_from_audit:
            bootstrap_audit = args.bootstrap_audit
            if bootstrap_audit is None:
                bootstrap_audit = args.audit if args.audit != DEFAULT_SESSION_AUDIT else DEFAULT_BOOTSTRAP_AUDIT
            account = bootstrap_continuity_from_audit(bootstrap_audit, args.state)
            print(
                f"Continuity bootstrap complete: cash={account['cash']:.2f} "
                f"position={account['position_quantity']:.8f} equity={account['equity']:.2f} REAL_orders=0"
            )
            return 0
        result = run_forward_paper(max_processed_bars=args.bars, audit_path=args.audit, state_path=args.state)
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
