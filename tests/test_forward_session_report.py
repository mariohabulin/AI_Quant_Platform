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
