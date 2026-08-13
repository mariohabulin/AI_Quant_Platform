import json

import pandas as pd

from src.process_incident import main, record_process_incident


RECORDED_AT = pd.Timestamp("2026-08-12T17:34:28Z")


def read_rows(path):
    return [
        json.loads(line)
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


def test_successful_service_result_does_not_create_an_incident(tmp_path):
    audit = tmp_path / "audit.jsonl"

    recorded = record_process_incident(
        audit,
        service_result="success",
        exit_code="exited",
        exit_status="0",
        clock=lambda: RECORDED_AT,
    )

    assert recorded is False
    assert not audit.exists()


def test_failed_service_result_appends_durable_process_incident(tmp_path):
    audit = tmp_path / "audit.jsonl"
    audit.write_text('{"type":"SESSION_START"}\n', encoding="utf-8")

    recorded = record_process_incident(
        audit,
        service_result="exit-code",
        exit_code="exited",
        exit_status="1",
        clock=lambda: RECORDED_AT,
    )

    assert recorded is True
    assert read_rows(audit)[-1] == {
        "type": "PROCESS_INCIDENT",
        "reason": "UNEXPECTED_PROCESS_FAILURE",
        "service_result": "exit-code",
        "exit_code": "exited",
        "exit_status": "1",
        "recorded_at": "2026-08-12T17:34:28+00:00",
        "real_orders": 0,
    }


def test_missing_systemd_result_fails_visible_instead_of_assuming_success(tmp_path):
    audit = tmp_path / "audit.jsonl"

    recorded = record_process_incident(
        audit,
        service_result=None,
        exit_code=None,
        exit_status=None,
        clock=lambda: RECORDED_AT,
    )

    assert recorded is True
    row = read_rows(audit)[0]
    assert row["service_result"] == "unknown"
    assert row["exit_code"] == "unknown"
    assert row["exit_status"] == "unknown"


def test_cli_consumes_systemd_post_stop_environment(tmp_path, monkeypatch, capsys):
    audit = tmp_path / "audit.jsonl"
    monkeypatch.setenv("SERVICE_RESULT", "signal")
    monkeypatch.setenv("EXIT_CODE", "killed")
    monkeypatch.setenv("EXIT_STATUS", "KILL")

    assert main(["--audit", str(audit)]) == 0

    row = read_rows(audit)[0]
    assert row["service_result"] == "signal"
    assert row["exit_code"] == "killed"
    assert row["exit_status"] == "KILL"
    assert "PROCESS_INCIDENT recorded" in capsys.readouterr().out
