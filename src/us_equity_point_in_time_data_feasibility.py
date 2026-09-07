"""Zero-cost source-capability boundary for point-in-time US-equity research."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
from pathlib import Path
import tempfile


SCHEMA_VERSION = 1
PROTOCOL_ID = "us-equity-point-in-time-data-feasibility-v1"
COMPONENT_ID = "us-equity-point-in-time-data-feasibility-v1"
PARENT_COMMIT = "816deff3bef51b3ddd8cf51ab89144587721a196"
PARENT_RESULT_SHA256 = (
    "a972088fca185266a4a726b3a4512a90bed15f4e1d3a3467e76bedd171a7f286"
)
RESEARCH_BOOK = "POINT_IN_TIME_CAN_SLIM_SWING"
MONTHLY_DATA_BUDGET_USD = 0

STATUS_FEASIBLE = (
    "US_EQUITY_POINT_IN_TIME_NO_COST_SOURCE_FEASIBLE_PROTOCOL_DESIGN_REQUIRED"
)
STATUS_GAP = (
    "US_EQUITY_POINT_IN_TIME_NO_COST_SOURCE_GAP_RECORDED_NO_PURCHASE_AUTHORIZED"
)

REQUIRED_CAPABILITIES = (
    "stable_security_identifier",
    "point_in_time_filing_availability",
    "as_reported_quarterly_and_annual_fundamentals",
    "active_and_delisted_security_master",
    "active_and_delisted_daily_ohlcv",
    "corporate_action_and_ticker_lineage",
    "point_in_time_sector_and_industry",
    "material_event_availability_timestamps",
    "institutional_sponsorship_availability_timestamps",
    "market_calendar_and_benchmark_history",
    "minimum_ten_year_history",
    "immutable_bulk_export_permitted",
)

INITIAL_SOURCE_CANDIDATES = {
    "SEC_EDGAR_PUBLIC_APIS": {
        "role": "PUBLIC_FILING_AND_DISCLOSURE_SCHEMA",
        "monthly_cost_usd": 0,
        "performance_source_preapproved": False,
    },
    "SHARADAR_FREE_DOW30_SAMPLE": {
        "role": "FREE_SCHEMA_SAMPLE_ONLY",
        "monthly_cost_usd": 0,
        "performance_source_preapproved": False,
    },
    "OFFICIAL_EXCHANGE_SYMBOL_DIRECTORIES": {
        "role": "PUBLIC_SECURITY_METADATA_SCHEMA",
        "monthly_cost_usd": 0,
        "performance_source_preapproved": False,
    },
}


def canonical_json_bytes(value):
    return (
        json.dumps(
            value,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
            allow_nan=False,
        )
        + "\n"
    ).encode("utf-8")


def equity_data_feasibility_declaration():
    return {
        "schema_version": SCHEMA_VERSION,
        "protocol_id": PROTOCOL_ID,
        "component_id": COMPONENT_ID,
        "parent_commit": PARENT_COMMIT,
        "parent_result_sha256": PARENT_RESULT_SHA256,
        "research_book": RESEARCH_BOOK,
        "required_capabilities": list(REQUIRED_CAPABILITIES),
        "initial_source_candidates": json.loads(
            json.dumps(INITIAL_SOURCE_CANDIDATES)
        ),
        "monthly_data_budget_usd": MONTHLY_DATA_BUDGET_USD,
        "source_documentation_review_authorized": True,
        "free_schema_sample_review_authorized": True,
        "paid_subscription_authorized": False,
        "paid_api_key_authorized": False,
        "automatic_paid_fallback": False,
        "source_documentation_opened": False,
        "free_schema_sample_opened": False,
        "market_values_opened": False,
        "labels_generated": False,
        "performance_evaluation_executed": False,
        "model_training_executed": False,
        "automatic_model_selection": False,
        "calibration_data_opened": False,
        "evaluation_data_opened": False,
        "candidate_v2_authorized": False,
        "portfolio_allocation_executed": False,
        "bounded_forward_paper_authorized": False,
        "cloud_strategy_execution_authorized": False,
        "real_orders_submitted": False,
        "live_execution_authorized": False,
        "status": (
            "US_EQUITY_POINT_IN_TIME_NO_COST_FEASIBILITY_IMPLEMENTED_"
            "READ_ONLY_AUDIT_REQUIRED"
        ),
        "next_stage": "READ_ONLY_NO_COST_SOURCE_DOCUMENTATION_AND_SCHEMA_AUDIT",
    }


def _validate_observation(observation):
    if not isinstance(observation, dict):
        raise ValueError("Every source observation must be an object.")
    expected_fields = {
        "source_id",
        "monthly_cost_usd",
        "sample_only",
        "license_reviewed",
        "capabilities",
    }
    if set(observation) != expected_fields:
        raise ValueError("Source observation field registry mismatch.")
    source_id = observation["source_id"]
    if not isinstance(source_id, str) or not source_id.strip():
        raise ValueError("source_id must be a non-empty string.")
    cost = observation["monthly_cost_usd"]
    if isinstance(cost, bool) or not isinstance(cost, (int, float)):
        raise ValueError("monthly_cost_usd must be a finite number.")
    if not math.isfinite(cost) or cost < 0:
        raise ValueError("monthly_cost_usd must be a finite nonnegative number.")
    if cost > MONTHLY_DATA_BUDGET_USD:
        raise ValueError("Paid source is not authorized by the zero-cost boundary.")
    for field in ("sample_only", "license_reviewed"):
        if not isinstance(observation[field], bool):
            raise ValueError(f"{field} must be Boolean.")
    capabilities = observation["capabilities"]
    if not isinstance(capabilities, dict) or set(capabilities) != set(
        REQUIRED_CAPABILITIES
    ):
        raise ValueError("Source capability registry mismatch.")
    if any(not isinstance(value, bool) for value in capabilities.values()):
        raise ValueError("Every source capability must be Boolean.")
    return source_id


def audit_no_cost_source_capabilities(observations):
    if not isinstance(observations, list) or not observations:
        raise ValueError("At least one source observation is required.")

    source_ids = []
    for observation in observations:
        source_id = _validate_observation(observation)
        if source_id in source_ids:
            raise ValueError(f"Duplicate source_id: {source_id}.")
        source_ids.append(source_id)

    eligible = [
        observation
        for observation in observations
        if not observation["sample_only"] and observation["license_reviewed"]
    ]
    provided_by = {
        capability: [
            observation["source_id"]
            for observation in eligible
            if observation["capabilities"][capability]
        ]
        for capability in REQUIRED_CAPABILITIES
    }
    missing = [
        capability for capability in REQUIRED_CAPABILITIES if not provided_by[capability]
    ]
    feasible = bool(eligible) and not missing
    status = STATUS_FEASIBLE if feasible else STATUS_GAP
    action = (
        "DESIGN_SEPARATE_EQUITY_HYPOTHESIS_PROTOCOL"
        if feasible
        else "HOLD_RESEARCH_OR_FIND_ANOTHER_NO_COST_SOURCE"
    )
    declaration = equity_data_feasibility_declaration()
    return {
        **declaration,
        "status": status,
        "action": action,
        "source_feasible": feasible,
        "observed_source_ids": source_ids,
        "observed_source_count": len(observations),
        "eligible_source_count": len(eligible),
        "sample_only_source_count": sum(
            observation["sample_only"] for observation in observations
        ),
        "license_reviewed_source_count": sum(
            observation["license_reviewed"] for observation in observations
        ),
        "monthly_data_cost_usd": sum(
            observation["monthly_cost_usd"] for observation in observations
        ),
        "capability_provided_by": provided_by,
        "missing_capabilities": missing,
        "gates": {
            "zero_monthly_cost_pass": True,
            "eligible_non_sample_source_present": bool(eligible),
            "all_required_capabilities_pass": not missing,
        },
        "source_documentation_opened": True,
        "free_schema_sample_opened": any(
            observation["sample_only"] for observation in observations
        ),
        "next_stage": (
            "PRE_REGISTER_SEPARATE_EQUITY_HYPOTHESIS"
            if feasible
            else "OPERATOR_DECISION_NO_AUTOMATIC_PURCHASE"
        ),
    }


def write_audit_result(result, output_path):
    output_path = Path(output_path)
    sidecar_path = output_path.with_suffix(output_path.suffix + ".sha256")
    if output_path.exists() or sidecar_path.exists():
        raise FileExistsError("Final feasibility evidence already exists.")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    payload = canonical_json_bytes(result)
    digest = hashlib.sha256(payload).hexdigest()
    sidecar = f"{digest}  {output_path.name}\n".encode("ascii")
    temporary_paths = []
    try:
        for target, content in ((output_path, payload), (sidecar_path, sidecar)):
            descriptor, temporary = tempfile.mkstemp(
                prefix=f".{target.name}.", dir=output_path.parent
            )
            temporary_paths.append(Path(temporary))
            with os.fdopen(descriptor, "wb") as handle:
                handle.write(content)
                handle.flush()
                os.fsync(handle.fileno())
        os.replace(temporary_paths[0], output_path)
        os.replace(temporary_paths[1], sidecar_path)
    finally:
        for temporary in temporary_paths:
            temporary.unlink(missing_ok=True)
    return digest


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="Declare or score the zero-cost US-equity source audit."
    )
    parser.add_argument("--observations", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args(argv)
    if args.observations is None:
        if args.output is not None:
            parser.error("--output requires --observations")
        result = equity_data_feasibility_declaration()
    else:
        if args.output is None:
            parser.error("--observations requires --output")
        observations = json.loads(args.observations.read_text(encoding="utf-8"))
        result = audit_no_cost_source_capabilities(observations)
        write_audit_result(result, args.output)
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
