import json

import pytest

from src.forward_session_report import build_forward_session_report, format_forward_session_report, main


def write_rows(path, rows):
    path.write_text("\n".join(json.dumps(row) for row in rows) + "\n", encoding="utf-8")


def session_rows(final_equity=4990.0, real_orders=0):
    return [
        {"type": "SESSION_START", "at": "2026-08-09T06:39:00+00:00", "resumed": True},
        {"type": "RESTART_REBASE", "timestamp": "2026-08-09T06:39:00+00:00", "real_orders": 0},
        {"type": "PAPER_EVENT", "paper_orders": 0, "real_orders": 0,
         "snapshot": {"equity": 5000.0, "position_quantity": 0.02},
         "event": {"signal": 0, "status": "NO_ACTION", "risk_status": "ALLOW"}},
        {"type": "REJECTED_BAR", "reason": "test", "real_orders": 0},
        {"type": "PAPER_EVENT", "paper_orders": 1, "real_orders": real_orders,
         "snapshot": {"equity": final_equity, "position_quantity": 0.0},
         "event": {"signal": -1, "status": "FILLED", "risk_status": "ALLOW"}},
        {"type": "SESSION_END", "reason": "MAX_BARS", "processed_events": 2, "rejected_events": 1,
         "paper_orders": 1, "equity": final_equity, "position": 0.0, "real_orders": real_orders},
    ]


def test_report_summarizes_latest_complete_session(tmp_path):
    audit = tmp_path / "audit.jsonl"
    write_rows(audit, session_rows())
    report = build_forward_session_report(audit)
    assert report.status == "PASS"
    assert report.processed_events == 2
    assert report.rejected_events == 1
    assert report.rebase_events == 1
    assert report.sell_signals == 1
    assert report.hold_signals == 1
    assert report.filled_orders == 1
    assert report.paper_orders == 1
    assert report.net_pnl == pytest.approx(-10.0)
    assert report.max_drawdown == pytest.approx(0.002)
    assert report.real_orders == 0


def test_report_uses_only_latest_session(tmp_path):
    audit = tmp_path / "audit.jsonl"
    rows = session_rows(final_equity=4900.0) + session_rows(final_equity=4995.0)
    write_rows(audit, rows)
    report = build_forward_session_report(audit)
    assert report.final_equity == pytest.approx(4995.0)
    assert report.processed_events == 2


def test_report_fails_closed_when_latest_session_has_no_end(tmp_path):
    audit = tmp_path / "audit.jsonl"
    write_rows(audit, session_rows() + [{"type": "SESSION_START", "at": "later"}])
    with pytest.raises(RuntimeError, match="incomplete"):
        build_forward_session_report(audit)


def test_report_marks_real_order_evidence_as_failure(tmp_path):
    audit = tmp_path / "audit.jsonl"
    write_rows(audit, session_rows(real_orders=1))
    report = build_forward_session_report(audit)
    assert report.status == "FAIL"
    assert report.audit_complete is False
    assert report.real_orders == 1


def test_report_format_is_operator_readable(tmp_path):
    audit = tmp_path / "audit.jsonl"
    write_rows(audit, session_rows())
    text = format_forward_session_report(build_forward_session_report(audit))
    assert "status=PASS" in text
    assert "REAL=0" in text
    assert "net_pnl=-10.00" in text


def test_cli_json_output(tmp_path, capsys):
    audit = tmp_path / "audit.jsonl"
    write_rows(audit, session_rows())
    assert main(["--audit", str(audit), "--json"]) == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["status"] == "PASS"
    assert payload["paper_orders"] == 1


def test_report_counts_reconnect_rebase_as_rebase_event(tmp_path):
    audit = tmp_path / "audit.jsonl"
    rows = session_rows()
    rows.insert(2, {"type": "RECONNECT_REBASE", "timestamp": "2026-08-09T06:40:00+00:00", "real_orders": 0})
    write_rows(audit, rows)
    report = build_forward_session_report(audit)
    assert report.status == "PASS"
    assert report.rebase_events == 2


