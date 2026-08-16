"""Read-only operational monitoring over forward audit and continuity state."""
from dataclasses import asdict, dataclass
import argparse
import json
from pathlib import Path

import pandas as pd


@dataclass(frozen=True)
class OperationalAlert:
    code: str
    severity: str
    message: str


@dataclass(frozen=True)
class OperationalMonitoringReport:
    status: str
    session_state: str
    end_reason: str
    last_recorded_at: object
    audit_age_seconds: float
    checkpoint_age_seconds: float
    real_orders: int
    alerts: tuple


def _now(value=None):
    ts = pd.Timestamp.now(tz="UTC") if value is None else pd.Timestamp(value)
    if pd.isna(ts):
        raise ValueError("Monitoring now timestamp must be valid.")
    if ts.tzinfo is None:
        ts = ts.tz_localize("UTC")
    return ts.tz_convert("UTC")


def _age_seconds(now, value):
    if value is None:
        return 0.0
    ts = pd.Timestamp(value)
    if ts.tzinfo is None:
        ts = ts.tz_localize("UTC")
    return max(0.0, (now - ts.tz_convert("UTC")).total_seconds())


def _record_timestamp(row):
    candidates = [
        row.get("recorded_at"), row.get("at"), row.get("timestamp"),
        row.get("executed_at"), row.get("detected_at"),
        row.get("snapshot", {}).get("timestamp")
        if isinstance(row.get("snapshot"), dict) else None,
    ]
    for value in candidates:
        if value is None:
            continue
        try:
            return _now(value)
        except Exception:
            continue
    return None


def _provider_sequence_diagnostics(row):
    failure_kind = str(row.get("failure_kind") or "")
    if not failure_kind.startswith("PROVIDER_SEQUENCE_"):
        return ""
    return (
        " "
        f"(failure_kind={failure_kind} "
        f"provider_channel={row.get('provider_channel', 'unknown')} "
        f"previous_sequence_num={row.get('previous_sequence_num', 'unknown')} "
        f"expected_sequence_num={row.get('expected_sequence_num', 'unknown')} "
        f"observed_sequence_num={row.get('observed_sequence_num', 'unknown')} "
        f"message_timestamp={row.get('message_timestamp', 'unknown')})"
    )


def _read_audit(path, alerts):
    path = Path(path)
    if not path.exists() or not path.is_file():
        alerts.append(OperationalAlert(
            "AUDIT_MISSING", "CRITICAL", "Forward audit file is missing."
        ))
        return []
    rows = []
    try:
        for number, line in enumerate(
            path.read_text(encoding="utf-8").splitlines(), start=1
        ):
            if not line.strip():
                continue
            row = json.loads(line)
            if not isinstance(row, dict) or "type" not in row:
                raise ValueError(f"invalid record at line {number}")
            rows.append(row)
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        alerts.append(OperationalAlert(
            "AUDIT_UNREADABLE", "CRITICAL",
            f"Forward audit cannot be read safely: {exc}",
        ))
        return []
    if not rows:
        alerts.append(OperationalAlert(
            "AUDIT_EMPTY", "CRITICAL", "Forward audit has no records."
        ))
    return rows


def _read_state(path, alerts):
    path = Path(path)
    if not path.exists() or not path.is_file():
        alerts.append(OperationalAlert(
            "CHECKPOINT_MISSING", "CRITICAL", "Forward continuity state is missing."
        ))
        return None, None
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(payload, dict) or payload.get("version") != 1:
            raise ValueError("unsupported or missing state version")
        runtime = payload.get("runtime")
        if not isinstance(runtime, dict) or not isinstance(runtime.get("risk"), dict):
            raise ValueError("runtime risk state is missing or invalid")
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        alerts.append(OperationalAlert(
            "CHECKPOINT_UNREADABLE", "CRITICAL",
            f"Forward continuity state cannot be read safely: {exc}",
        ))
        return None, None
    saved_at = payload.get("saved_at")
    if saved_at is None:
        saved_at = pd.Timestamp(path.stat().st_mtime, unit="s", tz="UTC")
    return payload, saved_at


