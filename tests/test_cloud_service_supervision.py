from pathlib import Path
import re


ROOT = Path(__file__).resolve().parents[1]
SYSTEMD = ROOT / "deploy" / "systemd"


def _unit(name):
    return (SYSTEMD / name).read_text(encoding="utf-8")


def _environment(name):
    values = {}
    for raw_line in _unit(name).splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        key, value = line.split("=", maxsplit=1)
        values[key] = value
    return values


def _values(text, directive):
    return re.findall(rf"^{re.escape(directive)}=(.*)$", text, flags=re.MULTILINE)


def test_supervision_package_contains_repeatable_deployment_artifacts():
    assert {
        "README.md",
        "ai-alpha-monitor.service",
        "ai-alpha-monitor.timer",
        "ai-alpha-paper.env",
        "ai-alpha-paper.service",
        "install.sh",
    } <= {path.name for path in SYSTEMD.iterdir()}


def test_paper_service_is_non_root_and_bound_to_the_deployed_revision():
    service = _unit("ai-alpha-paper.service")

    assert _values(service, "User") == ["ai-alpha"]
    assert _values(service, "Group") == ["ai-alpha"]
    assert _values(service, "WorkingDirectory") == ["/opt/ai-alpha"]
    assert _values(service, "ExecStart") == [
        "/opt/ai-alpha/.venv/bin/python -m src.forward_paper_session "
        "--bars ${AI_ALPHA_SESSION_BARS} "
        "--audit /var/lib/ai-alpha/forward_paper_audit.jsonl "
        "--state /var/lib/ai-alpha/forward_paper_state.json"
    ]


def test_paper_service_has_fail_closed_readiness_and_execution_lock():
    service = _unit("ai-alpha-paper.service")
    environment = set(_values(service, "Environment"))

    assert {
        "AI_ALPHA_MODE=PAPER",
        "AI_ALPHA_RUNTIME_DIR=/var/lib/ai-alpha",
        "AI_ALPHA_MONITOR_INTERVAL_SECONDS=60",
        "AI_ALPHA_STALE_AFTER_SECONDS=180",
        "AI_ALPHA_REAL_EXECUTION_ENABLED=false",
    } <= environment
    assert not any(value.startswith("AI_ALPHA_SESSION_BARS=") for value in environment)
    assert _values(service, "EnvironmentFile") == [
        "/etc/ai-alpha/ai-alpha-paper.env"
    ]
    assert _values(service, "ExecStartPre") == [
        "/opt/ai-alpha/.venv/bin/python -m src.cloud_readiness"
    ]


def test_paper_service_uses_reviewed_twelve_hour_overnight_soak_bound():
    environment = _environment("ai-alpha-paper.env")

    assert environment == {"AI_ALPHA_SESSION_BARS": "720"}
    assert 0 < int(environment["AI_ALPHA_SESSION_BARS"]) < 1440


def test_paper_service_uses_persistent_private_runtime_storage():
    service = _unit("ai-alpha-paper.service")

    assert _values(service, "StateDirectory") == ["ai-alpha"]
    assert _values(service, "StateDirectoryMode") == ["0700"]
    assert _values(service, "ReadWritePaths") == ["/var/lib/ai-alpha"]
    assert _values(service, "UMask") == ["0077"]


def test_paper_service_has_bounded_restart_policy_and_controlled_signal():
    service = _unit("ai-alpha-paper.service")

    assert _values(service, "Restart") == ["on-failure"]
    assert _values(service, "RestartSec") == ["10s"]
    assert _values(service, "StartLimitIntervalSec") == ["infinity"]
    assert _values(service, "StartLimitBurst") == ["2"]
    assert _values(service, "KillSignal") == ["SIGINT"]
    assert _values(service, "SuccessExitStatus") == ["130"]


def test_paper_service_persists_post_stop_failure_evidence_without_owning_policy():
    service = _unit("ai-alpha-paper.service")

    assert _values(service, "ExecStopPost") == [
        "-/opt/ai-alpha/.venv/bin/python -m src.process_incident "
        "--audit /var/lib/ai-alpha/forward_paper_audit.jsonl"
    ]


def test_paper_service_applies_minimum_process_hardening():
    service = _unit("ai-alpha-paper.service")

    for directive in (
        "LockPersonality",
        "NoNewPrivileges",
        "PrivateDevices",
        "PrivateTmp",
        "ProtectClock",
        "ProtectControlGroups",
        "ProtectHome",
        "ProtectHostname",
        "ProtectKernelLogs",
        "ProtectKernelModules",
        "ProtectKernelTunables",
        "RemoveIPC",
        "RestrictRealtime",
        "RestrictNamespaces",
        "RestrictSUIDSGID",
    ):
        assert _values(service, directive) == ["true"]
    assert _values(service, "CapabilityBoundingSet") == [""]
    assert _values(service, "AmbientCapabilities") == [""]
    assert _values(service, "ProtectSystem") == ["strict"]
    assert _values(service, "SystemCallArchitectures") == ["native"]
    assert _values(service, "RestrictAddressFamilies") == [
        "AF_UNIX AF_INET AF_INET6"
    ]