def test_report_adds_operational_transport_and_activity_diagnostics(tmp_path):
    audit = tmp_path / "diagnostics.jsonl"
    rows = [
        {"type": "SESSION_START", "at": "2026-08-09T10:47:00+00:00", "resumed": True},
        {"type": "PAPER_EVENT", "paper_orders": 0, "real_orders": 0,
         "snapshot": {"timestamp": "2026-08-09T10:47:00+00:00", "equity": 5000.0, "position_quantity": 0.0},
         "event": {"signal": 0, "status": "NO_ACTION", "risk_status": "ALLOW", "reason": "Strategy emitted HOLD."}},
        {"type": "TRANSPORT_EVENT", "event": "DISCONNECTED", "reason": "reset", "real_orders": 0},
        {"type": "TRANSPORT_EVENT", "event": "RECONNECTED", "reconnect_count": 1, "real_orders": 0},
        {"type": "RECONNECT_REBASE", "timestamp": "2026-08-09T10:55:00+00:00", "real_orders": 0},
        {"type": "PROVIDER_REPLAY_DROPPED", "timestamp": "2026-08-09T10:47:00+00:00", "real_orders": 0},
        {"type": "PAPER_EVENT", "paper_orders": 0, "real_orders": 0,
         "snapshot": {"timestamp": "2026-08-09T10:56:00+00:00", "equity": 5000.0, "position_quantity": 0.0},
         "event": {"signal": 1, "status": "REJECTED", "risk_status": "REJECT", "reason": "Minimum reward/risk requirement not met."}},
        {"type": "SESSION_END", "reason": "MAX_BARS", "processed_events": 2, "rejected_events": 0,
         "paper_orders": 0, "equity": 5000.0, "position": 0.0, "real_orders": 0},
    ]
    write_rows(audit, rows)
    report = build_forward_session_report(audit)
    assert report.transport_disconnects == 1
    assert report.transport_reconnects == 1
    assert report.reconnect_success_rate == pytest.approx(1.0)
    assert report.provider_replay_drops == 1
    assert report.market_span_minutes == pytest.approx(9.0)
    assert report.expected_contiguous_minutes == pytest.approx(1.0)
    assert report.observed_gap_minutes == pytest.approx(8.0)
    assert report.signal_activity_rate == pytest.approx(0.5)
    assert report.risk_rejection_rate == pytest.approx(1.0)
    assert report.risk_rejection_reasons == {"Minimum reward/risk requirement not met.": 1}
    text = format_forward_session_report(report)
    assert "disconnects=1 reconnects=1 success=100.0%" in text
    assert "observed_gap=8.0m" in text
    assert "signal_rate=50.0%" in text


def test_report_summarizes_transport_outage_quality_and_failure_kinds(tmp_path):
    audit = tmp_path / "transport_quality.jsonl"
    rows = [
        {"type": "SESSION_START", "at": "2026-08-09T10:00:00+00:00"},
        {"type": "PAPER_EVENT", "paper_orders": 0, "real_orders": 0,
         "snapshot": {"timestamp": "2026-08-09T10:00:00+00:00", "equity": 5000.0, "position_quantity": 0.0},
         "event": {"signal": 0, "status": "NO_ACTION", "risk_status": "ALLOW", "reason": "HOLD"}},
        {"type": "TRANSPORT_EVENT", "event": "DISCONNECTED", "failure_kind": "RESET", "real_orders": 0},
        {"type": "TRANSPORT_EVENT", "event": "RECONNECTED", "outage_seconds": 7.5, "real_orders": 0},
        {"type": "TRANSPORT_EVENT", "event": "DISCONNECTED", "failure_kind": "DNS", "real_orders": 0},
        {"type": "TRANSPORT_EVENT", "event": "RECONNECTED", "outage_seconds": 12.5, "real_orders": 0},
        {"type": "PAPER_EVENT", "paper_orders": 0, "real_orders": 0,
         "snapshot": {"timestamp": "2026-08-09T10:21:00+00:00", "equity": 5000.0, "position_quantity": 0.0},
         "event": {"signal": 0, "status": "NO_ACTION", "risk_status": "ALLOW", "reason": "HOLD"}},
        {"type": "SESSION_END", "reason": "MAX_BARS", "processed_events": 2, "rejected_events": 0,
         "paper_orders": 0, "equity": 5000.0, "position": 0.0, "real_orders": 0},
    ]
    write_rows(audit, rows)
    report = build_forward_session_report(audit)

    assert report.total_outage_seconds == pytest.approx(20.0)
    assert report.max_outage_seconds == pytest.approx(12.5)
    assert report.disconnect_reason_counts == {"DNS": 1, "RESET": 1}
    text = format_forward_session_report(report)
    assert "outage_total=20.0s" in text
    assert "outage_max=12.5s" in text
    assert "'DNS': 1" in text


