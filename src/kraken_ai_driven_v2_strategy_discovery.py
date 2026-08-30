"""Nonexecuting hybrid strategy-discovery and learning contract for Kraken V2."""

import copy
from dataclasses import dataclass
import hashlib
import json
import re


SCHEMA_VERSION = 1
PROTOCOL_ID = (
    "kraken-btc-eth-xrp-ai-driven-v2-hybrid-strategy-discovery-learning-v1"
)
STATUS = "KRAKEN_AI_V2_HYBRID_DISCOVERY_PROTOCOL_FROZEN_NO_RUN_AUTHORIZATION"
HYBRID_ARCHITECTURE_MODE = (
    "SHARED_CATALOG_ASSET_REGIME_SPECIFIC_ROUTING_SHARED_SAFETY_ENVELOPE"
)

ASSET_ORDER = ("BTC-USD", "ETH-USD", "XRP-USD")
DATASET_ID = (
    "kraken-spot-btc-eth-xrp-native-1d-20190101-20260401-archive-only-v2"
)
DATASET_MANIFEST_SHA256 = (
    "8c91b42f2bc0c16a0ef0c6b4373572ac53fbf7f5937d4ebbbe75a0d39483df1c"
)
PARTITION_PROTOCOL_ID = "kraken-btc-eth-xrp-ai-driven-v2-partition-v1"
REFERENCE_A_CLOSURE_STATUS = (
    "KRAKEN_AI_V2_DEVELOPMENT_REFERENCE_A_CLOSED_NO_TRADE_HOLD_CASH"
)
REFERENCE_A_REPORT_SHA256 = (
    "f537410d2a237be207951b638518d80e861289dafa7db9b5c2322ffa32d4e594"
)
REFERENCE_A_SIGNAL_CONTRACT_ID = "kraken-ai-v2-ccvr-reference-a-v1"
REFERENCE_A_EXECUTION_CONTRACT_ID = (
    "kraken-ai-v2-risk-execution-reference-a-v1"
)
REFERENCE_A_RUN_ID = (
    "kraken-btc-eth-xrp-ai-driven-v2-development-reference-a-v1"
)

REGIME_CATALOG = (
    {
        "regime_id": "DOWNTREND_CAPITULATION",
        "mechanism": "DECLINE_WITH_VOLATILITY_AND_VOLUME_SHOCK",
        "fallback_action": "HOLD_CASH",
    },
    {
        "regime_id": "UPTREND_PULLBACK",
        "mechanism": "POSITIVE_TREND_WITH_CAUSAL_RETRACEMENT",
        "fallback_action": "HOLD_CASH",
    },
    {
        "regime_id": "RANGE_BOUND",
        "mechanism": "BOUNDED_PRICE_DISTRIBUTION_WITHOUT_DIRECTIONAL_TREND",
        "fallback_action": "HOLD_CASH",
    },
    {
        "regime_id": "VOLATILITY_EXPANSION",
        "mechanism": "CAUSAL_RANGE_BREAK_WITH_EXPANDING_VOLATILITY",
        "fallback_action": "HOLD_CASH",
    },
    {
        "regime_id": "UNCLASSIFIED",
        "mechanism": "INSUFFICIENT_OR_CONFLICTING_CAUSAL_EVIDENCE",
        "fallback_action": "HOLD_CASH",
    },
)

