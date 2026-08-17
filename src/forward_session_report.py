"""Deterministic report for the latest forward-paper JSONL session.

The reporter is intentionally read-only. It summarizes the latest SESSION_START
through SESSION_END block and fails closed on malformed/incomplete audit data.
"""
from dataclasses import asdict, dataclass
import argparse
import json
from pathlib import Path
from collections import Counter
import sys

import pandas as pd


@dataclass(frozen=True)
class ForwardSessionReport:
    status: str
    resumed: bool
    processed_events: int
    rejected_events: int
    rebase_events: int
    paper_orders: int
    buy_signals: int
    sell_signals: int
    hold_signals: int
    filled_orders: int
    risk_allow: int
    risk_reduce: int
    risk_reject: int
    start_equity: float
    final_equity: float
    net_pnl: float
    max_drawdown: float
    final_position: float
    real_orders: int
    audit_complete: bool
    end_reason: str
    transport_disconnects: int
    transport_reconnects: int
    reconnect_exhausted: int
    reconnect_success_rate: float
    total_outage_seconds: float
    max_outage_seconds: float
    disconnect_reason_counts: dict
    provider_replay_drops: int
    provider_message_replay_drops: int
    provider_sequence_boundary_bar_drops: int
    provider_snapshot_boundaries: int
    provider_snapshot_boundary_bar_drops: int
    provider_snapshot_quarantine_trade_drops: int
    rest_backfill_bars: int
    startup_catchup_bars: int
    rest_backfill_failures: int
    market_span_minutes: float
    expected_contiguous_minutes: float
    observed_gap_minutes: float
    signal_activity_rate: float
    risk_rejection_rate: float
    risk_rejection_reasons: dict
    reward_risk_evaluations: int
    reward_risk_rejections: int
    reward_risk_ratio_min: float
    reward_risk_ratio_max: float
    minimum_reward_risk_values: tuple
    strategy_name: str
    strategy_relation_counts: dict
    strategy_spread_bps_min: float
    strategy_spread_bps_max: float
    strategy_spread_bps_avg: float
    event_reason_counts: dict
    live_relation_transitions: dict
    live_crossovers: int
    recovery_crossovers: int
    recovery_crossover_kinds: dict
    max_above_run_bars: int
    max_below_run_bars: int
    current_relation: str
    current_relation_run_bars: int
    bars_with_open_position: int
    bars_flat: int
    open_position_equity_change: float


def _read_rows(path):
    path = Path(path)
    if not path.exists() or not path.is_file():
        raise RuntimeError("Forward audit file does not exist.")
    rows = []
    for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        if not line.strip():
            continue
        try:
            row = json.loads(line)
        except json.JSONDecodeError as exc:
            raise RuntimeError(f"Forward audit contains invalid JSON at line {number}.") from exc
        if not isinstance(row, dict) or "type" not in row:
            raise RuntimeError(f"Forward audit record at line {number} is invalid.")
        rows.append(row)
    if not rows:
        raise RuntimeError("Forward audit is empty.")
    return rows


def _latest_session(rows):
    starts = [i for i, row in enumerate(rows) if row.get("type") == "SESSION_START"]
    if not starts:
        raise RuntimeError("Forward audit has no SESSION_START record.")
    start = starts[-1]
    session = rows[start:]
    ends = [i for i, row in enumerate(session) if row.get("type") == "SESSION_END"]
    if not ends:
        raise RuntimeError("Latest forward session is incomplete: SESSION_END is missing.")
    end = ends[0]
    trailing_session_start = any(row.get("type") == "SESSION_START" for row in session[1:end + 1])
    if trailing_session_start:
        raise RuntimeError("Forward audit session boundaries are inconsistent.")
    return session[:end + 1]