def test_report_includes_hybrid_rest_backfill_in_continuity_metrics(tmp_path):
    audit = tmp_path / "hybrid.jsonl"
    rows = [
        {"type": "SESSION_START", "at": "2026-08-09T12:00:00+00:00"},
        {"type": "PAPER_EVENT", "paper_orders": 0, "real_orders": 0,
         "snapshot": {"timestamp": "2026-08-09T12:00:00+00:00", "equity": 5000.0, "position_quantity": 0.0},
         "event": {"signal": 0, "status": "NO_ACTION", "risk_status": "ALLOW", "reason": "HOLD"}},
        {"type": "REST_BACKFILL_BAR", "timestamp": "2026-08-09T12:01:00+00:00", "real_orders": 0},
        {"type": "REST_BACKFILL_BAR", "timestamp": "2026-08-09T12:02:00+00:00", "real_orders": 0},
        {"type": "REST_BACKFILL_COMPLETE", "recovered_bars": 2, "real_orders": 0},
        {"type": "PAPER_EVENT", "paper_orders": 0, "real_orders": 0,
         "snapshot": {"timestamp": "2026-08-09T12:03:00+00:00", "equity": 5000.0, "position_quantity": 0.0},
         "event": {"signal": 0, "status": "NO_ACTION", "risk_status": "ALLOW", "reason": "HOLD"}},
        {"type": "SESSION_END", "reason": "MAX_BARS", "processed_events": 2, "rejected_events": 0,
         "paper_orders": 0, "equity": 5000.0, "position": 0.0, "real_orders": 0},
    ]
    write_rows(audit, rows)
    report = build_forward_session_report(audit)
    assert report.rest_backfill_bars == 2
    assert report.rest_backfill_failures == 0
    assert report.market_span_minutes == pytest.approx(3.0)
    assert report.expected_contiguous_minutes == pytest.approx(3.0)
    assert report.observed_gap_minutes == pytest.approx(0.0)
    assert "hybrid_recovery: backfill_bars=2 startup_catchup_bars=0 failures=0" in format_forward_session_report(report)


def test_report_explains_strategy_behavior_without_changing_policy(tmp_path):
    audit = tmp_path / "strategy_behavior.jsonl"
    rows = [
        {"type": "SESSION_START", "at": "2026-08-10T13:00:00+00:00"},
        {"type": "PAPER_EVENT", "paper_orders": 0, "real_orders": 0,
         "snapshot": {"timestamp": "2026-08-10T13:00:00+00:00", "equity": 5000.0, "position_quantity": 0.0},
         "event": {"signal": 0, "status": "NO_ACTION", "risk_status": "ALLOW", "reason": "Strategy emitted HOLD."},
         "strategy_diagnostics": {"strategy": "ema_crossover", "relation": "BELOW", "spread_bps": -2.0}},
        {"type": "PAPER_EVENT", "paper_orders": 1, "real_orders": 0,
         "snapshot": {"timestamp": "2026-08-10T13:01:00+00:00", "equity": 5001.0, "position_quantity": 0.01},
         "event": {"signal": 1, "status": "FILLED", "risk_status": "REDUCE", "reason": "Position reduced."},
         "strategy_diagnostics": {"strategy": "ema_crossover", "relation": "ABOVE", "spread_bps": 1.0}},
        {"type": "SESSION_END", "reason": "MAX_BARS", "processed_events": 2, "rejected_events": 0,
         "paper_orders": 1, "equity": 5001.0, "position": 0.01, "real_orders": 0},
    ]
    write_rows(audit, rows)
    report = build_forward_session_report(audit)
    assert report.strategy_name == "ema_crossover"
    assert report.strategy_relation_counts == {"ABOVE": 1, "BELOW": 1}
    assert report.strategy_spread_bps_min == pytest.approx(-2.0)
    assert report.strategy_spread_bps_avg == pytest.approx(-0.5)
    assert report.strategy_spread_bps_max == pytest.approx(1.0)
    assert report.event_reason_counts == {"Position reduced.": 1, "Strategy emitted HOLD.": 1}
    text = format_forward_session_report(report)
    assert "strategy_behavior: strategy=ema_crossover" in text
    assert "decision_reasons:" in text
