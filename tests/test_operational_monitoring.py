import json
import os
import pandas as pd
import pytest

from src.operational_monitoring import (
    build_operational_monitoring_report,
    format_operational_monitoring_report,
    main,
)


NOW = pd.Timestamp("2026-08-11T10:00:00Z")


def write_audit(path, rows):
    path.write_text(
        "\n".join(json.dumps(row) for row in rows) + "\n", encoding="utf-8"
    )


def paper_event(recorded_at="2026-08-11T09:59:00+00:00", real_orders=0):
    return {
        "type": "PAPER_EVENT",
        "recorded_at": recorded_at,
        "real_orders": real_orders,
        "snapshot": {
            "timestamp": "2026-08-11T09:59:00+00:00",
            "equity": 5000.0,
            "position_quantity": 0.0,
        },
        "event": {"signal": 0, "status": "NO_ACTION", "risk_status": "ALLOW"},
    }


def session_rows(end_reason="MAX_BARS", real_orders=0):
    return [
        {
            "type": "SESSION_START",
            "recorded_at": "2026-08-11T09:58:00+00:00",
            "real_orders": 0,
        },
        paper_event(real_orders=real_orders),
        {
            "type": "SESSION_END",
            "recorded_at": "2026-08-11T10:00:00+00:00",
            "reason": end_reason,
            "real_orders": real_orders,
        },
    ]


def process_incident(
    recorded_at="2026-08-11T09:59:30+00:00",
    service_result="exit-code",
    exit_code="exited",
    exit_status="1",
):
    return {
        "type": "PROCESS_INCIDENT",
        "recorded_at": recorded_at,
        "reason": "UNEXPECTED_PROCESS_FAILURE",
        "service_result": service_result,
        "exit_code": exit_code,
        "exit_status": exit_status,
        "real_orders": 0,
    }


def write_state(path, *, kill_switch=False, pending=None):
    payload = {
        "version": 1,
        "saved_at": "2026-08-11T09:59:00+00:00",
        "runtime": {
            "version": 1,
            "risk": {
                "kill_switch_active": kill_switch,
                "kill_switch_reason": (
                    "Maximum drawdown limit reached." if kill_switch else None
                ),
            },
        },
        "pending_reconciliation": pending,
    }
    path.write_text(json.dumps(payload), encoding="utf-8")


def monitor(tmp_path, rows, **kwargs):
    audit = tmp_path / "audit.jsonl"
    state = tmp_path / "state.json"
    write_audit(audit, rows)
    write_state(state)
    return build_operational_monitoring_report(
        audit, state, now=NOW, stale_after="5min", **kwargs
    )


def test_completed_safe_session_is_ok(tmp_path):
    report = monitor(tmp_path, session_rows())
    assert report.status == "OK"
    assert report.session_state == "COMPLETED"
    assert report.alerts == ()
    assert report.real_orders == 0


def test_fresh_incomplete_session_is_running_not_critical(tmp_path):
    report = monitor(tmp_path, session_rows()[:-1])
    assert report.status == "OK"
    assert report.session_state == "RUNNING"


def test_current_process_incident_is_critical_and_not_mislabeled_running(tmp_path):
    rows = session_rows()[:-1] + [process_incident()]

    report = monitor(tmp_path, rows)

    assert report.status == "CRITICAL"
    assert report.session_state == "FAILED"
    assert report.end_reason == "PROCESS_FAILURE"
    assert "PROCESS_FAILURE" in {alert.code for alert in report.alerts}


def test_healthy_restart_retains_previous_process_failure_as_warning(tmp_path):
    failed_attempt = [
        {
            "type": "SESSION_START",
            "recorded_at": "2026-08-11T09:50:00+00:00",
            "real_orders": 0,
        },
        paper_event(recorded_at="2026-08-11T09:51:00+00:00"),
        process_incident(recorded_at="2026-08-11T09:52:00+00:00"),
    ]

    report = monitor(tmp_path, failed_attempt + session_rows())

    assert report.status == "WARNING"
    assert report.session_state == "COMPLETED"
    assert report.end_reason == "MAX_BARS"
    assert "PREVIOUS_PROCESS_FAILURE" in {
        alert.code for alert in report.alerts
    }


def test_later_session_clears_incident_after_one_completed_recovery_session(tmp_path):
    failed_attempt = [
        {
            "type": "SESSION_START",
            "recorded_at": "2026-08-11T09:40:00+00:00",
            "real_orders": 0,
        },
        process_incident(recorded_at="2026-08-11T09:42:00+00:00"),
    ]
    recovered_attempt = [
        {
            "type": "SESSION_START",
            "recorded_at": "2026-08-11T09:45:00+00:00",
            "real_orders": 0,
        },
        {
            "type": "SESSION_END",
            "recorded_at": "2026-08-11T09:50:00+00:00",
            "reason": "MAX_BARS",
            "real_orders": 0,
        },
    ]

    report = monitor(tmp_path, failed_attempt + recovered_attempt + session_rows())

    assert report.status == "OK"
    assert "PREVIOUS_PROCESS_FAILURE" not in {
        alert.code for alert in report.alerts
    }


def test_stale_running_audit_is_critical(tmp_path):
    rows = session_rows()[:-1]
    rows[-1]["recorded_at"] = "2026-08-11T09:50:00+00:00"
    report = monitor(tmp_path, rows)
    assert report.status == "CRITICAL"
    assert "AUDIT_STALE" in {alert.code for alert in report.alerts}