def test_monitor_service_consumes_existing_read_only_policy():
    service = _unit("ai-alpha-monitor.service")

    assert _values(service, "Type") == ["oneshot"]
    assert _values(service, "User") == ["ai-alpha"]
    assert _values(service, "Group") == ["ai-alpha"]
    assert _values(service, "ExecStart") == [
        "/opt/ai-alpha/.venv/bin/python -m src.operational_monitoring "
        "--audit /var/lib/ai-alpha/forward_paper_audit.jsonl "
        "--state /var/lib/ai-alpha/forward_paper_state.json "
        "--stale-after 3min"
    ]
    assert _values(service, "ReadWritePaths") == []
    assert _values(service, "SuccessExitStatus") == ["1"]


def test_monitor_timer_is_recurring_persistent_and_does_not_start_trading():
    timer = _unit("ai-alpha-monitor.timer")

    assert _values(timer, "OnBootSec") == ["2min"]
    assert _values(timer, "OnUnitActiveSec") == ["1min"]
    assert _values(timer, "Persistent") == ["true"]
    assert _values(timer, "Unit") == ["ai-alpha-monitor.service"]
    assert "ai-alpha-paper.service" not in timer


def test_installer_creates_passwordless_system_identity_and_exact_paths():
    installer = _unit("install.sh")

    assert "useradd --system" in installer
    assert "--shell /usr/sbin/nologin" in installer
    assert "/var/lib/ai-alpha" in installer
    assert "/etc/systemd/system" in installer
    assert "systemd-analyze verify" in installer
    assert "systemctl daemon-reload" in installer


def test_installer_deploys_root_controlled_session_configuration_before_verify():
    installer = _unit("install.sh")

    assert "config_target=/etc/ai-alpha" in installer
    assert 'install -d -o root -g root -m 0755 "${config_target}"' in installer
    config_install = (
        'install -o root -g root -m 0644 "${unit_source}/ai-alpha-paper.env" '
        '"${config_target}/ai-alpha-paper.env"'
    )
    assert config_install in installer
    assert installer.index(config_install) < installer.index("systemd-analyze verify")


def test_installer_never_starts_or_enables_a_trading_process():
    installer = _unit("install.sh")

    forbidden = (
        "systemctl start",
        "systemctl restart",
        "systemctl enable",
        "systemctl --now",
        "enable --now",
    )
    assert all(command not in installer for command in forbidden)


def test_runbook_opens_a_fresh_restart_budget_before_each_reviewed_activation():
    runbook = _unit("README.md")
    normalized = " ".join(runbook.split())
    reset = "systemctl reset-failed ai-alpha-paper.service"
    start = "systemctl start ai-alpha-paper.service"

    assert reset in runbook
    assert runbook.index(reset) < runbook.index(start)
    assert "Unit ai-alpha-paper.service not loaded" in normalized
    assert "no retained start-limit counter" in normalized
    assert "Installed PAPER unit is not loadable" in normalized
    assert "Any other `reset-failed` error aborts activation" in normalized
    assert "Do not replace this guard with `|| true`" in normalized


def test_runbook_requires_provider_message_sequence_integrity_evidence():
    runbook = _unit("README.md")

    assert "sequence_num" in runbook
    assert "PROVIDER_MESSAGE_REPLAY_DROPPED" in runbook
    assert "PROVIDER_SEQUENCE_GAP" in runbook
    assert "message_replay_drops" in runbook
    assert "sequence_boundary_drops" in runbook
    assert "before OHLCV aggregation" in runbook
    assert "before channel routing" in runbook
    assert "`subscriptions`" in runbook
    assert "Do not filter sequence observation to the" in runbook
    assert "validly sequenced `market_trades` payload" in runbook
    assert "does not authorize widening the two-second event-time window" in runbook


def test_runbook_requires_market_trades_snapshot_boundary_evidence():
    runbook = _unit("README.md")

    assert "type=snapshot" in runbook
    assert "PROVIDER_SNAPSHOT_BOUNDARY" in runbook
    assert "PROVIDER_SNAPSHOT_BOUNDARY_BAR_DROPPED" in runbook
    assert "before OHLCV aggregation" in runbook
    assert "Snapshot trades never enter Strategy, Risk or" in runbook
    assert "startup snapshot must preserve the existing `RESTART` boundary" in runbook
    assert "snapshot_boundaries" in runbook
    assert "snapshot_boundary_drops" in runbook
    assert "event_type=update" in runbook


def test_runbook_requires_post_snapshot_trade_quarantine_evidence():
    runbook = _unit("README.md")

    assert "in-band nonzero-sequence snapshot" in runbook
    assert "PROVIDER_SNAPSHOT_QUARANTINE_TRADES_DROPPED" in runbook
    assert "snapshot_quarantine_trades" in runbook
    assert "before the reorder" in runbook
    assert "strictly before that floor" in runbook
    assert "at or after the trusted snapshot floor remains" in runbook
    assert "Do not classify arbitrary late updates as snapshot history" in runbook