FAMILY_CATALOG = (
    {
        "family_id": "CAPITULATION_RECOVERY",
        "mechanism": "EXHAUSTION_STABILIZATION_AND_RECOVERY",
        "eligible_regimes": ("DOWNTREND_CAPITULATION",),
        "permitted_indicators": (
            "RETURN",
            "VOLUME_RATIO",
            "ATR",
            "CLOSE_LOCATION",
        ),
        "family_specific_signal_contract_required": True,
        "family_specific_execution_contract_required": True,
        "reference_a_exact_variant_closed": True,
    },
    {
        "family_id": "TREND_PULLBACK_CONTINUATION",
        "mechanism": "TREND_PERSISTENCE_AFTER_CAUSAL_PULLBACK",
        "eligible_regimes": ("UPTREND_PULLBACK",),
        "permitted_indicators": (
            "EMA",
            "ADX",
            "MACD",
            "VOLUME_RATIO",
            "ATR",
        ),
        "family_specific_signal_contract_required": True,
        "family_specific_execution_contract_required": True,
        "reference_a_exact_variant_closed": False,
    },
    {
        "family_id": "RANGE_MEAN_REVERSION",
        "mechanism": "REVERSAL_FROM_CAUSAL_RANGE_EXTREME",
        "eligible_regimes": ("RANGE_BOUND",),
        "permitted_indicators": (
            "RSI",
            "BOLLINGER_BANDS",
            "STOCHASTIC",
            "ATR",
            "VOLUME_RATIO",
        ),
        "family_specific_signal_contract_required": True,
        "family_specific_execution_contract_required": True,
        "reference_a_exact_variant_closed": False,
    },
    {
        "family_id": "VOLATILITY_BREAKOUT",
        "mechanism": "CAUSAL_CHANNEL_BREAK_WITH_VOLATILITY_CONFIRMATION",
        "eligible_regimes": ("VOLATILITY_EXPANSION",),
        "permitted_indicators": (
            "DONCHIAN_CHANNEL",
            "ATR",
            "VOLUME_RATIO",
            "CLOSE_LOCATION",
            "ADX",
        ),
        "family_specific_signal_contract_required": True,
        "family_specific_execution_contract_required": True,
        "reference_a_exact_variant_closed": False,
    },
)

DISCOVERY_BUDGET = {
    "max_hypotheses_per_round": 6,
    "max_variants_per_family_per_round": 2,
    "max_routes_per_asset_per_round": 4,
    "max_rounds_under_protocol": 2,
    "max_total_hypotheses_under_protocol": 12,
    "min_indicators_per_hypothesis": 2,
    "max_indicators_per_hypothesis": 5,
}

SHARED_SAFETY_ENVELOPE = {
    "safety_envelope_id": "kraken-ai-v2-shared-portfolio-safety-envelope-v1",
    "cost_profile_id": "kraken-tier1-taker-adverse-20260829-v1",
    "initial_capital": 5000.0,
    "quote_currency": "USD_RESEARCH_NOTIONAL",
    "position_risk_fraction_ceiling": 0.005,
    "total_open_risk_fraction_ceiling": 0.015,
    "maximum_concurrent_positions": 3,
    "per_asset_notional_fraction_ceiling": 1.0 / 3.0,
    "cash_only": True,
    "leverage_permitted": False,
    "short_positions_permitted": False,
    "completed_bar_signal_required": True,
    "next_open_entry_required": True,
    "entry_bar_protection_required": True,
    "stop_first_intrabar_ordering_required": True,
    "adverse_cost_model_required": True,
    "synthetic_terminal_force_close_permitted": False,
}

FEEDBACK_SCHEMA = (
    "signal_count",
    "entry_approved_count",
    "entry_rejection_reason_counts",
    "closed_trade_count",
    "net_expectancy_r",
    "modeled_cost_drag",
    "maximum_marked_drawdown_fraction",
    "time_slice_results",
    "asset_results",
    "regime_results",
    "unresolved_position_count",
    "failure_attribution",
)

REQUIRED_INTEREST_GATES = (
    "SAMPLE_SUFFICIENCY",
    "ADVERSE_COST_SURVIVAL",
    "CHRONOLOGICAL_STABILITY",
    "ASSET_CONCENTRATION",
    "DRAWDOWN_BOUND",
    "FAILURE_ATTRIBUTION_COMPLETE",
)