@pytest.mark.parametrize(
    "reason,code",
    [
        ("BACKFILL_FATAL", "BACKFILL_FATAL"),
        ("TRANSPORT_FATAL", "TRANSPORT_FATAL"),
        ("RUNTIME_HALTED", "RUNTIME_HALTED"),
    ],
)
def test_fatal_session_end_is_critical(tmp_path, reason, code):
    report = monitor(tmp_path, session_rows(end_reason=reason))
    assert report.status == "CRITICAL"
    assert code in {alert.code for alert in report.alerts}


def test_real_order_evidence_is_critical(tmp_path):
    report = monitor(tmp_path, session_rows(real_orders=1))
    assert report.status == "CRITICAL"
    assert report.real_orders == 1
    assert "REAL_ORDER_DETECTED" in {alert.code for alert in report.alerts}


def test_backfill_failure_record_is_critical(tmp_path):
    rows = session_rows()
    rows.insert(2, {
        "type": "REST_BACKFILL_FAILED",
        "recorded_at": "2026-08-11T09:59:30+00:00",
        "reason": "incomplete candles",
        "real_orders": 0,
    })
    report = monitor(tmp_path, rows)
    assert report.status == "CRITICAL"
    assert "BACKFILL_FAILED" in {alert.code for alert in report.alerts}


def test_current_transport_disconnect_is_warning(tmp_path):
    rows = session_rows()[:-1]
    rows.append({
        "type": "TRANSPORT_EVENT",
        "event": "DISCONNECTED",
        "recorded_at": "2026-08-11T09:59:30+00:00",
        "real_orders": 0,
    })
    report = monitor(tmp_path, rows)
    assert report.status == "WARNING"
    assert "TRANSPORT_DISCONNECTED" in {alert.code for alert in report.alerts}


def test_active_kill_switch_is_critical(tmp_path):
    audit = tmp_path / "audit.jsonl"
    state = tmp_path / "state.json"
    write_audit(audit, session_rows())
    write_state(state, kill_switch=True)
    report = build_operational_monitoring_report(audit, state, now=NOW)
    assert report.status == "CRITICAL"
    assert "RISK_KILL_SWITCH" in {alert.code for alert in report.alerts}


def test_pending_reconciliation_is_warning(tmp_path):
    audit = tmp_path / "audit.jsonl"
    state = tmp_path / "state.json"
    write_audit(audit, session_rows())
    write_state(state, pending={"kind": "LONG_EXIT"})
    report = build_operational_monitoring_report(audit, state, now=NOW)
    assert report.status == "WARNING"
    assert "PENDING_RECONCILIATION" in {alert.code for alert in report.alerts}


@pytest.mark.parametrize("missing", ["audit", "state"])
def test_missing_required_operational_file_is_critical(tmp_path, missing):
    audit = tmp_path / "audit.jsonl"
    state = tmp_path / "state.json"
    if missing != "audit":
        write_audit(audit, session_rows())
    if missing != "state":
        write_state(state)
    report = build_operational_monitoring_report(audit, state, now=NOW)
    assert report.status == "CRITICAL"


@pytest.mark.parametrize("corrupt", ["audit", "state"])
def test_corrupt_required_operational_file_is_critical(tmp_path, corrupt):
    audit = tmp_path / "audit.jsonl"
    state = tmp_path / "state.json"
    write_audit(audit, session_rows())
    write_state(state)
    target = audit if corrupt == "audit" else state
    target.write_text("{broken", encoding="utf-8")
    report = build_operational_monitoring_report(audit, state, now=NOW)
    assert report.status == "CRITICAL"


def test_invalid_real_order_evidence_fails_closed(tmp_path):
    rows = session_rows()
    rows[1]["real_orders"] = "unknown"
    report = monitor(tmp_path, rows)
    assert report.status == "CRITICAL"
    assert "REAL_ORDER_EVIDENCE_INVALID" in {alert.code for alert in report.alerts}


def test_stale_checkpoint_during_running_session_is_critical(tmp_path):
    audit = tmp_path / "audit.jsonl"
    state = tmp_path / "state.json"
    write_audit(audit, session_rows()[:-1])
    write_state(state)
    payload = json.loads(state.read_text(encoding="utf-8"))
    payload["saved_at"] = "2026-08-11T09:50:00+00:00"
    state.write_text(json.dumps(payload), encoding="utf-8")
    report = build_operational_monitoring_report(
        audit, state, now=NOW, stale_after="5min"
    )
    assert report.status == "CRITICAL"
    assert "CHECKPOINT_STALE" in {alert.code for alert in report.alerts}


def test_legacy_completed_audit_without_recorded_at_uses_file_mtime(tmp_path):
    audit = tmp_path / "audit.jsonl"
    state = tmp_path / "state.json"
    rows = session_rows()
    for row in rows:
        row.pop("recorded_at", None)
    write_audit(audit, rows)
    legacy_time = pd.Timestamp("2026-08-11T09:50:00Z").timestamp()
    os.utime(audit, (legacy_time, legacy_time))
    write_state(state)

    report = build_operational_monitoring_report(audit, state, now=NOW)

    assert report.status == "OK"
    assert report.audit_age_seconds == pytest.approx(600.0)


def test_format_and_cli_expose_operator_status_and_exit_code(tmp_path, capsys):
    audit = tmp_path / "audit.jsonl"
    state = tmp_path / "state.json"
    write_audit(audit, session_rows(end_reason="TRANSPORT_FATAL"))
    write_state(state)
    report = build_operational_monitoring_report(audit, state, now=NOW)
    text = format_operational_monitoring_report(report)
    assert "status=CRITICAL" in text
    assert "TRANSPORT_FATAL" in text
    assert main([
        "--audit", str(audit), "--state", str(state),
        "--now", NOW.isoformat(),
    ]) == 2
    assert "status=CRITICAL" in capsys.readouterr().out
