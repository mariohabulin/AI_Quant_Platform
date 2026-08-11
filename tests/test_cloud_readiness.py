import json

import pytest

from src.cloud_readiness import (
    CloudRuntimeConfig,
    CloudRuntimeReadinessGate,
    format_cloud_readiness_report,
    main,
)


def valid_config(tmp_path, **overrides):
    runtime_dir = tmp_path / "runtime"
    values = {
        "mode": "PAPER",
        "runtime_dir": runtime_dir,
        "audit_path": runtime_dir / "forward_paper_audit.jsonl",
        "state_path": runtime_dir / "forward_paper_state.json",
        "session_bars": 5,
        "monitor_interval_seconds": 60.0,
        "stale_after_seconds": 300.0,
        "real_execution_enabled": False,
    }
    values.update(overrides)
    return CloudRuntimeConfig(**values)


def test_valid_provider_neutral_cloud_configuration_passes(tmp_path):
    report = CloudRuntimeReadinessGate(valid_config(tmp_path)).run()
    assert report.status == "PASS"
    assert all(check.status == "PASS" for check in report.checks)
    assert not list((tmp_path / "runtime").glob("*.probe"))


@pytest.mark.parametrize(
    "overrides,failed_check",
    [
        ({"mode": "LIVE"}, "execution_lock"),
        ({"real_execution_enabled": True}, "execution_lock"),
        ({"session_bars": 0}, "bounded_session"),
        ({"monitor_interval_seconds": 300.0}, "monitoring_cadence"),
        ({"stale_after_seconds": 0.0}, "monitoring_cadence"),
    ],
)
def test_unsafe_cloud_configuration_fails_closed(tmp_path, overrides, failed_check):
    report = CloudRuntimeReadinessGate(valid_config(tmp_path, **overrides)).run()
    assert report.status == "FAIL"
    assert next(check for check in report.checks if check.name == failed_check).status == "FAIL"


def test_runtime_directory_must_be_absolute(tmp_path):
    config = valid_config(
        tmp_path,
        runtime_dir="runtime",
        audit_path="runtime/audit.jsonl",
        state_path="runtime/state.json",
    )
    report = CloudRuntimeReadinessGate(config).run()
    assert next(check for check in report.checks if check.name == "persistent_paths").status == "FAIL"


def test_invalid_paths_do_not_run_storage_probe(tmp_path):
    calls = []
    config = valid_config(
        tmp_path,
        runtime_dir="runtime",
        audit_path="runtime/audit.jsonl",
        state_path="runtime/state.json",
    )
    report = CloudRuntimeReadinessGate(
        config, storage_probe=lambda path: calls.append(path) or True
    ).run()
    assert report.status == "FAIL"
    assert calls == []
    assert next(
        check for check in report.checks if check.name == "persistent_storage"
    ).status == "FAIL"


def test_audit_and_state_must_share_persistent_runtime_directory(tmp_path):
    config = valid_config(tmp_path, audit_path=tmp_path / "outside.jsonl")
    report = CloudRuntimeReadinessGate(config).run()
    assert next(check for check in report.checks if check.name == "persistent_paths").status == "FAIL"


def test_failed_storage_probe_blocks_readiness(tmp_path):
    gate = CloudRuntimeReadinessGate(
        valid_config(tmp_path), storage_probe=lambda _: False
    )
    report = gate.run()
    assert next(check for check in report.checks if check.name == "persistent_storage").status == "FAIL"


def test_missing_environment_configuration_fails_instead_of_using_live_defaults(monkeypatch):
    for name in (
        "AI_ALPHA_MODE", "AI_ALPHA_RUNTIME_DIR", "AI_ALPHA_SESSION_BARS",
        "AI_ALPHA_MONITOR_INTERVAL_SECONDS", "AI_ALPHA_STALE_AFTER_SECONDS",
        "AI_ALPHA_REAL_EXECUTION_ENABLED",
    ):
        monkeypatch.delenv(name, raising=False)
    report = CloudRuntimeReadinessGate(CloudRuntimeConfig.from_env()).run()
    assert report.status == "FAIL"


def test_report_is_operator_readable_and_json_serializable(tmp_path):
    report = CloudRuntimeReadinessGate(valid_config(tmp_path)).run()
    text = format_cloud_readiness_report(report)
    assert "Cloud Runtime Readiness | status=PASS" in text
    json.dumps(report.to_dict())


def test_cli_returns_zero_for_pass_and_two_for_fail(tmp_path, monkeypatch, capsys):
    runtime_dir = tmp_path / "runtime"
    monkeypatch.setenv("AI_ALPHA_MODE", "PAPER")
    monkeypatch.setenv("AI_ALPHA_RUNTIME_DIR", str(runtime_dir))
    monkeypatch.setenv("AI_ALPHA_SESSION_BARS", "5")
    monkeypatch.setenv("AI_ALPHA_MONITOR_INTERVAL_SECONDS", "60")
    monkeypatch.setenv("AI_ALPHA_STALE_AFTER_SECONDS", "300")
    monkeypatch.setenv("AI_ALPHA_REAL_EXECUTION_ENABLED", "false")
    assert main([]) == 0
    assert "status=PASS" in capsys.readouterr().out
    monkeypatch.setenv("AI_ALPHA_MODE", "LIVE")
    assert main([]) == 2
