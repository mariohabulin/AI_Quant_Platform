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
from src.coinbase_market_data import (
    CoinbaseHybridGapRecovery,
    CoinbaseOneMinuteTradeAggregator,
    CoinbasePublicWebSocketTransport,
    CoinbaseTradeOrderingError,
)
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

    def __init__(self, path, clock=None):
        self.path = Path(path)
        self.clock = clock or (lambda: pd.Timestamp.now(tz="UTC"))
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
        record = dict(record)
        recorded_at = pd.Timestamp(self.clock())
        if pd.isna(recorded_at):
            raise ValueError("audit clock returned an invalid timestamp.")
        record.setdefault("recorded_at", recorded_at)
        with self.path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(record, sort_keys=True, default=self._json_default) + "\n")



class ForwardContinuityStore:
    """Atomic continuity state for supervised forward-paper restarts.

    Stores the existing operational checkpoint plus the two stateful pieces that
    live outside PaperOperationalRuntime: accumulated strategy history and the
    in-progress Coinbase one-minute aggregation bucket.
    """

    VERSION = 1

    def __init__(self, path, clock=None):
        self.path = Path(path)
        self.clock = clock or (lambda: pd.Timestamp.now(tz="UTC"))

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
        saved_at = pd.Timestamp(self.clock())
        if pd.isna(saved_at):
            raise ValueError("continuity clock returned an invalid timestamp.")
        payload = {
            "version": self.VERSION,
            "saved_at": saved_at.isoformat(),
            "runtime": runtime.export_checkpoint(),
            "strategy_history": self._frame_to_records(runtime.session._history),
            "aggregator": aggregator.export_state(),
            "pending_reconciliation": getattr(runtime, "_forward_pending_reconciliation", None),
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
        runtime._forward_pending_reconciliation = payload.get("pending_reconciliation")
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


def _is_completed_provider_replay(runtime, bar):
    """Return True when a completed bar is at/behind the accepted feed watermark."""
    last_accepted = runtime.realtime_feed._last_timestamp
    return last_accepted is not None and pd.Timestamp(bar.timestamp) <= pd.Timestamp(last_accepted)


def _trusted_live_bucket(message_timestamp, timeframe):
    """Return the first full bucket after a provider stream boundary."""
    try:
        timestamp = pd.Timestamp(message_timestamp)
        if pd.isna(timestamp):
            raise ValueError("Provider boundary timestamp is missing.")
        if timestamp.tzinfo is None:
            timestamp = timestamp.tz_localize("UTC")
        else:
            timestamp = timestamp.tz_convert("UTC")
        return timestamp.floor("min") + pd.Timedelta(timeframe)
    except Exception:
        return None


def _utc_timestamp_or_none(value):
    """Normalize provider event time without weakening downstream validation."""
    try:
        timestamp = pd.Timestamp(value)
        if pd.isna(timestamp):
            return None
        if timestamp.tzinfo is None:
            return timestamp.tz_localize("UTC")
        return timestamp.tz_convert("UTC")
    except Exception:
        return None


def _quarantine_pre_snapshot_boundary_trades(message, trusted_live_bucket):
    """Remove provider history older than the latest trusted snapshot floor.

    Coinbase can send a new ``market_trades`` snapshot on an established
    connection and then replay snapshot-era trades in later ``update`` events.
    Those rows are provider history, not new incremental evidence.  The returned
    message is a copy, so transport evidence remains unchanged for callers and
    tests. Invalid trade timestamps are deliberately retained for the strict
    aggregator to reject rather than being silently discarded.
    """
    if (
        not isinstance(message, dict)
        or message.get("channel") != "market_trades"
    ):
        return message, None
    floor = _utc_timestamp_or_none(trusted_live_bucket)
    events = message.get("events")
    if floor is None or not isinstance(events, list):
        return message, None

    filtered_events = []
    dropped = []
    for event in events:
        if not isinstance(event, dict) or not isinstance(
            event.get("trades"), list
        ):
            filtered_events.append(event)
            continue
        retained = []
        for trade in event["trades"]:
            timestamp = (
                _utc_timestamp_or_none(trade.get("time"))
                if isinstance(trade, dict)
                else None
            )
            if timestamp is not None and timestamp < floor:
                dropped.append((trade, timestamp))
            else:
                retained.append(trade)
        if len(retained) == len(event["trades"]):
            filtered_events.append(event)
        else:
            filtered_event = dict(event)
            filtered_event["trades"] = retained
            filtered_events.append(filtered_event)

    if not dropped:
        return message, None
    filtered_message = dict(message)
    filtered_message["events"] = filtered_events
    trade_ids = [
        str(trade["trade_id"])
        for trade, _ in dropped
        if isinstance(trade, dict) and trade.get("trade_id") is not None
    ]
    timestamps = [timestamp for _, timestamp in dropped]
    return filtered_message, {
        "trade_count": len(dropped),
        "first_trade_id": trade_ids[0] if trade_ids else None,
        "last_trade_id": trade_ids[-1] if trade_ids else None,
        "oldest_trade_timestamp": min(timestamps),
        "newest_trade_timestamp": max(timestamps),
    }


def _apply_rest_backfill_bar(runtime, bar):
    """Catch up market/strategy/risk state without retroactive order execution."""
    market_event = runtime.realtime_feed.ingest_backfill(bar)
    timestamp = pd.Timestamp(market_event.timestamp)
    latest = market_event.data.loc[[timestamp]].copy()
    runtime.session._history = pd.concat([runtime.session._history, latest]).sort_index()
    runtime.session._history = runtime.session._history[~runtime.session._history.index.duplicated(keep="last")]
    runtime.session._last_timestamp = timestamp

    broker = runtime.session.engine.paper_broker
    close = float(latest["Close"].iloc[-1])
    broker.last_market_price = close
    account = broker.account_snapshot(mark_price=close)
    runtime.session.engine.risk_engine.observe_equity(account["equity"], timestamp)
    runtime._last_event_at = timestamp
    return account


def _strategy_activity_diagnostics(runtime):
    """Return read-only diagnostics for the current strategy state.

    Diagnostics explain observed signal behavior; they never alter strategy, risk,
    broker, feed-health, or execution decisions.
    """
    engine = runtime.session.engine.strategy_engine
    result = engine.run(runtime.session._history)
    strategy = engine.strategy
    latest = result.iloc[-1]
    diagnostics = {
        "strategy": engine.strategy_name,
        "signal": int(latest["Signal"]),
    }
    fast_period = getattr(strategy, "fast_period", None)
    slow_period = getattr(strategy, "slow_period", None)
    if fast_period is not None and slow_period is not None:
        fast_col = f"EMA_{fast_period}"
        slow_col = f"EMA_{slow_period}"
        if fast_col in result.columns and slow_col in result.columns:
            fast = float(latest[fast_col])
            slow = float(latest[slow_col])
            spread = fast - slow
            diagnostics.update({
                "fast_period": int(fast_period),
                "slow_period": int(slow_period),
                "fast_value": fast,
                "slow_value": slow,
                "spread": spread,
                "spread_bps": (spread / slow * 10000.0) if slow else 0.0,
                "relation": "ABOVE" if spread > 0 else "BELOW" if spread < 0 else "EQUAL",
            })
    return diagnostics


def _run_forward_paper_once(
    transport=None,
    max_processed_bars=60,
    audit_path="runtime/forward_paper_audit.jsonl",
    output=print,
    now_fn=None,
    state_path="runtime/forward_paper_state.json",
    resume=True,
    gap_recovery=None,
):
    if not isinstance(max_processed_bars, int) or max_processed_bars <= 0:
        raise ValueError("max_processed_bars must be a positive integer.")

    audit = JsonlForwardAudit(audit_path)
    transport = transport or CoinbasePublicWebSocketTransport()
    aggregator = CoinbaseOneMinuteTradeAggregator(product_id="BTC-USD")
    runtime = build_live_paper_runtime()
    runtime._forward_pending_reconciliation = None
    continuity = ForwardContinuityStore(state_path)
    resumed = continuity.load_into(runtime, aggregator) if resume else False
    if resumed:
        # A persisted partial trade bucket cannot be trusted across process downtime.
        # The historical gap will be rebuilt from completed REST candles instead.
        aggregator.reset_stream_boundary()
    gap_recovery = gap_recovery or CoinbaseHybridGapRecovery()
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
    stream_boundary_pending = False
    stream_trusted_live_bucket = None
    stream_boundary_source = None
    snapshot_quarantine_floor = None
    snapshot_boundary_sequence_num = None
    snapshot_boundary_bar_drops = set()
    transport_fatal = False
    backfill_fatal = False

    for message in transport:
        if isinstance(message, dict) and message.get("channel") == "_coinbase_transport":
            event = str(message.get("event", "UNKNOWN"))
            if event == "PROVIDER_MESSAGE_REPLAY_DROPPED":
                audit.append({
                    "type": "PROVIDER_MESSAGE_REPLAY_DROPPED",
                    "failure_kind": message.get("failure_kind"),
                    "provider_channel": message.get("provider_channel"),
                    "previous_sequence_num": message.get(
                        "previous_sequence_num"
                    ),
                    "observed_sequence_num": message.get(
                        "observed_sequence_num"
                    ),
                    "message_timestamp": message.get("message_timestamp"),
                    "trade_count": message.get("trade_count"),
                    "first_trade_id": message.get("first_trade_id"),
                    "last_trade_id": message.get("last_trade_id"),
                    "processed_events": session_processed,
                    "rejected_events": session_rejected,
                    "runtime_processed_events": runtime.health.processed_events,
                    "runtime_rejected_events": runtime.health.rejected_events,
                    "real_orders": 0,
                })
                output(
                    "PROVIDER_MESSAGE_REPLAY_DROPPED: "
                    f"channel={message.get('provider_channel')} "
                    f"sequence={message.get('observed_sequence_num')} "
                    f"previous={message.get('previous_sequence_num')} "
                    f"trades={message.get('trade_count')}"
                )
                continue
            if event == "PROVIDER_SNAPSHOT_BOUNDARY":
                audit.append({
                    "type": "PROVIDER_SNAPSHOT_BOUNDARY",
                    "provider_channel": message.get("provider_channel"),
                    "message_sequence_num": message.get(
                        "message_sequence_num"
                    ),
                    "message_timestamp": message.get("message_timestamp"),
                    "snapshot_event_count": message.get(
                        "snapshot_event_count"
                    ),
                    "trade_count": message.get("trade_count"),
                    "first_trade_id": message.get("first_trade_id"),
                    "last_trade_id": message.get("last_trade_id"),
                    "oldest_trade_timestamp": message.get(
                        "oldest_trade_timestamp"
                    ),
                    "newest_trade_timestamp": message.get(
                        "newest_trade_timestamp"
                    ),
                    "processed_events": session_processed,
                    "rejected_events": session_rejected,
                    "runtime_processed_events": runtime.health.processed_events,
                    "runtime_rejected_events": runtime.health.rejected_events,
                    "real_orders": 0,
                })
                aggregator.reset_stream_boundary()
                if not rebase_boundary_pending:
                    rebase_boundary_kind = "SNAPSHOT"
                rebase_boundary_pending = True
                stream_boundary_pending = True
                stream_boundary_source = "SNAPSHOT"
                candidate_trusted_live_bucket = _trusted_live_bucket(
                    message.get("message_timestamp"),
                    runtime.realtime_feed.timeframe,
                )
                if candidate_trusted_live_bucket is None:
                    candidate_trusted_live_bucket = _trusted_live_bucket(
                        message.get("newest_trade_timestamp"),
                        runtime.realtime_feed.timeframe,
                    )
                if candidate_trusted_live_bucket is not None:
                    if snapshot_quarantine_floor is None:
                        snapshot_quarantine_floor = (
                            candidate_trusted_live_bucket
                        )
                    else:
                        snapshot_quarantine_floor = max(
                            snapshot_quarantine_floor,
                            candidate_trusted_live_bucket,
                        )
                snapshot_boundary_sequence_num = message.get(
                    "message_sequence_num"
                )
                stream_trusted_live_bucket = snapshot_quarantine_floor
                if stream_trusted_live_bucket is not None:
                    boundary_bar = (
                        stream_trusted_live_bucket
                        - runtime.realtime_feed.timeframe
                    )
                    if boundary_bar not in snapshot_boundary_bar_drops:
                        snapshot_boundary_bar_drops.add(boundary_bar)
                        audit.append({
                            "type": "PROVIDER_SNAPSHOT_BOUNDARY_BAR_DROPPED",
                            "timestamp": boundary_bar,
                            "trusted_live_bucket": stream_trusted_live_bucket,
                            "boundary_source": "SNAPSHOT",
                            "reason": (
                                "Bar intersects the provider snapshot boundary "
                                "and is quarantined before aggregation."
                            ),
                            "processed_events": session_processed,
                            "rejected_events": session_rejected,
                            "runtime_processed_events": (
                                runtime.health.processed_events
                            ),
                            "runtime_rejected_events": (
                                runtime.health.rejected_events
                            ),
                            "real_orders": 0,
                        })
                        output(
                            "PROVIDER_SNAPSHOT_BOUNDARY_BAR_DROPPED: "
                            f"bar={boundary_bar.isoformat()} "
                            f"trusted_from={stream_trusted_live_bucket.isoformat()}"
                        )
                continuity.save(runtime, aggregator)
                output(
                    "PROVIDER_SNAPSHOT_BOUNDARY: "
                    f"sequence={message.get('message_sequence_num')} "
                    f"trades={message.get('trade_count')} "
                    f"oldest={message.get('oldest_trade_timestamp')} "
                    f"trusted_from={stream_trusted_live_bucket}"
                )
                continue
            audit.append({
                "type": "TRANSPORT_EVENT",
                "event": event,
                "reason": message.get("reason"),
                "failure_kind": message.get("failure_kind"),
                "provider_channel": message.get("provider_channel"),
                "attempt": message.get("attempt"),
                "reconnect_count": message.get("reconnect_count"),
                "outage_seconds": message.get("outage_seconds"),
                "previous_sequence_num": message.get(
                    "previous_sequence_num"
                ),
                "expected_sequence_num": message.get(
                    "expected_sequence_num"
                ),
                "observed_sequence_num": message.get(
                    "observed_sequence_num"
                ),
                "message_timestamp": message.get("message_timestamp"),
                "real_orders": 0,
            })
            output(f"TRANSPORT {event}: {message.get('reason') or 'connection restored'}")
            if event == "DISCONNECTED":
                aggregator.reset_stream_boundary()
                rebase_boundary_pending = True
                rebase_boundary_kind = "RECONNECT"
                if message.get("failure_kind") in {
                    "PROVIDER_SEQUENCE_GAP",
                    "PROVIDER_SEQUENCE_MISSING",
                    "PROVIDER_SEQUENCE_INVALID",
                }:
                    stream_boundary_pending = True
                    stream_trusted_live_bucket = None
                    stream_boundary_source = "SEQUENCE"
                continuity.save(runtime, aggregator)
            elif event == "RECONNECTED":
                rebase_boundary_pending = True
                rebase_boundary_kind = "RECONNECT"
                if stream_boundary_pending:
                    stream_trusted_live_bucket = _trusted_live_bucket(
                        message.get("message_timestamp"),
                        runtime.realtime_feed.timeframe,
                    )
            elif event == "RECONNECT_EXHAUSTED":
                transport_fatal = True
                continuity.save(runtime, aggregator)
            continue

        message, quarantined = _quarantine_pre_snapshot_boundary_trades(
            message, snapshot_quarantine_floor
        )
        if quarantined is not None:
            audit.append({
                "type": "PROVIDER_SNAPSHOT_QUARANTINE_TRADES_DROPPED",
                "snapshot_message_sequence_num": (
                    snapshot_boundary_sequence_num
                ),
                "message_sequence_num": (
                    message.get("sequence_num")
                    if isinstance(message, dict)
                    else None
                ),
                "message_timestamp": (
                    message.get("timestamp")
                    if isinstance(message, dict)
                    else None
                ),
                "trusted_live_bucket": snapshot_quarantine_floor,
                **quarantined,
                "processed_events": session_processed,
                "rejected_events": session_rejected,
                "runtime_processed_events": runtime.health.processed_events,
                "runtime_rejected_events": runtime.health.rejected_events,
                "real_orders": 0,
            })
            output(
                "PROVIDER_SNAPSHOT_QUARANTINE_TRADES_DROPPED: "
                f"sequence={message.get('sequence_num')} "
                f"trades={quarantined['trade_count']} "
                f"trusted_from={snapshot_quarantine_floor.isoformat()}"
            )

        try:
            completed_bars = aggregator.ingest_message(message)
        except CoinbaseTradeOrderingError as exc:
            audit.append({
                "type": "LATE_TRADE_REJECTED",
                **exc.diagnostics(),
                "processed_events": session_processed,
                "rejected_events": session_rejected,
                "runtime_processed_events": runtime.health.processed_events,
                "runtime_rejected_events": runtime.health.rejected_events,
                "real_orders": 0,
            })
            continuity.save(runtime, aggregator)
            broker = runtime.session.engine.paper_broker
            mark = broker.last_market_price or 1.0
            final = broker.account_snapshot(mark_price=mark)
            audit.append({
                "type": "SESSION_END",
                "reason": "ORDERING_FATAL",
                "processed_events": session_processed,
                "rejected_events": session_rejected,
                "runtime_processed_events": runtime.health.processed_events,
                "runtime_rejected_events": runtime.health.rejected_events,
                "paper_orders": len(broker.order_history),
                "equity": final["equity"],
                "position": broker.position_quantity,
                "real_orders": 0,
            })
            output(
                "LATE_TRADE_REJECTED: "
                f"trade={exc.trade_timestamp.isoformat()} "
                f"active_bucket={exc.active_bucket.isoformat()} "
                f"lateness={exc.lateness_seconds:.3f}s"
            )
            raise

        for bar in completed_bars:
            received_at = now_fn()

            # Coinbase can replay already-completed minutes after a stream boundary
            # (and occasionally across normal websocket delivery). Those bars are
            # non-actionable because the feed has already accepted an equal/newer
            # timestamp. Drop them before Feed Health so benign provider replay does
            # not consume the runtime's consecutive-failure budget. Fresh forward
            # bars still pass through the full stale/order/gap health gate below.
            last_accepted = runtime.realtime_feed._last_timestamp
            if _is_completed_provider_replay(runtime, bar):
                audit.append({
                    "type": "PROVIDER_REPLAY_DROPPED",
                    "timestamp": bar.timestamp,
                    "last_accepted_timestamp": last_accepted,
                    "reason": "Completed provider bar already accepted or older than feed watermark.",
                    "processed_events": session_processed,
                    "rejected_events": session_rejected,
                    "runtime_processed_events": runtime.health.processed_events,
                    "runtime_rejected_events": runtime.health.rejected_events,
                    "real_orders": 0,
                })
                output(f"REPLAY_DROP {bar.timestamp}: already at/below accepted feed watermark")
                continue

            if stream_boundary_pending:
                bar_timestamp = pd.Timestamp(bar.timestamp)
                if stream_trusted_live_bucket is None:
                    # Without a trustworthy reconnect timestamp, conservatively
                    # treat the first completed bucket as partial and require the
                    # following bucket to establish a fully observed live boundary.
                    stream_trusted_live_bucket = (
                        bar_timestamp + runtime.realtime_feed.timeframe
                    )
                if bar_timestamp < stream_trusted_live_bucket:
                    snapshot_boundary = stream_boundary_source == "SNAPSHOT"
                    audit_type = (
                        "PROVIDER_SNAPSHOT_BOUNDARY_BAR_DROPPED"
                        if snapshot_boundary
                        else "PROVIDER_SEQUENCE_BOUNDARY_BAR_DROPPED"
                    )
                    reason = (
                        "Bar began before the provider snapshot boundary and "
                        "may contain only a partial live minute."
                        if snapshot_boundary
                        else "Bar may contain only post-reconnect trades after "
                        "a provider sequence integrity failure."
                    )
                    already_audited = (
                        snapshot_boundary
                        and bar_timestamp in snapshot_boundary_bar_drops
                    )
                    if not already_audited:
                        audit.append({
                            "type": audit_type,
                            "timestamp": bar_timestamp,
                            "trusted_live_bucket": stream_trusted_live_bucket,
                            "boundary_source": stream_boundary_source,
                            "reason": reason,
                            "processed_events": session_processed,
                            "rejected_events": session_rejected,
                            "runtime_processed_events": runtime.health.processed_events,
                            "runtime_rejected_events": runtime.health.rejected_events,
                            "real_orders": 0,
                        })
                        output(
                            f"{audit_type}: "
                            f"bar={bar_timestamp.isoformat()} "
                            f"trusted_from={stream_trusted_live_bucket.isoformat()}"
                        )
                    continue
                stream_boundary_pending = False
                stream_trusted_live_bucket = None
                stream_boundary_source = None

            if rebase_boundary_pending:
                last_accepted = runtime.realtime_feed._last_timestamp
                gap = None if last_accepted is None else pd.Timestamp(bar.timestamp) - pd.Timestamp(last_accepted)
                # A stream boundary requires exact 1m continuity, not merely
                # compliance with the normal live-feed max-gap tolerance. If the
                # first completed live bar is two minutes after the accepted
                # watermark, exactly one minute is missing and must be REST
                # recovered before trading resumes.
                if (
                    last_accepted is not None
                    and gap is not None
                    and gap > runtime.realtime_feed.timeframe
                ):
                    boundary_kind = rebase_boundary_kind or "RESTART"
                    try:
                        startup_catchup = boundary_kind == "RESTART" and hasattr(gap_recovery, "recover_startup")
                        if startup_catchup:
                            recovered = gap_recovery.recover_startup(last_accepted, bar.timestamp)
                        else:
                            recovered = gap_recovery.recover(last_accepted, bar.timestamp)
                        audit_type = "STARTUP_CATCHUP_BAR" if startup_catchup else "REST_BACKFILL_BAR"
                        complete_type = "STARTUP_CATCHUP_COMPLETE" if startup_catchup else "REST_BACKFILL_COMPLETE"
                        for recovered_bar in recovered:
                            account = _apply_rest_backfill_bar(runtime, recovered_bar)
                            recovery_diagnostics = _strategy_activity_diagnostics(runtime)
                            if (
                                account["position_quantity"] > 0
                                and recovery_diagnostics.get("signal") == -1
                                and runtime._forward_pending_reconciliation is None
                            ):
                                runtime._forward_pending_reconciliation = {
                                    "kind": "LONG_EXIT",
                                    "detected_at": pd.Timestamp(recovered_bar.timestamp).isoformat(),
                                    "strategy": recovery_diagnostics.get("strategy"),
                                    "boundary_kind": boundary_kind,
                                }
                                audit.append({
                                    "type": "RECOVERY_CROSSOVER_DETECTED",
                                    **runtime._forward_pending_reconciliation,
                                    "position": account["position_quantity"],
                                    "real_orders": 0,
                                })
                            audit.append({
                                "type": audit_type,
                                "timestamp": recovered_bar.timestamp,
                                "close": recovered_bar.close,
                                "equity": account["equity"],
                                "position": account["position_quantity"],
                                "boundary_kind": boundary_kind,
                                "real_orders": 0,
                            })
                        audit.append({
                            "type": complete_type,
                            "boundary_kind": boundary_kind,
                            "from_timestamp": last_accepted,
                            "to_timestamp": bar.timestamp,
                            "recovered_bars": len(recovered),
                            "real_orders": 0,
                        })
                        label = "STARTUP_CATCHUP" if startup_catchup else "REST_BACKFILL"
                        output(
                            f"{label} {len(recovered)} bars: "
                            f"{pd.Timestamp(last_accepted)} -> {pd.Timestamp(bar.timestamp)}; trading resumes on live bar"
                        )
                        continuity.save(runtime, aggregator)
                        rebase_boundary_pending = False
                        rebase_boundary_kind = None
                    except Exception as exc:
                        backfill_fatal = True
                        continuity.save(runtime, aggregator)
                        audit.append({
                            "type": "REST_BACKFILL_FAILED",
                            "boundary_kind": boundary_kind,
                            "from_timestamp": last_accepted,
                            "to_timestamp": bar.timestamp,
                            "reason": f"{type(exc).__name__}: {exc}",
                            "real_orders": 0,
                        })
                        output(f"REST_BACKFILL_FAILED: {type(exc).__name__}: {exc}")
                        break
                else:
                    rebase_boundary_pending = False
                    rebase_boundary_kind = None

            pending_reconciliation = runtime._forward_pending_reconciliation
            reconcile_long_exit = bool(
                pending_reconciliation
                and pending_reconciliation.get("kind") == "LONG_EXIT"
                and runtime.session.engine.paper_broker.position_quantity > 0
            )
            snapshot = runtime.process_provider_message(
                bar, received_at=received_at, reconcile_long_exit=reconcile_long_exit
            )
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

            if reconcile_long_exit:
                event = runtime.session.engine.event_history[-1]
                audit.append({
                    "type": "POST_RECOVERY_RECONCILIATION",
                    "detected_at": pending_reconciliation.get("detected_at"),
                    "executed_at": snapshot.timestamp,
                    "strategy": pending_reconciliation.get("strategy"),
                    "status": event.status,
                    "order_id": event.order_id,
                    "fill_price": event.fill_price,
                    "real_orders": 0,
                })
                runtime._forward_pending_reconciliation = None

            session_processed += 1
            event = runtime.session.engine.event_history[-1]
            broker = runtime.session.engine.paper_broker
            record = {
                "type": "PAPER_EVENT",
                "snapshot": asdict(snapshot),
                "event": asdict(event),
                "strategy_diagnostics": _strategy_activity_diagnostics(runtime),
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
        if backfill_fatal or runtime.stop_requested:
            break

    broker = runtime.session.engine.paper_broker
    mark = broker.last_market_price or 1.0
    final = broker.account_snapshot(mark_price=mark)
    if backfill_fatal:
        end_reason = "BACKFILL_FATAL"
    elif transport_fatal:
        end_reason = "TRANSPORT_FATAL"
    elif runtime.stop_requested and runtime.health.status == "HALTED":
        end_reason = "RUNTIME_HALTED"
    else:
        end_reason = "TRANSPORT_ENDED"
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


def _audit_session_start_count(audit_path):
    path = Path(audit_path)
    if not path.exists():
        return 0
    if not path.is_file():
        return None
    try:
        rows = [
            json.loads(line)
            for line in path.read_text(encoding="utf-8").splitlines()
            if line.strip()
        ]
    except (OSError, json.JSONDecodeError):
        return None
    return sum(row.get("type") == "SESSION_START" for row in rows)


def _append_operator_stop(audit_path, state_path, prior_start_count):
    """Close the latest open audit session from already-durable evidence."""
    path = Path(audit_path)
    if not path.exists() or not path.is_file():
        return False
    try:
        rows = [
            json.loads(line)
            for line in path.read_text(encoding="utf-8").splitlines()
            if line.strip()
        ]
    except (OSError, json.JSONDecodeError):
        return False
    starts = [index for index, row in enumerate(rows) if row.get("type") == "SESSION_START"]
    if not starts or prior_start_count is None or len(starts) <= prior_start_count:
        return False
    session = rows[starts[-1]:]
    if any(row.get("type") == "SESSION_END" for row in session):
        return False

    paper = [row for row in session if row.get("type") == "PAPER_EVENT"]
    rejected = [row for row in session if row.get("type") == "REJECTED_BAR"]
    latest_paper = paper[-1] if paper else {}
    snapshot = latest_paper.get("snapshot", {})
    paper_orders = int(latest_paper.get("paper_orders", 0))
    equity = snapshot.get("equity")
    position = snapshot.get("position_quantity")
    runtime_processed = len(paper)
    runtime_rejected = len(rejected)

    state_file = Path(state_path)
    if state_file.exists() and state_file.is_file():
        try:
            state = json.loads(state_file.read_text(encoding="utf-8"))
            runtime_state = state.get("runtime", {})
            counters = runtime_state.get("runtime", {})
            broker = runtime_state.get("broker", {})
            runtime_processed = int(
                counters.get("processed_events", runtime_processed)
            )
            runtime_rejected = int(
                counters.get("rejected_events", runtime_rejected)
            )
            if equity is None:
                cash = float(broker.get("cash", 0.0))
                position = float(broker.get("position_quantity", 0.0))
                mark = broker.get("last_market_price")
                mark = 0.0 if mark is None else float(mark)
                equity = cash + position * mark
        except (OSError, json.JSONDecodeError, TypeError, ValueError):
            pass

    JsonlForwardAudit(path).append({
        "type": "SESSION_END",
        "reason": "OPERATOR_STOP",
        "processed_events": len(paper),
        "rejected_events": len(rejected),
        "runtime_processed_events": runtime_processed,
        "runtime_rejected_events": runtime_rejected,
        "paper_orders": paper_orders,
        "equity": equity,
        "position": position,
        "real_orders": 0,
    })
    return True


def run_forward_paper(
    transport=None,
    max_processed_bars=60,
    audit_path="runtime/forward_paper_audit.jsonl",
    output=print,
    now_fn=None,
    state_path="runtime/forward_paper_state.json",
    resume=True,
    gap_recovery=None,
):
    prior_start_count = _audit_session_start_count(audit_path)
    try:
        return _run_forward_paper_once(
            transport=transport,
            max_processed_bars=max_processed_bars,
            audit_path=audit_path,
            output=output,
            now_fn=now_fn,
            state_path=state_path,
            resume=resume,
            gap_recovery=gap_recovery,
        )
    except KeyboardInterrupt:
        _append_operator_stop(audit_path, state_path, prior_start_count)
        raise


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
