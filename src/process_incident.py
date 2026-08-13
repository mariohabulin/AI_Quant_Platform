"""Append-only systemd process-failure evidence for PAPER supervision.

This adapter records service-manager exit evidence only. It does not classify
alerts, restart processes, import trading runtime components, or mutate
continuity state.
"""
import argparse
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import sys


def _systemd_value(value):
    if value is None:
        return "unknown"
    text = str(value).strip()
    return text or "unknown"


def _recorded_at(clock):
    value = clock()
    try:
        text = value.isoformat()
    except (AttributeError, TypeError, ValueError) as exc:
        raise ValueError("incident clock returned an invalid timestamp.") from exc
    if not text:
        raise ValueError("incident clock returned an invalid timestamp.")
    return text


def record_process_incident(
    audit_path,
    *,
    service_result,
    exit_code,
    exit_status,
    clock=None,
):
    """Append one failure record and return whether an incident was written.

    systemd supplies SERVICE_RESULT, EXIT_CODE and EXIT_STATUS to ExecStopPost.
    Only the explicit ``success`` result is treated as a clean stop. Missing or
    unknown lifecycle evidence fails visible instead of being assumed healthy.
    """
    service_result = _systemd_value(service_result)
    if service_result == "success":
        return False

    path = Path(audit_path)
    if path.exists() and path.is_dir():
        raise ValueError("audit path must be a file path.")
    path.parent.mkdir(parents=True, exist_ok=True)
    clock = clock or (lambda: datetime.now(timezone.utc))
    record = {
        "type": "PROCESS_INCIDENT",
        "reason": "UNEXPECTED_PROCESS_FAILURE",
        "service_result": service_result,
        "exit_code": _systemd_value(exit_code),
        "exit_status": _systemd_value(exit_status),
        "recorded_at": _recorded_at(clock),
        "real_orders": 0,
    }
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(record, sort_keys=True) + "\n")
        handle.flush()
        os.fsync(handle.fileno())
    return True


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="Record append-only systemd failure evidence for PAPER supervision."
    )
    parser.add_argument(
        "--audit", default="runtime/forward_paper_audit.jsonl"
    )
    args = parser.parse_args(argv)
    try:
        recorded = record_process_incident(
            args.audit,
            service_result=os.environ.get("SERVICE_RESULT"),
            exit_code=os.environ.get("EXIT_CODE"),
            exit_status=os.environ.get("EXIT_STATUS"),
        )
    except Exception as exc:
        print(
            f"Process incident recorder failed: {type(exc).__name__}: {exc}",
            file=sys.stderr,
        )
        return 1
    if recorded:
        print(
            "PROCESS_INCIDENT recorded: "
            f"service_result={_systemd_value(os.environ.get('SERVICE_RESULT'))} "
            f"exit_code={_systemd_value(os.environ.get('EXIT_CODE'))} "
            f"exit_status={_systemd_value(os.environ.get('EXIT_STATUS'))}"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