def build_operational_monitoring_report(
    audit_path="runtime/forward_paper_audit.jsonl",
    state_path="runtime/forward_paper_state.json",
    *,
    now=None,
    stale_after="5min",
):
    now = _now(now)
    stale_limit = pd.Timedelta(stale_after)
    if stale_limit <= pd.Timedelta(0):
        raise ValueError("stale_after must be positive.")

    alerts = []
    rows = _read_audit(audit_path, alerts)
    state, saved_at = _read_state(state_path, alerts)

    starts = [index for index, row in enumerate(rows) if row.get("type") == "SESSION_START"]
    if rows and not starts:
        alerts.append(OperationalAlert(
            "SESSION_START_MISSING", "CRITICAL",
            "Forward audit has no session boundary.",
        ))
        session = rows
        previous_session = []
    else:
        session = rows[starts[-1]:] if starts else []
        previous_session = (
            rows[starts[-2]:starts[-1]] if len(starts) >= 2 else []
        )

    ends = [row for row in session if row.get("type") == "SESSION_END"]
    end = ends[-1] if ends else None
    process_incidents = [
        row for row in session if row.get("type") == "PROCESS_INCIDENT"
    ]
    previous_process_incidents = [
        row for row in previous_session if row.get("type") == "PROCESS_INCIDENT"
    ]
    explicit_end_reason = str(end.get("reason", "UNKNOWN")) if end else None
    fatal_reasons = {
        "BACKFILL_FATAL", "TRANSPORT_FATAL", "RUNTIME_HALTED", "ORDERING_FATAL"
    }
    if process_incidents:
        session_state = "FAILED"
        end_reason = (
            explicit_end_reason
            if explicit_end_reason in fatal_reasons
            else "PROCESS_FAILURE"
        )
    elif explicit_end_reason == "OPERATOR_STOP":
        session_state = "STOPPED"
        end_reason = explicit_end_reason
    elif explicit_end_reason in fatal_reasons:
        session_state = "FAILED"
        end_reason = explicit_end_reason
    else:
        session_state = "COMPLETED" if end else (
            "RUNNING" if session else "UNKNOWN"
        )
        end_reason = explicit_end_reason if end else "RUNNING"

    last_recorded_at = _record_timestamp(session[-1]) if session else None
    audit_file = Path(audit_path)
    if last_recorded_at is None and audit_file.exists() and audit_file.is_file():
        last_recorded_at = pd.Timestamp(
            audit_file.stat().st_mtime, unit="s", tz="UTC"
        )
    audit_age_seconds = _age_seconds(now, last_recorded_at)
    checkpoint_age_seconds = _age_seconds(now, saved_at)

    if session_state == "RUNNING" and (
        last_recorded_at is None or audit_age_seconds > stale_limit.total_seconds()
    ):
        alerts.append(OperationalAlert(
            "AUDIT_STALE", "CRITICAL",
            "Running session audit activity exceeded the stale threshold.",
        ))
    if session_state == "RUNNING" and (
        saved_at is None or checkpoint_age_seconds > stale_limit.total_seconds()
    ):
        alerts.append(OperationalAlert(
            "CHECKPOINT_STALE", "CRITICAL",
            "Running session continuity checkpoint exceeded the stale threshold.",
        ))

    if process_incidents:
        incident = process_incidents[-1]
        alerts.append(OperationalAlert(
            "PROCESS_FAILURE", "CRITICAL",
            "Current supervised process failed unexpectedly "
            f"(service_result={incident.get('service_result', 'unknown')} "
            f"exit_code={incident.get('exit_code', 'unknown')} "
            f"exit_status={incident.get('exit_status', 'unknown')}).",
        ))
    if previous_process_incidents:
        incident = previous_process_incidents[-1]
        alerts.append(OperationalAlert(
            "PREVIOUS_PROCESS_FAILURE", "WARNING",
            "The immediately previous supervised process failed before this "
            "restart "
            f"(service_result={incident.get('service_result', 'unknown')} "
            f"exit_code={incident.get('exit_code', 'unknown')} "
            f"exit_status={incident.get('exit_status', 'unknown')}).",
        ))

    if explicit_end_reason in fatal_reasons:
        message = f"Session ended with {explicit_end_reason}."
        if explicit_end_reason == "ORDERING_FATAL":
            ordering_records = [
                row
                for row in session
                if row.get("type") == "LATE_TRADE_REJECTED"
            ]
            if ordering_records:
                ordering = ordering_records[-1]
                message = (
                    "Session ended with ORDERING_FATAL "
                    f"(trade_timestamp={ordering.get('trade_timestamp', 'unknown')} "
                    f"trade_id={ordering.get('trade_id', 'unknown')} "
                    f"message_sequence_num={ordering.get('message_sequence_num', 'unknown')} "
                    f"message_timestamp={ordering.get('message_timestamp', 'unknown')} "
                    f"event_type={ordering.get('event_type', 'unknown')} "
                    f"active_bucket={ordering.get('active_bucket', 'unknown')} "
                    f"watermark_timestamp={ordering.get('watermark_timestamp', 'unknown')} "
                    f"reorder_window_seconds={ordering.get('reorder_window_seconds', 'unknown')} "
                    f"lateness_seconds={ordering.get('lateness_seconds', 'unknown')})."
                )
        alerts.append(OperationalAlert(
            explicit_end_reason,
            "CRITICAL",
            message,
        ))
    if explicit_end_reason == "OPERATOR_STOP":
        alerts.append(OperationalAlert(
            "OPERATOR_STOP", "WARNING", "Session was stopped by the operator."
        ))

    if any(row.get("type") == "REST_BACKFILL_FAILED" for row in session):
        alerts.append(OperationalAlert(
            "BACKFILL_FAILED", "CRITICAL",
            "REST recovery failure is present in the latest session.",
        ))

    real_order_values = []
    for row in session:
        try:
            value = int(row.get("real_orders", 0))
            if value < 0:
                raise ValueError
            real_order_values.append(value)
        except (TypeError, ValueError):
            alerts.append(OperationalAlert(
                "REAL_ORDER_EVIDENCE_INVALID", "CRITICAL",
                "Real-order evidence is invalid or unreadable.",
            ))
    real_orders = max(real_order_values, default=0)
    if real_orders > 0:
        alerts.append(OperationalAlert(
            "REAL_ORDER_DETECTED", "CRITICAL",
            "Real-order evidence is non-zero in paper operation.",
        ))

    transport_events = [row for row in session if row.get("type") == "TRANSPORT_EVENT"]
    if transport_events:
        latest_transport_record = transport_events[-1]
        latest_transport = str(latest_transport_record.get("event", "UNKNOWN"))
        sequence_diagnostics = _provider_sequence_diagnostics(
            latest_transport_record
        )
        if latest_transport == "RECONNECT_EXHAUSTED":
            alerts.append(OperationalAlert(
                "TRANSPORT_RECONNECT_EXHAUSTED", "CRITICAL",
                "Transport reconnect budget is exhausted."
                f"{sequence_diagnostics}",
            ))
        elif latest_transport == "DISCONNECTED" and session_state == "RUNNING":
            alerts.append(OperationalAlert(
                "TRANSPORT_DISCONNECTED", "WARNING",
                "Latest transport state is disconnected."
                f"{sequence_diagnostics}",
            ))

    if state is not None:
        risk = state.get("runtime", {}).get("risk", {})
        if bool(risk.get("kill_switch_active", False)):
            alerts.append(OperationalAlert(
                "RISK_KILL_SWITCH", "CRITICAL",
                str(risk.get("kill_switch_reason") or "Risk kill switch is active."),
            ))
        if state.get("pending_reconciliation"):
            alerts.append(OperationalAlert(
                "PENDING_RECONCILIATION", "WARNING",
                "A post-recovery position reconciliation is pending.",
            ))

    severities = {alert.severity for alert in alerts}
    status = "CRITICAL" if "CRITICAL" in severities else (
        "WARNING" if "WARNING" in severities else "OK"
    )
    return OperationalMonitoringReport(
        status=status,
        session_state=session_state,
        end_reason=end_reason,
        last_recorded_at=last_recorded_at,
        audit_age_seconds=audit_age_seconds,
        checkpoint_age_seconds=checkpoint_age_seconds,
        real_orders=real_orders,
        alerts=tuple(alerts),
    )


