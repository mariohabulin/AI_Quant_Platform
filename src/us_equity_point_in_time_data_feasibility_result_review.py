"""Read-only review of zero-cost US-equity source-feasibility Attempt 1."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

try:
    from us_equity_point_in_time_data_feasibility import (
        PROTOCOL_ID as FEASIBILITY_PROTOCOL_ID,
        REQUIRED_CAPABILITIES,
        STATUS_GAP,
        audit_no_cost_source_capabilities,
    )
except ImportError:  # pragma: no cover - package import compatibility
    from .us_equity_point_in_time_data_feasibility import (
        PROTOCOL_ID as FEASIBILITY_PROTOCOL_ID,
        REQUIRED_CAPABILITIES,
        STATUS_GAP,
        audit_no_cost_source_capabilities,
    )


SCHEMA_VERSION = 1
PROTOCOL_ID = "us-equity-point-in-time-data-feasibility-result-review-v1"
COMPONENT_ID = PROTOCOL_ID
EXECUTION_COMMIT = "6a185e6d0dd9a7e31513f951a234601cfb9b06fa"
EVIDENCE_DIRECTORY_NAME = "us_equity_point_in_time_data_feasibility_v1"
OBSERVATIONS_FILENAME = "source_observations.json"
SOURCE_EVIDENCE_FILENAME = "source_evidence.json"
REPORT_FILENAME = "us_equity_point_in_time_data_feasibility_report.json"
EXPECTED_OBSERVATIONS_SHA256 = (
    "2d70d8bee1f0a7840a184f627ae9341419ac8eb9a8716273f5713052c0ab9a72"
)
EXPECTED_SOURCE_EVIDENCE_SHA256 = (
    "2ffa2430ff22f3fdf86f0bf7d7695ac634fe05586a8f4639702b2c9f3b6be539"
)
EXPECTED_REPORT_SHA256 = (
    "8f2348138376438129f3db1a94d0321e6b10177cd486f5436c935a167de0d2cb"
)
STATUS = "US_EQUITY_POINT_IN_TIME_DATA_FEASIBILITY_RESULT_REVIEW_PASS"
STATIC_STATUS = (
    "US_EQUITY_POINT_IN_TIME_DATA_FEASIBILITY_RESULT_REVIEW_"
    "REVIEWED_EXTERNAL_EVIDENCE_REQUIRED"
)
EXPECTED_ACTION = "HOLD_RESEARCH_OR_FIND_ANOTHER_NO_COST_SOURCE"

EXPECTED_SOURCE_IDS = (
    "SEC_EDGAR_PUBLIC_APIS",
    "SHARADAR_FREE_DOW30_SAMPLE",
    "OFFICIAL_EXCHANGE_SYMBOL_DIRECTORIES",
)
EXPECTED_MISSING_CAPABILITIES = (
    "stable_security_identifier",
    "active_and_delisted_security_master",
    "active_and_delisted_daily_ohlcv",
    "corporate_action_and_ticker_lineage",
    "point_in_time_sector_and_industry",
    "market_calendar_and_benchmark_history",
)
EXPECTED_SOURCE_URLS = {
    "SEC_EDGAR_PUBLIC_APIS": (
        "https://www.sec.gov/search-filings/edgar-application-programming-interfaces",
        "https://www.sec.gov/search-filings/edgar-search-assistance/accessing-edgar-data",
        "https://www.sec.gov/data-research/sec-markets-data/financial-statement-data-sets",
        "https://www.sec.gov/data-research/sec-markets-data/form-13f-data-sets",
        "https://www.sec.gov/about/webmaster-frequently-asked-questions",
    ),
    "SHARADAR_FREE_DOW30_SAMPLE": (
        "https://data.nasdaq.com/databases/SFA",
        "https://data.nasdaq.com/databases/SF1",
        "https://data.nasdaq.com/databases/SEP",
    ),
    "OFFICIAL_EXCHANGE_SYMBOL_DIRECTORIES": (
        "https://www.nasdaqtrader.com/Trader.aspx?id=SymbolDirDefs",
    ),
}


def _capabilities(*enabled):
    return {
        capability: capability in enabled for capability in REQUIRED_CAPABILITIES
    }


EXPECTED_OBSERVATIONS = [
    {
        "source_id": "SEC_EDGAR_PUBLIC_APIS",
        "monthly_cost_usd": 0,
        "sample_only": False,
        "license_reviewed": True,
        "capabilities": _capabilities(
            "point_in_time_filing_availability",
            "as_reported_quarterly_and_annual_fundamentals",
            "material_event_availability_timestamps",
            "institutional_sponsorship_availability_timestamps",
            "minimum_ten_year_history",
            "immutable_bulk_export_permitted",
        ),
    },
    {
        "source_id": "SHARADAR_FREE_DOW30_SAMPLE",
        "monthly_cost_usd": 0,
        "sample_only": True,
        "license_reviewed": False,
        "capabilities": _capabilities(
            "point_in_time_filing_availability",
            "as_reported_quarterly_and_annual_fundamentals",
        ),
    },
    {
        "source_id": "OFFICIAL_EXCHANGE_SYMBOL_DIRECTORIES",
        "monthly_cost_usd": 0,
        "sample_only": False,
        "license_reviewed": False,
        "capabilities": _capabilities(),
    },
]

EVIDENCE_REQUIRED_KEYS = {
    "schema_version",
    "audit_date_utc",
    "execution_commit",
    "protocol_id",
    "evidence_scope",
    "sources",
    "source_documentation_opened",
    "free_schema_sample_opened",
    "market_values_opened",
    "labels_generated",
    "performance_evaluation_executed",
    "model_training_executed",
    "paid_subscription_authorized",
    "paid_api_key_authorized",
    "real_orders_submitted",
    "live_execution_authorized",
}
SAFETY_FALSE_FIELDS = (
    "market_values_opened",
    "labels_generated",
    "performance_evaluation_executed",
    "model_training_executed",
    "paid_subscription_authorized",
    "paid_api_key_authorized",
    "real_orders_submitted",
    "live_execution_authorized",
)


def _sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def _read_json(path, label):
    try:
        return json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise RuntimeError(f"Unable to read {label} JSON.") from exc


def _validate_source_evidence(evidence, observations):
    if not isinstance(evidence, dict) or set(evidence) != EVIDENCE_REQUIRED_KEYS:
        raise RuntimeError("Source-evidence schema mismatch.")
    expected_identity = {
        "schema_version": SCHEMA_VERSION,
        "audit_date_utc": "2026-09-07",
        "execution_commit": EXECUTION_COMMIT,
        "protocol_id": FEASIBILITY_PROTOCOL_ID,
        "evidence_scope": "OFFICIAL_DOCUMENTATION_AND_PUBLIC_SCHEMA_ONLY",
        "source_documentation_opened": True,
        "free_schema_sample_opened": True,
    }
    for field, expected in expected_identity.items():
        if evidence.get(field) != expected:
            raise RuntimeError(f"Source-evidence identity mismatch: {field}.")
    if any(evidence.get(field) is not False for field in SAFETY_FALSE_FIELDS):
        raise RuntimeError("Source-evidence safety boundary mismatch.")
    sources = evidence.get("sources")
    if not isinstance(sources, list) or [item.get("source_id") for item in sources] != list(
        EXPECTED_SOURCE_IDS
    ):
        raise RuntimeError("Source-evidence source registry mismatch.")
    observations_by_id = {item["source_id"]: item for item in observations}
    for source in sources:
        if set(source) != {
            "source_id",
            "official_urls",
            "finding",
            "license_reuse_reviewed",
            "market_values_opened",
        }:
            raise RuntimeError("Source-evidence item schema mismatch.")
        source_id = source["source_id"]
        if tuple(source["official_urls"]) != EXPECTED_SOURCE_URLS[source_id]:
            raise RuntimeError(f"Source-evidence official URL registry mismatch: {source_id}.")
        if not isinstance(source["finding"], str) or not source["finding"].strip():
            raise RuntimeError(f"Source-evidence finding missing: {source_id}.")
        if source["license_reuse_reviewed"] is not observations_by_id[source_id][
            "license_reviewed"
        ]:
            raise RuntimeError(f"Source-evidence license mismatch: {source_id}.")
        if source["market_values_opened"] is not False:
            raise RuntimeError(f"Source-evidence market-value mismatch: {source_id}.")


def result_review_declaration():
    return {
        "schema_version": SCHEMA_VERSION,
        "protocol_id": PROTOCOL_ID,
        "component_id": COMPONENT_ID,
        "execution_commit": EXECUTION_COMMIT,
        "feasibility_protocol_id": FEASIBILITY_PROTOCOL_ID,
        "expected_observation_source_ids": list(EXPECTED_SOURCE_IDS),
        "expected_observations_sha256": EXPECTED_OBSERVATIONS_SHA256,
        "expected_source_evidence_sha256": EXPECTED_SOURCE_EVIDENCE_SHA256,
        "expected_report_sha256": EXPECTED_REPORT_SHA256,
        "expected_source_status": STATUS_GAP,
        "expected_action": EXPECTED_ACTION,
        "expected_missing_capabilities": list(EXPECTED_MISSING_CAPABILITIES),
        "external_evidence_opened": False,
        "market_values_opened": False,
        "labels_generated": False,
        "performance_evaluation_executed": False,
        "model_training_executed": False,
        "paid_subscription_authorized": False,
        "paid_api_key_authorized": False,
        "calibration_data_opened": False,
        "evaluation_data_opened": False,
        "candidate_v2_authorized": False,
        "real_orders_submitted": False,
        "live_execution_authorized": False,
        "status": STATIC_STATUS,
        "next_stage": "EXTERNAL_ZERO_COST_AUDIT_EVIDENCE_REVIEW",
    }


def analyze_zero_cost_source_audit(observations, evidence, report):
    if observations != EXPECTED_OBSERVATIONS:
        raise RuntimeError("Zero-cost source observation registry mismatch.")
    _validate_source_evidence(evidence, observations)
    recomputed = audit_no_cost_source_capabilities(observations)
    if report != recomputed:
        raise RuntimeError("Zero-cost source recomputed report mismatch.")
    if report.get("status") != STATUS_GAP or report.get("action") != EXPECTED_ACTION:
        raise RuntimeError("Zero-cost source terminal result mismatch.")
    if report.get("missing_capabilities") != list(EXPECTED_MISSING_CAPABILITIES):
        raise RuntimeError("Zero-cost source exact gap mismatch.")
    if (
        report.get("observed_source_ids") != list(EXPECTED_SOURCE_IDS)
        or report.get("observed_source_count") != 3
        or report.get("eligible_source_count") != 1
        or report.get("sample_only_source_count") != 1
        or report.get("license_reviewed_source_count") != 1
        or report.get("monthly_data_cost_usd") != 0
        or report.get("source_feasible") is not False
    ):
        raise RuntimeError("Zero-cost source count or cost mismatch.")
    report_false = SAFETY_FALSE_FIELDS + (
        "automatic_paid_fallback",
        "automatic_model_selection",
        "calibration_data_opened",
        "evaluation_data_opened",
        "candidate_v2_authorized",
        "portfolio_allocation_executed",
        "bounded_forward_paper_authorized",
        "cloud_strategy_execution_authorized",
    )
    if any(report.get(field) is not False for field in report_false):
        raise RuntimeError("Zero-cost source report safety boundary mismatch.")
    if report.get("next_stage") != "OPERATOR_DECISION_NO_AUTOMATIC_PURCHASE":
        raise RuntimeError("Zero-cost source next-stage mismatch.")
    return {
        **result_review_declaration(),
        "status": STATUS,
        "source_status": STATUS_GAP,
        "action": EXPECTED_ACTION,
        "source_feasible": False,
        "missing_capabilities": list(EXPECTED_MISSING_CAPABILITIES),
        "documented_capability_count": (
            len(REQUIRED_CAPABILITIES) - len(EXPECTED_MISSING_CAPABILITIES)
        ),
        "observed_source_count": 3,
        "eligible_source_count": 1,
        "monthly_data_cost_usd": 0,
        "purchase_authorized": False,
        "source_documentation_opened": True,
        "free_schema_sample_opened": True,
        "external_evidence_opened": True,
        "next_stage": "OPERATOR_DECISION_NO_AUTOMATIC_PURCHASE",
    }


def _verify_file_and_sidecar(root, filename, expected_digest):
    path = root / filename
    sidecar = root / f"{filename}.sha256"
    observed = _sha256(path)
    if observed != expected_digest:
        raise RuntimeError(f"Zero-cost source evidence hash mismatch: {filename}.")
    expected_sidecar = f"{observed}  {filename}\n".encode("ascii")
    if sidecar.read_bytes() != expected_sidecar:
        raise RuntimeError(f"Zero-cost source sidecar mismatch: {filename}.")
    return observed


def read_zero_cost_source_audit_result(evidence_root):
    root = Path(evidence_root)
    expected_files = {
        OBSERVATIONS_FILENAME,
        SOURCE_EVIDENCE_FILENAME,
        REPORT_FILENAME,
        f"{OBSERVATIONS_FILENAME}.sha256",
        f"{SOURCE_EVIDENCE_FILENAME}.sha256",
        f"{REPORT_FILENAME}.sha256",
    }
    if not root.is_dir() or {path.name for path in root.iterdir()} != expected_files:
        raise RuntimeError("Zero-cost source evidence file registry mismatch.")
    before = {name: _sha256(root / name) for name in expected_files}
    observed_hashes = {
        OBSERVATIONS_FILENAME: _verify_file_and_sidecar(
            root, OBSERVATIONS_FILENAME, EXPECTED_OBSERVATIONS_SHA256
        ),
        SOURCE_EVIDENCE_FILENAME: _verify_file_and_sidecar(
            root, SOURCE_EVIDENCE_FILENAME, EXPECTED_SOURCE_EVIDENCE_SHA256
        ),
        REPORT_FILENAME: _verify_file_and_sidecar(
            root, REPORT_FILENAME, EXPECTED_REPORT_SHA256
        ),
    }
    result = analyze_zero_cost_source_audit(
        _read_json(root / OBSERVATIONS_FILENAME, "source observations"),
        _read_json(root / SOURCE_EVIDENCE_FILENAME, "source evidence"),
        _read_json(root / REPORT_FILENAME, "audit report"),
    )
    after = {name: _sha256(root / name) for name in expected_files}
    if before != after:
        raise RuntimeError("Zero-cost source evidence changed during review.")
    return {
        **result,
        "evidence_sha256_matches": {
            name: observed_hashes[name] == expected
            for name, expected in (
                (OBSERVATIONS_FILENAME, EXPECTED_OBSERVATIONS_SHA256),
                (SOURCE_EVIDENCE_FILENAME, EXPECTED_SOURCE_EVIDENCE_SHA256),
                (REPORT_FILENAME, EXPECTED_REPORT_SHA256),
            )
        },
        "sidecars_verified": True,
        "evidence_unchanged": True,
    }


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="Review zero-cost US-equity source-feasibility evidence."
    )
    parser.add_argument("--evidence", type=Path)
    args = parser.parse_args(argv)
    result = (
        result_review_declaration()
        if args.evidence is None
        else read_zero_cost_source_audit_result(args.evidence)
    )
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