ROOT_MANIFEST_FIELDS = {
    "schema_version",
    "protocol_id",
    "round_id",
    "partition",
    "hypotheses",
    "development_data_access_authorized",
    "calibration_authorized",
    "evaluation_authorized",
    "automatic_mutation_authorized",
    "automatic_ranking_authorized",
    "candidate_v2_authorized",
    "round_execution_authorized",
}
HYPOTHESIS_FIELDS = {
    "hypothesis_id",
    "family_id",
    "asset_scope",
    "regime_scope",
    "indicator_set",
    "economic_thesis",
    "signal_contract_id",
    "execution_contract_id",
    "development_gate_id",
    "parent_hypothesis_id",
    "source_feedback_sha256s",
}
FALSE_AUTHORIZATION_FIELDS = (
    "development_data_access_authorized",
    "calibration_authorized",
    "evaluation_authorized",
    "automatic_mutation_authorized",
    "automatic_ranking_authorized",
    "candidate_v2_authorized",
    "round_execution_authorized",
)
BLOCKED_REFERENCE_A_IDENTITIES = {
    REFERENCE_A_SIGNAL_CONTRACT_ID,
    REFERENCE_A_EXECUTION_CONTRACT_ID,
    REFERENCE_A_RUN_ID,
}
IDENTIFIER_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{2,127}$")
SHA256_PATTERN = re.compile(r"^[0-9a-f]{64}$")


@dataclass(frozen=True)
class LockedHypothesisManifest:
    payload: dict
    sha256: str


def _catalog_payload(catalog):
    result = []
    for entry in catalog:
        normalized = {}
        for key, value in entry.items():
            normalized[key] = list(value) if isinstance(value, tuple) else value
        result.append(normalized)
    return result


def _canonical_json_bytes(value):
    try:
        return json.dumps(
            value,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
            allow_nan=False,
        ).encode("utf-8")
    except (TypeError, ValueError) as exc:
        raise ValueError("Hypothesis manifest must be canonical JSON data.") from exc


def _require_exact_fields(value, required, label):
    if not isinstance(value, dict):
        raise TypeError(f"{label} must be an object.")
    actual = set(value)
    if actual != required:
        missing = sorted(required - actual)
        extra = sorted(actual - required)
        raise ValueError(
            f"{label} fields mismatch; missing={missing}, extra={extra}."
        )


def _identifier(value, label):
    if not isinstance(value, str) or not IDENTIFIER_PATTERN.fullmatch(value):
        raise ValueError(f"{label} must be a stable identifier.")
    return value


def _ordered_unique_strings(value, label):
    if not isinstance(value, list) or not value:
        raise ValueError(f"{label} must be a nonempty list.")
    if any(not isinstance(item, str) or not item for item in value):
        raise ValueError(f"{label} must contain nonempty strings.")
    if len(value) != len(set(value)):
        raise ValueError(f"{label} must not contain duplicates.")
    return list(value)


