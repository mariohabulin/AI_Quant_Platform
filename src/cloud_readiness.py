"""Provider-neutral pre-deployment gate for controlled cloud paper runtime."""
from dataclasses import asdict, dataclass
import argparse
import importlib
import json
import os
from pathlib import Path
import sys


@dataclass(frozen=True)
class CloudRuntimeConfig:
    mode: str
    runtime_dir: object
    audit_path: object
    state_path: object
    session_bars: object
    monitor_interval_seconds: object
    stale_after_seconds: object
    real_execution_enabled: object

    @staticmethod
    def _number(value, integer=False):
        try:
            return int(value) if integer else float(value)
        except (TypeError, ValueError):
            return None

    @staticmethod
    def _boolean(value):
        normalized = str(value).strip().lower()
        if normalized == "true":
            return True
        if normalized == "false":
            return False
        return None

    @classmethod
    def from_env(cls, environ=None):
        env = os.environ if environ is None else environ
        runtime_value = str(env.get("AI_ALPHA_RUNTIME_DIR", "")).strip()
        runtime_dir = Path(runtime_value) if runtime_value else Path("")
        return cls(
            mode=str(env.get("AI_ALPHA_MODE", "")).strip().upper(),
            runtime_dir=runtime_dir,
            audit_path=runtime_dir / "forward_paper_audit.jsonl",
            state_path=runtime_dir / "forward_paper_state.json",
            session_bars=cls._number(env.get("AI_ALPHA_SESSION_BARS"), integer=True),
            monitor_interval_seconds=cls._number(
                env.get("AI_ALPHA_MONITOR_INTERVAL_SECONDS")
            ),
            stale_after_seconds=cls._number(
                env.get("AI_ALPHA_STALE_AFTER_SECONDS")
            ),
            real_execution_enabled=cls._boolean(
                env.get("AI_ALPHA_REAL_EXECUTION_ENABLED")
            ),
        )


@dataclass(frozen=True)
class CloudReadinessCheck:
    name: str
    status: str
    reason: str
    details: str = ""


@dataclass(frozen=True)
class CloudReadinessReport:
    status: str
    checks: tuple

    def to_dict(self):
        return asdict(self)


class CloudRuntimeReadinessGate:
    """Validate safe cloud configuration without starting trading processes."""

    def __init__(
        self, config, *, storage_probe=None, import_probe=None, python_version=None
    ):
        if not isinstance(config, CloudRuntimeConfig):
            raise TypeError("config must be a CloudRuntimeConfig.")
        self.config = config
        self.storage_probe = storage_probe or self._storage_probe
        self.import_probe = import_probe or importlib.import_module
        self.python_version = python_version or sys.version_info[:2]

    @staticmethod
    def _check(name, passed, success, failure, details=""):
        return CloudReadinessCheck(
            name, "PASS" if passed else "FAIL",
            success if passed else failure, details,
        )

    @staticmethod
    def _storage_probe(runtime_dir):
        runtime_dir = Path(runtime_dir)
        probe = runtime_dir / ".cloud_readiness.probe"
        try:
            runtime_dir.mkdir(parents=True, exist_ok=True)
            probe.write_text("cloud-readiness", encoding="utf-8")
            if probe.read_text(encoding="utf-8") != "cloud-readiness":
                return False
            probe.unlink()
            return True
        except OSError:
            try:
                if probe.exists():
                    probe.unlink()
            except OSError:
                pass
            return False

    def _execution_check(self):
        passed = (
            self.config.mode == "PAPER"
            and self.config.real_execution_enabled is False
        )
        return self._check(
            "execution_lock", passed,
            "Cloud runtime is explicitly paper-only with real execution disabled.",
            "Cloud readiness requires AI_ALPHA_MODE=PAPER and explicit real execution=false.",
        )

    def _bounded_session_check(self):
        value = self.config.session_bars
        passed = isinstance(value, int) and not isinstance(value, bool) and value > 0
        return self._check(
            "bounded_session", passed,
            "Cloud validation session has a positive bar bound.",
            "Cloud validation requires a positive integer session bar bound.",
            details=f"bars={value}",
        )

    def _monitoring_check(self):
        interval = self.config.monitor_interval_seconds
        stale = self.config.stale_after_seconds
        passed = (
            isinstance(interval, (int, float)) and not isinstance(interval, bool)
            and isinstance(stale, (int, float)) and not isinstance(stale, bool)
            and interval > 0 and stale > 0 and interval < stale
        )
        return self._check(
            "monitoring_cadence", passed,
            "Monitoring cadence is positive and faster than the stale threshold.",
            "Monitoring interval and stale threshold must be positive, with interval < stale threshold.",
            details=f"interval={interval}s stale_after={stale}s",
        )

    def _paths_check(self):
        runtime = Path(self.config.runtime_dir)
        audit = Path(self.config.audit_path)
        state = Path(self.config.state_path)
        passed = (
            runtime.is_absolute()
            and audit.is_absolute()
            and state.is_absolute()
            and audit.parent.resolve() == runtime.resolve()
            and state.parent.resolve() == runtime.resolve()
            and audit != state
        )
        return self._check(
            "persistent_paths", passed,
            "Audit and continuity state share one absolute persistent runtime directory.",
            "Audit/state paths must be distinct files inside one absolute persistent runtime directory.",
            details=f"runtime_dir={runtime}",
        )

    def _storage_check(self, paths_ready):
        if not paths_ready:
            return self._check(
                "persistent_storage", False, "",
                "Persistent storage probe is blocked until path validation passes.",
            )
        try:
            passed = bool(self.storage_probe(Path(self.config.runtime_dir)))
        except Exception:
            passed = False
        return self._check(
            "persistent_storage", passed,
            "Persistent runtime directory passed write/read/cleanup probe.",
            "Persistent runtime directory is not safely writable.",
        )

    def _components_check(self):
        required = ("src.forward_paper_session", "src.operational_monitoring")
        try:
            for name in required:
                self.import_probe(name)
            passed = True
        except Exception:
            passed = False
        return self._check(
            "runtime_components", passed,
            "Forward-paper and operational-monitoring entrypoints are importable.",
            "Required cloud runtime components are not importable.",
        )

    def _python_check(self):
        major, minor = self.python_version
        passed = major == 3 and 12 <= minor <= 14
        return self._check(
            "python_runtime", passed,
            "Python runtime is within the validated 3.12-3.14 compatibility range.",
            "Cloud Python runtime must be within the validated 3.12-3.14 range.",
            details=f"python={major}.{minor}",
        )

    def run(self):
        paths_check = self._paths_check()
        checks = (
            self._execution_check(),
            self._bounded_session_check(),
            self._monitoring_check(),
            paths_check,
            self._storage_check(paths_check.status == "PASS"),
            self._components_check(),
            self._python_check(),
        )
        status = "PASS" if all(check.status == "PASS" for check in checks) else "FAIL"
        return CloudReadinessReport(status, checks)


def format_cloud_readiness_report(report):
    lines = [f"Cloud Runtime Readiness | status={report.status}"]
    lines.extend(
        f"{check.status} {check.name}: {check.reason}"
        + (f" ({check.details})" if check.details else "")
        for check in report.checks
    )
    return "\n".join(lines)


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="Provider-neutral cloud paper-runtime readiness gate."
    )
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)
    report = CloudRuntimeReadinessGate(CloudRuntimeConfig.from_env()).run()
    if args.json:
        print(json.dumps(report.to_dict(), sort_keys=True))
    else:
        print(format_cloud_readiness_report(report))
    return 0 if report.status == "PASS" else 2


if __name__ == "__main__":
    raise SystemExit(main())
