import hashlib
import json
import os
from pathlib import Path
import sys

import pytest


sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src")))

from us_equity_point_in_time_data_feasibility import (
    MONTHLY_DATA_BUDGET_USD,
    PROTOCOL_ID,
    REQUIRED_CAPABILITIES,
    STATUS_FEASIBLE,
    STATUS_GAP,
    audit_no_cost_source_capabilities,
    canonical_json_bytes,
    equity_data_feasibility_declaration,
    write_audit_result,
)


ROOT = Path(__file__).resolve().parents[1]


def _source(
    source_id,
    *,
    enabled=(),
    sample_only=False,
    monthly_cost_usd=0,
    license_reviewed=True,
):
    return {
        "source_id": source_id,
        "monthly_cost_usd": monthly_cost_usd,
        "sample_only": sample_only,
        "license_reviewed": license_reviewed,
        "capabilities": {
            capability: capability in enabled for capability in REQUIRED_CAPABILITIES
        },
    }


def test_declaration_freezes_zero_cost_metadata_only_boundary():
    declaration = equity_data_feasibility_declaration()

    assert declaration["protocol_id"] == PROTOCOL_ID
    assert declaration["parent_commit"] == (
        "816deff3bef51b3ddd8cf51ab89144587721a196"
    )
    assert declaration["monthly_data_budget_usd"] == MONTHLY_DATA_BUDGET_USD == 0
    assert declaration["paid_subscription_authorized"] is False
    assert declaration["paid_api_key_authorized"] is False
    assert declaration["source_documentation_review_authorized"] is True
    assert declaration["free_schema_sample_review_authorized"] is True
    assert declaration["market_values_opened"] is False
    assert declaration["performance_evaluation_executed"] is False
    assert declaration["model_training_executed"] is False
    assert declaration["calibration_data_opened"] is False
    assert declaration["evaluation_data_opened"] is False
    assert declaration["candidate_v2_authorized"] is False
    assert declaration["real_orders_submitted"] is False


def test_required_capabilities_cover_point_in_time_and_survivorship_failures():
    assert REQUIRED_CAPABILITIES == (
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


def test_complete_zero_cost_capability_union_is_feasible_without_promotion():
    first_half = REQUIRED_CAPABILITIES[:6]
    second_half = REQUIRED_CAPABILITIES[6:]
    result = audit_no_cost_source_capabilities(
        [
            _source("PUBLIC_SOURCE_A", enabled=first_half),
            _source("PUBLIC_SOURCE_B", enabled=second_half),
        ]
    )

    assert result["status"] == STATUS_FEASIBLE
    assert result["source_feasible"] is True
    assert result["missing_capabilities"] == []
    assert result["action"] == "DESIGN_SEPARATE_EQUITY_HYPOTHESIS_PROTOCOL"
    assert result["monthly_data_cost_usd"] == 0
    assert result["market_values_opened"] is False
    assert result["performance_evaluation_executed"] is False
    assert result["model_training_executed"] is False
    assert result["candidate_v2_authorized"] is False


def test_missing_capabilities_record_gap_without_authorizing_purchase():
    result = audit_no_cost_source_capabilities(
        [
            _source(
                "SEC_EDGAR_PUBLIC_APIS",
                enabled=(
                    "stable_security_identifier",
                    "point_in_time_filing_availability",
                    "as_reported_quarterly_and_annual_fundamentals",
                    "material_event_availability_timestamps",
                    "institutional_sponsorship_availability_timestamps",
                    "minimum_ten_year_history",
                    "immutable_bulk_export_permitted",
                ),
            )
        ]
    )

    assert result["status"] == STATUS_GAP
    assert result["source_feasible"] is False
    assert "active_and_delisted_daily_ohlcv" in result["missing_capabilities"]
    assert "point_in_time_sector_and_industry" in result["missing_capabilities"]
    assert result["action"] == "HOLD_RESEARCH_OR_FIND_ANOTHER_NO_COST_SOURCE"
    assert result["paid_subscription_authorized"] is False
    assert result["automatic_paid_fallback"] is False


def test_schema_only_sample_cannot_satisfy_performance_capabilities():
    result = audit_no_cost_source_capabilities(
        [
            _source(
                "SHARADAR_FREE_DOW30_SAMPLE",
                enabled=REQUIRED_CAPABILITIES,
                sample_only=True,
            )
        ]
    )

    assert result["source_feasible"] is False
    assert result["eligible_source_count"] == 0
    assert result["sample_only_source_count"] == 1
    assert result["missing_capabilities"] == list(REQUIRED_CAPABILITIES)


@pytest.mark.parametrize("monthly_cost", [0.01, 1, 69])
def test_any_paid_source_is_rejected_before_capability_scoring(monthly_cost):
    with pytest.raises(ValueError, match="Paid source is not authorized"):
        audit_no_cost_source_capabilities(
            [
                _source(
                    "PAID_PROVIDER",
                    enabled=REQUIRED_CAPABILITIES,
                    monthly_cost_usd=monthly_cost,
                )
            ]
        )


def test_observation_schema_is_strict_and_duplicate_sources_are_rejected():
    valid = _source("PUBLIC_SOURCE", enabled=())

    with pytest.raises(ValueError, match="Duplicate source_id"):
        audit_no_cost_source_capabilities([valid, valid])

    malformed = dict(valid)
    malformed["capabilities"] = {"unknown": True}
    with pytest.raises(ValueError, match="capability registry"):
        audit_no_cost_source_capabilities([malformed])

    malformed = dict(valid)
    malformed["sample_only"] = 0
    with pytest.raises(ValueError, match="sample_only"):
        audit_no_cost_source_capabilities([malformed])


def test_unreviewed_license_cannot_contribute_capabilities():
    result = audit_no_cost_source_capabilities(
        [
            _source(
                "PUBLIC_SOURCE",
                enabled=REQUIRED_CAPABILITIES,
                license_reviewed=False,
            )
        ]
    )

    assert result["source_feasible"] is False
    assert result["license_reviewed_source_count"] == 0
    assert result["missing_capabilities"] == list(REQUIRED_CAPABILITIES)


def test_atomic_result_and_sidecar_are_canonical(tmp_path):
    result = audit_no_cost_source_capabilities(
        [_source("PUBLIC_SOURCE", enabled=())]
    )
    output = tmp_path / "audit.json"
    digest = write_audit_result(result, output)

    assert output.read_bytes() == canonical_json_bytes(result)
    assert digest == hashlib.sha256(output.read_bytes()).hexdigest()
    assert output.with_suffix(".json.sha256").read_text(encoding="ascii") == (
        f"{digest}  audit.json\n"
    )
    assert json.loads(output.read_text(encoding="utf-8"))["status"] == STATUS_GAP


def test_protocol_keeps_free_sample_and_paid_provider_boundaries_explicit():
    protocol = (
        ROOT / "US_EQUITY_POINT_IN_TIME_DATA_FEASIBILITY_PROTOCOL_V1.md"
    ).read_text(encoding="utf-8")

    for marker in (
        "$0 monthly data budget",
        "SEC/EDGAR",
        "free Dow 30 sample is schema-only",
        "A capability gap does not authorize a purchase",
        "No market value, label, return or model",
        "Calibration and Evaluation remain unopened",
    ):
        assert marker in protocol