def _validate_hypothesis(raw):
    _require_exact_fields(raw, HYPOTHESIS_FIELDS, "Hypothesis")
    hypothesis = copy.deepcopy(raw)
    hypothesis_id = _identifier(hypothesis["hypothesis_id"], "Hypothesis ID")
    family_id = hypothesis["family_id"]
    families = {item["family_id"]: item for item in FAMILY_CATALOG}
    if family_id not in families:
        raise ValueError(f"Unknown strategy family: {family_id}.")
    family = families[family_id]

    assets = _ordered_unique_strings(hypothesis["asset_scope"], "Asset scope")
    expected_order = [asset for asset in ASSET_ORDER if asset in assets]
    if assets != expected_order:
        raise ValueError(
            "Hypothesis asset scope must use the canonical asset order and known assets."
        )

    regimes = _ordered_unique_strings(
        hypothesis["regime_scope"], "Regime scope"
    )
    if not set(regimes) <= set(family["eligible_regimes"]):
        raise ValueError(
            f"Hypothesis regime scope is not eligible for family {family_id}."
        )

    indicators = _ordered_unique_strings(
        hypothesis["indicator_set"], "Indicator set"
    )
    minimum = DISCOVERY_BUDGET["min_indicators_per_hypothesis"]
    maximum = DISCOVERY_BUDGET["max_indicators_per_hypothesis"]
    if not minimum <= len(indicators) <= maximum:
        raise ValueError(
            f"Hypothesis indicator count must be between {minimum} and {maximum}."
        )
    if not set(indicators) <= set(family["permitted_indicators"]):
        raise ValueError(
            f"Hypothesis indicator is not permitted for family {family_id}."
        )

    thesis = hypothesis["economic_thesis"]
    if not isinstance(thesis, str) or len(thesis.strip()) < 60:
        raise ValueError("Hypothesis economic thesis must be at least 60 characters.")
    hypothesis["economic_thesis"] = thesis.strip()

    identity_fields = (
        "hypothesis_id",
        "signal_contract_id",
        "execution_contract_id",
        "development_gate_id",
    )
    for field in identity_fields:
        identity = _identifier(hypothesis[field], field.replace("_", " ").title())
        if identity in BLOCKED_REFERENCE_A_IDENTITIES:
            raise ValueError("Reference A identity reuse is prohibited.")

    parent = hypothesis["parent_hypothesis_id"]
    if parent is not None:
        _identifier(parent, "Parent hypothesis ID")

    feedback_hashes = hypothesis["source_feedback_sha256s"]
    if not isinstance(feedback_hashes, list):
        raise ValueError("Source feedback SHA-256 values must be a list.")
    if len(feedback_hashes) > 3 or len(feedback_hashes) != len(set(feedback_hashes)):
        raise ValueError("Source feedback SHA-256 budget or uniqueness failed.")
    if any(
        not isinstance(digest, str) or not SHA256_PATTERN.fullmatch(digest)
        for digest in feedback_hashes
    ):
        raise ValueError("Source feedback SHA-256 value is invalid.")

    hypothesis["hypothesis_id"] = hypothesis_id
    hypothesis["asset_scope"] = assets
    hypothesis["regime_scope"] = regimes
    hypothesis["indicator_set"] = indicators
    return hypothesis


def validate_hypothesis_manifest(manifest):
    """Validate and canonically lock a future, still-unauthorized research round."""

    _require_exact_fields(manifest, ROOT_MANIFEST_FIELDS, "Hypothesis manifest")
    raw = copy.deepcopy(manifest)
    if raw["schema_version"] != SCHEMA_VERSION:
        raise ValueError("Hypothesis manifest schema version mismatch.")
    if raw["protocol_id"] != PROTOCOL_ID:
        raise ValueError("Hypothesis manifest protocol ID mismatch.")
    _identifier(raw["round_id"], "Round ID")
    if raw["partition"] != "DEVELOPMENT":
        raise ValueError("Hypothesis manifest is restricted to DEVELOPMENT.")
    for field in FALSE_AUTHORIZATION_FIELDS:
        if raw[field] is not False:
            raise ValueError(f"Hypothesis manifest {field} must remain false.")

    hypotheses = raw["hypotheses"]
    maximum = DISCOVERY_BUDGET["max_hypotheses_per_round"]
    if not isinstance(hypotheses, list) or not 1 <= len(hypotheses) <= maximum:
        raise ValueError(
            f"Hypothesis manifest must contain between 1 and {maximum} hypotheses."
        )
    validated = [_validate_hypothesis(item) for item in hypotheses]
    identifiers = [item["hypothesis_id"] for item in validated]
    if len(identifiers) != len(set(identifiers)):
        raise ValueError("Hypothesis IDs must be unique inside one round.")

    family_counts = {item["family_id"]: 0 for item in FAMILY_CATALOG}
    asset_counts = {asset: 0 for asset in ASSET_ORDER}
    for hypothesis in validated:
        family_counts[hypothesis["family_id"]] += 1
        for asset in hypothesis["asset_scope"]:
            asset_counts[asset] += 1
    if max(family_counts.values()) > DISCOVERY_BUDGET[
        "max_variants_per_family_per_round"
    ]:
        raise ValueError("Hypothesis manifest exceeds the family variant budget.")
    if max(asset_counts.values()) > DISCOVERY_BUDGET[
        "max_routes_per_asset_per_round"
    ]:
        raise ValueError("Hypothesis manifest exceeds the asset route budget.")

    payload = copy.deepcopy(raw)
    payload["hypotheses"] = validated
    payload["hypothesis_count"] = len(validated)
    payload["family_variant_counts"] = family_counts
    payload["asset_route_counts"] = asset_counts
    payload["automatic_strategy_selection"] = False
    payload["runtime_learning_or_mutation"] = False
    payload["hold_cash_is_valid_action"] = True
    digest = hashlib.sha256(_canonical_json_bytes(payload)).hexdigest()
    return LockedHypothesisManifest(payload=payload, sha256=digest)