def format_operational_monitoring_report(report):
    lines = [
        f"Operational Monitoring | status={report.status} | session={report.session_state} | end_reason={report.end_reason}",
        f"freshness: audit_age={report.audit_age_seconds:.1f}s checkpoint_age={report.checkpoint_age_seconds:.1f}s",
        f"safety: REAL_orders={report.real_orders} alerts={len(report.alerts)}",
    ]
    lines.extend(
        f"{alert.severity} {alert.code}: {alert.message}"
        for alert in report.alerts
    )
    return "\n".join(lines)


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="Read-only operational monitoring for forward paper trading."
    )
    parser.add_argument("--audit", default="runtime/forward_paper_audit.jsonl")
    parser.add_argument("--state", default="runtime/forward_paper_state.json")
    parser.add_argument("--stale-after", default="5min")
    parser.add_argument("--now", default=None)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)
    report = build_operational_monitoring_report(
        args.audit, args.state, now=args.now, stale_after=args.stale_after
    )
    if args.json:
        payload = asdict(report)
        print(json.dumps(payload, default=str, sort_keys=True))
    else:
        print(format_operational_monitoring_report(report))
    return {"OK": 0, "WARNING": 1, "CRITICAL": 2}[report.status]


if __name__ == "__main__":
    raise SystemExit(main())
