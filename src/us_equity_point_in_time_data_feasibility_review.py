"""Static binding review for the zero-cost US-equity feasibility boundary."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

try:
    from us_equity_point_in_time_data_feasibility import (
        COMPONENT_ID,
        MONTHLY_DATA_BUDGET_USD,
        PARENT_COMMIT,
        PARENT_RESULT_SHA256,
        PROTOCOL_ID,
        REQUIRED_CAPABILITIES,
        equity_data_feasibility_declaration,
    )
except ImportError:  # pragma: no cover - package import compatibility
    from .us_equity_point_in_time_data_feasibility import (
        COMPONENT_ID,
        MONTHLY_DATA_BUDGET_USD,
        PARENT_COMMIT,
        PARENT_RESULT_SHA256,
        PROTOCOL_ID,
        REQUIRED_CAPABILITIES,
        equity_data_feasibility_declaration,
    )


STATUS = "US_EQUITY_POINT_IN_TIME_DATA_FEASIBILITY_REVIEWED_READ_ONLY_AUDIT_REQUIRED"
EXPECTED_PARENT_COMMIT = "816deff3bef51b3ddd8cf51ab89144587721a196"
EXPECTED_PARENT_RESULT_SHA256 = (
    "a972088fca185266a4a726b3a4512a90bed15f4e1d3a3467e76bedd171a7f286"
)
EXPECTED_HASHES = {
    "research_mandate": (
        "7c4e6405f8b09c138748644bb51abcc69d06c5c45cfcd7c2df450dfd1efe0c98"
    ),
    "portfolio_protocol": (
        "8615d0e9a21d0e3ca663626dd26f1ab19059e37e4fef39e0cf1954d55cdd0cd8"
    ),
    "terminal_result": (
        "d9f1ac12d56571752dc78f13dc0157df3df7023be37e07448e75e0f700c87794"
    ),
    "feasibility_protocol": (
        "8b860e2e282f38e13a2195b451d5d7359ae1a8321f12dc302478ce455d0d77bd"
    ),
    "feasibility_component": (
        "b1c48c79269bd24720e78282d55e93b3378616529fadffa183865fa448eb6e3e"
    ),
}


def _checkout_stable_sha256(path):
    payload = Path(path).read_bytes().replace(b"\r\n", b"\n")
    return hashlib.sha256(payload).hexdigest()


def review_equity_data_feasibility(root=None):
    root = Path(__file__).resolve().parents[1] if root is None else Path(root)
    paths = {
        "research_mandate": root / "SELECTIVE_SWING_TRADING_RESEARCH_MANDATE_V1.md",
        "portfolio_protocol": root
        / "SELECTIVE_SWING_PORTFOLIO_CONSTRUCTION_PROTOCOL_V1.md",
        "terminal_result": root
        / "KRAKEN_AI_DRIVEN_V2_REGIME_GATED_SELECTIVE_DEVELOPMENT_ATTEMPT_1_RESULT.md",
        "feasibility_protocol": root
        / "US_EQUITY_POINT_IN_TIME_DATA_FEASIBILITY_PROTOCOL_V1.md",
        "feasibility_component": root
        / "src"
        / "us_equity_point_in_time_data_feasibility.py",
    }
    observed = {
        name: _checkout_stable_sha256(path) for name, path in paths.items()
    }
    for name, expected in EXPECTED_HASHES.items():
        if observed[name] != expected:
            raise RuntimeError(f"US-equity feasibility source binding mismatch: {name}.")

    declaration = equity_data_feasibility_declaration()
    if PARENT_COMMIT != EXPECTED_PARENT_COMMIT:
        raise RuntimeError("US-equity feasibility parent commit mismatch.")
    if PARENT_RESULT_SHA256 != EXPECTED_PARENT_RESULT_SHA256:
        raise RuntimeError("US-equity feasibility parent result mismatch.")
    if declaration["protocol_id"] != PROTOCOL_ID:
        raise RuntimeError("US-equity feasibility protocol identity mismatch.")
    if declaration["component_id"] != COMPONENT_ID:
        raise RuntimeError("US-equity feasibility component identity mismatch.")
    if declaration["required_capabilities"] != list(REQUIRED_CAPABILITIES):
        raise RuntimeError("US-equity feasibility capability registry mismatch.")
    if MONTHLY_DATA_BUDGET_USD != 0:
        raise RuntimeError("US-equity feasibility zero-cost boundary mismatch.")
    required_false = (
        "paid_subscription_authorized",
        "paid_api_key_authorized",
        "automatic_paid_fallback",
        "source_documentation_opened",
        "free_schema_sample_opened",
        "market_values_opened",
        "labels_generated",
        "performance_evaluation_executed",
        "model_training_executed",
        "automatic_model_selection",
        "calibration_data_opened",
        "evaluation_data_opened",
        "candidate_v2_authorized",
        "portfolio_allocation_executed",
        "bounded_forward_paper_authorized",
        "cloud_strategy_execution_authorized",
        "real_orders_submitted",
        "live_execution_authorized",
    )
    if any(declaration[field] is not False for field in required_false):
        raise RuntimeError("US-equity feasibility safety boundary mismatch.")
    if declaration["monthly_data_budget_usd"] != 0:
        raise RuntimeError("US-equity feasibility declaration budget mismatch.")
    if declaration["source_documentation_review_authorized"] is not True:
        raise RuntimeError("US-equity documentation review authorization mismatch.")
    if declaration["free_schema_sample_review_authorized"] is not True:
        raise RuntimeError("US-equity free-sample authorization mismatch.")

    return {
        **declaration,
        "status": STATUS,
        "source_sha256_matches": {name: True for name in observed},
        "checkout_stable_hashing": True,
        "next_stage": "READ_ONLY_NO_COST_SOURCE_DOCUMENTATION_AND_SCHEMA_AUDIT",
    }


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="Review the zero-cost US-equity data-feasibility component."
    )
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    args = parser.parse_args(argv)
    print(json.dumps(review_equity_data_feasibility(args.root), indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