def build_forward_session_report(audit_path="runtime/forward_paper_audit.jsonl"):
    rows = _latest_session(_read_rows(audit_path))
    paper = [row for row in rows if row.get("type") == "PAPER_EVENT"]
    rejected = [row for row in rows if row.get("type") == "REJECTED_BAR"]
    rebases = [row for row in rows if row.get("type") in {"RESTART_REBASE", "RECONNECT_REBASE"}]
    end = rows[-1]
    transport = [row for row in rows if row.get("type") == "TRANSPORT_EVENT"]
    replay_drops = [row for row in rows if row.get("type") == "PROVIDER_REPLAY_DROPPED"]
    message_replay_drops = [
        row
        for row in rows
        if row.get("type") == "PROVIDER_MESSAGE_REPLAY_DROPPED"
    ]
    sequence_boundary_bar_drops = [
        row
        for row in rows
        if row.get("type") == "PROVIDER_SEQUENCE_BOUNDARY_BAR_DROPPED"
    ]
    snapshot_boundaries = [
        row
        for row in rows
        if row.get("type") == "PROVIDER_SNAPSHOT_BOUNDARY"
    ]
    snapshot_boundary_bar_drops = [
        row
        for row in rows
        if row.get("type") == "PROVIDER_SNAPSHOT_BOUNDARY_BAR_DROPPED"
    ]
    snapshot_quarantine_trade_drops = [
        row
        for row in rows
        if row.get("type")
        == "PROVIDER_SNAPSHOT_QUARANTINE_TRADES_DROPPED"
    ]
    rest_backfill = [row for row in rows if row.get("type") == "REST_BACKFILL_BAR"]
    startup_catchup = [row for row in rows if row.get("type") == "STARTUP_CATCHUP_BAR"]
    rest_backfill_failures = [row for row in rows if row.get("type") == "REST_BACKFILL_FAILED"]

    if not paper:
        raise RuntimeError("Latest forward session has no PAPER_EVENT records to report.")

    snapshots = [row.get("snapshot", {}) for row in paper]
    events = [row.get("event", {}) for row in paper]
    equities = [float(snapshot["equity"]) for snapshot in snapshots]
    start_equity = equities[0]
    peak = equities[0]
    max_drawdown = 0.0
    for equity in equities:
        peak = max(peak, equity)
        if peak > 0:
            max_drawdown = max(max_drawdown, (peak - equity) / peak)

    signals = [int(event.get("signal", 0)) for event in events]
    risk_statuses = [str(event.get("risk_status", "")) for event in events]
    statuses = [str(event.get("status", "")) for event in events]
    real_orders_values = [int(row.get("real_orders", 0)) for row in rows if "real_orders" in row]
    real_orders = max(real_orders_values, default=0)
    final_equity = float(end.get("equity", equities[-1]))
    final_position = float(end.get("position", snapshots[-1].get("position_quantity", 0.0)))

    disconnects = sum(row.get("event") == "DISCONNECTED" for row in transport)
    reconnects = sum(row.get("event") == "RECONNECTED" for row in transport)
    reconnect_exhausted = sum(row.get("event") == "RECONNECT_EXHAUSTED" for row in transport)
    reconnect_success_rate = (reconnects / disconnects) if disconnects else 1.0
    outage_values = [
        float(row.get("outage_seconds"))
        for row in transport
        if row.get("event") in {"RECONNECTED", "RECONNECT_EXHAUSTED"}
        and row.get("outage_seconds") is not None
    ]
    total_outage_seconds = sum(outage_values)
    max_outage_seconds = max(outage_values, default=0.0)
    disconnect_reason_counts = dict(sorted(Counter(
        str(row.get("failure_kind") or "UNKNOWN")
        for row in transport
        if row.get("event") == "DISCONNECTED"
    ).items()))

    continuity_timestamps = []
    for snapshot in snapshots:
        value = snapshot.get("timestamp")
        if value is not None:
            try:
                continuity_timestamps.append(pd.Timestamp(value))
            except Exception:
                pass
    for row in rest_backfill + startup_catchup:
        value = row.get("timestamp")
        if value is not None:
            try:
                continuity_timestamps.append(pd.Timestamp(value))
            except Exception:
                pass
    continuity_timestamps = sorted(set(continuity_timestamps))
    if len(continuity_timestamps) >= 2:
        market_span_minutes = (max(continuity_timestamps) - min(continuity_timestamps)).total_seconds() / 60.0
        expected_contiguous_minutes = float(len(continuity_timestamps) - 1)
        observed_gap_minutes = max(0.0, market_span_minutes - expected_contiguous_minutes)
    else:
        market_span_minutes = 0.0
        expected_contiguous_minutes = 0.0
        observed_gap_minutes = 0.0

    actionable_signals = sum(signal != 0 for signal in signals)
    signal_activity_rate = actionable_signals / len(signals) if signals else 0.0
    risk_rejections = [event for event in events if str(event.get("risk_status", "")) == "REJECT"]
    risk_rejection_rate = len(risk_rejections) / actionable_signals if actionable_signals else 0.0
    risk_rejection_reasons = dict(sorted(Counter(
        str(event.get("reason") or "UNKNOWN") for event in risk_rejections
    ).items()))
    reward_risk_events = [
        event for event in events
        if event.get("planned_reward_risk_ratio") is not None
    ]
    reward_risk_ratios = [
        float(event["planned_reward_risk_ratio"]) for event in reward_risk_events
    ]
    minimum_reward_risk_values = tuple(sorted(set(
        float(event["minimum_reward_risk"])
        for event in reward_risk_events
        if event.get("minimum_reward_risk") is not None
    )))

    diagnostics = [row.get("strategy_diagnostics", {}) for row in paper]
    diagnostics = [item for item in diagnostics if isinstance(item, dict) and item]
    strategy_names = [str(item.get("strategy")) for item in diagnostics if item.get("strategy")]
    strategy_name = strategy_names[-1] if strategy_names else "UNKNOWN"
    strategy_relation_counts = dict(sorted(Counter(
        str(item.get("relation")) for item in diagnostics if item.get("relation")
    ).items()))
    spread_bps = [float(item["spread_bps"]) for item in diagnostics if item.get("spread_bps") is not None]
    strategy_spread_bps_min = min(spread_bps, default=0.0)
    strategy_spread_bps_max = max(spread_bps, default=0.0)
    strategy_spread_bps_avg = sum(spread_bps) / len(spread_bps) if spread_bps else 0.0
    event_reason_counts = dict(sorted(Counter(
        str(event.get("reason") or "UNKNOWN") for event in events
    ).items()))

    relations = [
        str(row.get("strategy_diagnostics", {}).get("relation"))
        for row in paper
        if isinstance(row.get("strategy_diagnostics"), dict)
        and row.get("strategy_diagnostics", {}).get("relation") in {"ABOVE", "BELOW"}
    ]
    relation_transitions = Counter()
    for previous, current in zip(relations, relations[1:]):
        if previous != current:
            relation_transitions[f"{previous}->{current}"] += 1
    live_relation_transitions = dict(sorted(relation_transitions.items()))
    live_crossovers = sum(relation_transitions.values())

    recovery_crossover_rows = [row for row in rows if row.get("type") == "RECOVERY_CROSSOVER_DETECTED"]
    recovery_crossovers = len(recovery_crossover_rows)
    recovery_crossover_kinds = dict(sorted(Counter(
        str(row.get("boundary_kind") or "UNKNOWN") for row in recovery_crossover_rows
    ).items()))

    max_runs = {"ABOVE": 0, "BELOW": 0}
    current_relation = relations[-1] if relations else "UNKNOWN"
    current_relation_run_bars = 0
    run_relation = None
    run_length = 0
    for relation in relations:
        if relation == run_relation:
            run_length += 1
        else:
            run_relation = relation
            run_length = 1
        max_runs[relation] = max(max_runs[relation], run_length)
    if relations:
        current_relation_run_bars = run_length

    position_quantities = [float(snapshot.get("position_quantity", 0.0)) for snapshot in snapshots]
    bars_with_open_position = sum(abs(quantity) > 0.0 for quantity in position_quantities)
    bars_flat = len(position_quantities) - bars_with_open_position
    open_equities = [equity for equity, quantity in zip(equities, position_quantities) if abs(quantity) > 0.0]
    open_position_equity_change = (open_equities[-1] - open_equities[0]) if open_equities else 0.0

    processed = int(end.get("processed_events", len(paper)))
    rejected_count = int(end.get("rejected_events", len(rejected)))
    complete = (
        rows[0].get("type") == "SESSION_START"
        and end.get("type") == "SESSION_END"
        and processed == len(paper)
        and rejected_count == len(rejected)
        and real_orders == 0
    )
    status = "PASS" if complete and end.get("reason") == "MAX_BARS" else "FAIL"

    return ForwardSessionReport(
        status=status,
        resumed=bool(rows[0].get("resumed", False)),
        processed_events=processed,
        rejected_events=rejected_count,
        rebase_events=len(rebases),
        paper_orders=int(end.get("paper_orders", max((row.get("paper_orders", 0) for row in paper), default=0))),
        buy_signals=sum(signal > 0 for signal in signals),
        sell_signals=sum(signal < 0 for signal in signals),
        hold_signals=sum(signal == 0 for signal in signals),
        filled_orders=sum(status == "FILLED" for status in statuses),
        risk_allow=sum(status == "ALLOW" for status in risk_statuses),
        risk_reduce=sum(status == "REDUCE" for status in risk_statuses),
        risk_reject=sum(status == "REJECT" for status in risk_statuses),
        start_equity=start_equity,
        final_equity=final_equity,
        net_pnl=final_equity - start_equity,
        max_drawdown=max_drawdown,
        final_position=final_position,
        real_orders=real_orders,
        audit_complete=complete,
        end_reason=str(end.get("reason", "UNKNOWN")),
        transport_disconnects=disconnects,
        transport_reconnects=reconnects,
        reconnect_exhausted=reconnect_exhausted,
        reconnect_success_rate=reconnect_success_rate,
        total_outage_seconds=total_outage_seconds,
        max_outage_seconds=max_outage_seconds,
        disconnect_reason_counts=disconnect_reason_counts,
        provider_replay_drops=len(replay_drops),
        provider_message_replay_drops=len(message_replay_drops),
        provider_sequence_boundary_bar_drops=len(
            sequence_boundary_bar_drops
        ),
        provider_snapshot_boundaries=len(snapshot_boundaries),
        provider_snapshot_boundary_bar_drops=len(
            snapshot_boundary_bar_drops
        ),
        provider_snapshot_quarantine_trade_drops=sum(
            int(row.get("trade_count", 0))
            for row in snapshot_quarantine_trade_drops
        ),
        rest_backfill_bars=len(rest_backfill),
        startup_catchup_bars=len(startup_catchup),
        rest_backfill_failures=len(rest_backfill_failures),
        market_span_minutes=market_span_minutes,
        expected_contiguous_minutes=expected_contiguous_minutes,
        observed_gap_minutes=observed_gap_minutes,
        signal_activity_rate=signal_activity_rate,
        risk_rejection_rate=risk_rejection_rate,
        risk_rejection_reasons=risk_rejection_reasons,
        reward_risk_evaluations=len(reward_risk_events),
        reward_risk_rejections=sum(
            str(event.get("risk_status", "")) == "REJECT"
            for event in reward_risk_events
        ),
        reward_risk_ratio_min=min(reward_risk_ratios, default=0.0),
        reward_risk_ratio_max=max(reward_risk_ratios, default=0.0),
        minimum_reward_risk_values=minimum_reward_risk_values,
        strategy_name=strategy_name,
        strategy_relation_counts=strategy_relation_counts,
        strategy_spread_bps_min=strategy_spread_bps_min,
        strategy_spread_bps_max=strategy_spread_bps_max,
        strategy_spread_bps_avg=strategy_spread_bps_avg,
        event_reason_counts=event_reason_counts,
        live_relation_transitions=live_relation_transitions,
        live_crossovers=live_crossovers,
        recovery_crossovers=recovery_crossovers,
        recovery_crossover_kinds=recovery_crossover_kinds,
        max_above_run_bars=max_runs["ABOVE"],
        max_below_run_bars=max_runs["BELOW"],
        current_relation=current_relation,
        current_relation_run_bars=current_relation_run_bars,
        bars_with_open_position=bars_with_open_position,
        bars_flat=bars_flat,
        open_position_equity_change=open_position_equity_change,
    )