def discovery_protocol_declaration():
    """Return the frozen nonexecuting architecture declaration."""

    return {
        "schema_version": SCHEMA_VERSION,
        "status": STATUS,
        "protocol_id": PROTOCOL_ID,
        "architecture_mode": HYBRID_ARCHITECTURE_MODE,
        "dataset_id": DATASET_ID,
        "dataset_manifest_sha256": DATASET_MANIFEST_SHA256,
        "partition_protocol_id": PARTITION_PROTOCOL_ID,
        "partition": "DEVELOPMENT",
        "asset_order": list(ASSET_ORDER),
        "strategy_family_order": [
            family["family_id"] for family in FAMILY_CATALOG
        ],
        "strategy_family_catalog": _catalog_payload(FAMILY_CATALOG),
        "regime_order": [regime["regime_id"] for regime in REGIME_CATALOG],
        "regime_catalog": _catalog_payload(REGIME_CATALOG),
        "discovery_budget": dict(DISCOVERY_BUDGET),
        "shared_safety_envelope": dict(SHARED_SAFETY_ENVELOPE),
        "feedback_schema": list(FEEDBACK_SCHEMA),
        "required_interest_gates": list(REQUIRED_INTEREST_GATES),
        "selection_policy": "THRESHOLD_GATED_NO_LEADERBOARD",
        "learning_mode": "OFFLINE_VERSIONED_PROPOSALS_ONLY",
        "runtime_rules_immutable": True,
        "family_specific_signal_contract_required": True,
        "family_specific_execution_contract_required": True,
        "shared_portfolio_risk_contract_required": True,
        "hold_cash_is_valid_action": True,
        "forced_asset_participation": False,
        "reference_a_closure_status": REFERENCE_A_CLOSURE_STATUS,
        "reference_a_report_sha256": REFERENCE_A_REPORT_SHA256,
        "reference_a_closed": True,
        "reference_a_rerun_authorized": False,
        "reference_a_policy_reuse_authorized": False,
        "hypothesis_manifest_registered": False,
        "strategy_components_implemented": False,
        "discovery_runner_implemented": False,
        "dataset_opened": False,
        "development_data_opened": False,
        "calibration_data_opened": False,
        "evaluation_data_opened": False,
        "development_run_authorized": False,
        "performance_evaluation_executed": False,
        "parameter_sweep_authorized": False,
        "automatic_ranking_authorized": False,
        "automatic_strategy_selection_authorized": False,
        "runtime_learning_authorized": False,
        "calibration_authorized": False,
        "evaluation_authorized": False,
        "candidate_v2_authorized": False,
        "bounded_forward_paper_authorized": False,
        "cloud_execution_authorized": False,
        "live_execution_authorized": False,
        "next_stage": "PRE_REGISTER_BOUNDED_HYBRID_DISCOVERY_ROUND_1",
    }