def format_forward_session_report(report):
    return "\n".join([
        f"Extended Forward Session Report | status={report.status} | audit_complete={report.audit_complete} | resumed={report.resumed}",
        f"bars: processed={report.processed_events} rejected={report.rejected_events} rebases={report.rebase_events}",
        f"signals: BUY={report.buy_signals} SELL={report.sell_signals} HOLD={report.hold_signals}",
        f"risk: ALLOW={report.risk_allow} REDUCE={report.risk_reduce} REJECT={report.risk_reject}",
        f"orders: paper={report.paper_orders} filled={report.filled_orders} REAL={report.real_orders}",
        f"equity: start={report.start_equity:.2f} final={report.final_equity:.2f} net_pnl={report.net_pnl:.2f} max_drawdown={report.max_drawdown:.4%}",
        f"transport: disconnects={report.transport_disconnects} reconnects={report.transport_reconnects} success={report.reconnect_success_rate:.1%} exhausted={report.reconnect_exhausted} replay_drops={report.provider_replay_drops} message_replay_drops={report.provider_message_replay_drops} sequence_boundary_drops={report.provider_sequence_boundary_bar_drops} snapshot_boundaries={report.provider_snapshot_boundaries} snapshot_boundary_drops={report.provider_snapshot_boundary_bar_drops} snapshot_quarantine_trades={report.provider_snapshot_quarantine_trade_drops}",
        f"transport_quality: outage_total={report.total_outage_seconds:.1f}s outage_max={report.max_outage_seconds:.1f}s reasons={report.disconnect_reason_counts}",
        f"hybrid_recovery: backfill_bars={report.rest_backfill_bars} startup_catchup_bars={report.startup_catchup_bars} failures={report.rest_backfill_failures}",
        f"continuity: market_span={report.market_span_minutes:.1f}m expected_contiguous={report.expected_contiguous_minutes:.1f}m observed_gap={report.observed_gap_minutes:.1f}m",
        f"activity: signal_rate={report.signal_activity_rate:.1%} risk_reject_rate={report.risk_rejection_rate:.1%} reject_reasons={report.risk_rejection_reasons}",
        f"reward_risk: evaluations={report.reward_risk_evaluations} rejected={report.reward_risk_rejections} observed[min/max]={report.reward_risk_ratio_min:.6f}/{report.reward_risk_ratio_max:.6f} required={report.minimum_reward_risk_values}",
        f"strategy_behavior: strategy={report.strategy_name} relation={report.strategy_relation_counts} spread_bps[min/avg/max]={report.strategy_spread_bps_min:.2f}/{report.strategy_spread_bps_avg:.2f}/{report.strategy_spread_bps_max:.2f}",
        f"strategy_transitions: live={report.live_crossovers} {report.live_relation_transitions} recovery={report.recovery_crossovers} {report.recovery_crossover_kinds}",
        f"strategy_runs: max_ABOVE={report.max_above_run_bars} max_BELOW={report.max_below_run_bars} current={report.current_relation}:{report.current_relation_run_bars}",
        f"position_behavior: open_bars={report.bars_with_open_position} flat_bars={report.bars_flat} open_equity_change={report.open_position_equity_change:.2f}",
        f"decision_reasons: {report.event_reason_counts}",
        f"final_position={report.final_position:.8f} end_reason={report.end_reason}",
    ])


def main(argv=None):
    parser = argparse.ArgumentParser(description="Report the latest audited forward-paper session.")
    parser.add_argument("--audit", default="runtime/forward_paper_audit.jsonl")
    parser.add_argument("--json", action="store_true", help="emit machine-readable JSON")
    args = parser.parse_args(argv)
    try:
        report = build_forward_session_report(args.audit)
    except Exception as exc:
        print(f"Forward session report failed safely: {type(exc).__name__}: {exc}", file=sys.stderr)
        return 1
    if args.json:
        print(json.dumps(asdict(report), sort_keys=True))
    else:
        print(format_forward_session_report(report))
    return 0 if report.status == "PASS" else 2


if __name__ == "__main__":
    raise SystemExit(main())
