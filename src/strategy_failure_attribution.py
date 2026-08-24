"""Immutable boundary for failure attribution and causal volume research."""

import argparse
from dataclasses import dataclass
import hashlib
import json
from pathlib import Path
import re

try:
    from first_strategy_candidate import BASELINE_COSTS, STRESSED_COSTS
    from research_evidence import canonical_json_bytes
    from strategy_family_screening import (
        DEVELOPMENT_MANIFEST_SHA256,
        SCREENING_ID,
        SCREENING_SPECS,
        StrategyFamilyScreeningPreregistration,
    )
    from strategy_evaluation_protocol import ExecutionCostProfile
    from volume_research import VolumeResearchConfig
except ImportError:  # package import when src is not placed directly on sys.path
    from src.first_strategy_candidate import BASELINE_COSTS, STRESSED_COSTS
    from src.research_evidence import canonical_json_bytes
    from src.strategy_family_screening import (
        DEVELOPMENT_MANIFEST_SHA256,
        SCREENING_ID,
        SCREENING_SPECS,
        StrategyFamilyScreeningPreregistration,
    )
    from src.strategy_evaluation_protocol import ExecutionCostProfile
    from src.volume_research import VolumeResearchConfig


ATTRIBUTION_SCHEMA_VERSION = 1
ATTRIBUTION_ID = "standalone-default-failure-attribution-volume-v1"
RECORDED_SCREENING_REPORT_SHA256 = (
    "9cf74deebe6a7efe9928d89b93b8ad4f7504ef70dfcf07ab0c00091a2cb9ec7f"
)
RECORDED_STRATEGY_ORDER = tuple(spec.strategy_name for spec in SCREENING_SPECS)
DIAGNOSTIC_PROFILES = (
    "zero_cost",
    "coinbase_low_volume_taker_baseline_v1",
    "coinbase_adverse_market_order_stress_v1",
)

ZERO_COSTS = ExecutionCostProfile(
    label="zero_cost",
    commission_rate=0.0,
    slippage_rate=0.0,
    spread_rate=0.0,
)


def _validated_sha256(value, name):
    if not isinstance(value, str):
        raise TypeError(f"{name} must be a string.")
    if not re.fullmatch(r"[0-9a-f]{64}", value):
        raise ValueError(
            f"{name} must be exactly 64 lowercase hexadecimal characters."
        )
    return value


def failure_attribution_configuration():
    """Return the exact explanatory views allowed in the future runner."""

    volume = VolumeResearchConfig()
    return {
        "diagnostic_profiles": [
            ZERO_COSTS.as_dict(),
            BASELINE_COSTS.as_dict(),
            STRESSED_COSTS.as_dict(),
        ],
        "diagnostic_axes": [
            "GROSS_SIGNAL_BEFORE_COSTS",
            "COST_TURNOVER_DECOMPOSITION",
            "EXPOSURE_AND_HOLDING_PERIOD",
            "DRAWDOWN_CONCENTRATION",
            "MARKET_REGIME_AT_SIGNAL_BAR",
            "VOLUME_REGIME_AT_SIGNAL_BAR",
            "ABSOLUTE_VS_BENCHMARK_RETURN",
            "WALK_FORWARD_PERSISTENCE",
        ],
        "execution_timing": "next_bar_open",
        "signal_observation": "completed_bar_close",
        "attribution_timestamp": "entry_signal_index",
        "terminal_position_policy": "force_close_at_final_close",
        "market_regime": {
            "fast_period": 10,
            "slow_period": 30,
            "atr_period": 14,
            "volatility_lookback": 30,
            "trend_threshold": 0.50,
            "high_volatility_ratio": 1.25,
            "low_volatility_ratio": 0.80,
            "signal_observation": "COMPLETED_BAR_ONLY",
            "attribution_timestamp": "entry_signal_index",
        },
        "volume": volume.as_dict(),
        "cross_asset_aggregation": "DESCRIPTIVE_PER_ASSET_THEN_MULTI_ASSET",
        "performance_ranking": "NONE",
    }


def volume_policy():
    return {
        "mandatory_for_future_alpha_hypothesis": True,
        "allowed_roles": [
            "ENTRY_CONFIRMATION",
            "BREAKOUT_CONFIRMATION",
            "LOW_LIQUIDITY_AVOIDANCE",
            "REGIME_FEATURE",
            "RISK_SIZING_INPUT",
        ],
        "required_evidence": [
            "RELATIVE_VOLUME",
            "RELATIVE_DOLLAR_VOLUME",
            "ON_BALANCE_VOLUME",
            "VOLUME_REGIME_CONDITIONED_RESULTS",
        ],
        "raw_cross_asset_volume_comparison": "PROHIBITED",
        "future_data_access": "PROHIBITED",
        "standalone_edge_claim": False,
        "live_liquidity_substitute": False,
        "live_extension_requires": [
            "SPREAD",
            "ORDER_BOOK_DEPTH",
            "MARKET_IMPACT",
        ],
    }


def interpretation_policy():
    return {
        "purpose": "EXPLAIN_RECORDED_FAILURE_NOT_SELECT_WINNER",
        "ranking": "PROHIBITED",
        "winner_selection": "PROHIBITED",
        "formal_validation_claim": "PROHIBITED",
        "result_driven_parameter_changes": "PROHIBITED",
        "parameter_leaderboard": "PROHIBITED",
        "future_hypothesis_may_use_inspected_evidence": True,
        "future_candidate_requires_new_preregistration": True,
        "future_candidate_requires_genuinely_unseen_data": True,
        "recorded_screen_out_scope": (
            "STANDALONE_FROZEN_CONFIGURATION_NOT_INDICATOR_FAMILY"
        ),
    }


def _safety_boundary():
    return {
        "failure_attribution_executed": False,
        "performance_replay_executed": False,
        "automatic_ranking_generated": False,
        "automatic_strategy_selection": False,
        "parameter_sweep_authorized": False,
        "strategy_combination_authorized": False,
        "candidate_v2_authorized": False,
        "optimization_authorized": False,
        "bounded_forward_paper_review_eligible": False,
        "bounded_forward_paper_authorized": False,
        "live_execution_authorized": False,
    }


def load_recorded_screening_report(
    report_path,
    expected_sha256=RECORDED_SCREENING_REPORT_SHA256,
):
    """Load only the exact canonical, safely closed screening evidence."""

    expected_sha256 = _validated_sha256(
        expected_sha256, "Required screening-report SHA-256"
    )
    path = Path(report_path)
    if not path.is_file():
        raise FileNotFoundError(f"Recorded screening report does not exist: {path}")
    report_bytes = path.read_bytes()
    digest = hashlib.sha256(report_bytes).hexdigest()
    if digest != expected_sha256:
        raise ValueError(
            "Recorded screening report does not match the frozen SHA-256."
        )

    checksum_path = path.with_name("strategy_family_screening_report.sha256")
    if not checksum_path.is_file():
        raise FileNotFoundError("Recorded screening checksum sidecar is missing.")
    expected_sidecar = f"{digest}  {path.name}\n".encode("ascii")
    if checksum_path.read_bytes() != expected_sidecar:
        raise ValueError("Recorded screening checksum sidecar is invalid.")

    try:
        payload = json.loads(report_bytes)
    except json.JSONDecodeError as exc:
        raise ValueError("Recorded screening report is not valid JSON.") from exc
    if canonical_json_bytes(payload) != report_bytes:
        raise ValueError("Recorded screening report is not canonical JSON.")

    if (
        payload.get("schema_version") != 1
        or payload.get("status") != "STRATEGY_FAMILY_SCREENING_COMPLETED"
        or payload.get("screening_id") != SCREENING_ID
        or payload.get("strategy_order") != list(RECORDED_STRATEGY_ORDER)
        or payload.get("strategy_count") != len(RECORDED_STRATEGY_ORDER)
        or payload.get("dataset_role") != "INSPECTED_DEVELOPMENT_ONLY"
        or payload.get("development_data_only") is not True
    ):
        raise ValueError("Recorded screening identity or scope is invalid.")

    required_true = (
        "screening_executed",
        "performance_evaluation_executed",
        "development_screening_executed",
    )
    if any(payload.get(flag) is not True for flag in required_true):
        raise ValueError("Recorded screening execution evidence is incomplete.")
    required_false = (
        "automatic_ranking_generated",
        "automatic_strategy_selection",
        "parameter_sweep_executed",
        "strategy_combination_executed",
        "formal_candidate_evaluation",
        "candidate_v2_authorized",
        "optimization_authorized",
        "bounded_forward_paper_review_eligible",
        "bounded_forward_paper_authorized",
        "live_execution_authorized",
    )
    if any(payload.get(flag) is not False for flag in required_false):
        raise ValueError("Recorded screening authorization boundary is invalid.")
    if payload.get("selected_strategy") is not None:
        raise ValueError("Recorded screening unexpectedly selected a strategy.")

    comparison = payload.get("comparison")
    if not isinstance(comparison, dict):
        raise ValueError("Recorded screening comparison is missing.")
    if (
        comparison.get("strategy_order") != list(RECORDED_STRATEGY_ORDER)
        or comparison.get("selection_policy")
        != "DESCRIPTIVE_MULTIPLE_COMPARISON_GUARD"
        or comparison.get("automatic_ranking_generated") is not False
        or comparison.get("automatic_strategy_selection") is not False
        or comparison.get("mechanisms_retaining_interest") != []
        or comparison.get("outcome_counts")
        != {
            "INCONCLUSIVE": 0,
            "MECHANISM_RETAINS_INTEREST": 0,
            "SCREEN_OUT": len(RECORDED_STRATEGY_ORDER),
        }
    ):
        raise ValueError("Recorded screening closed comparison is invalid.")
    comparison_strategies = comparison.get("strategies")
    evidence = payload.get("strategy_evidence")
    if (
        not isinstance(comparison_strategies, dict)
        or tuple(comparison_strategies) != RECORDED_STRATEGY_ORDER
        or not isinstance(evidence, dict)
        or tuple(evidence) != RECORDED_STRATEGY_ORDER
    ):
        raise ValueError("Recorded screening strategy scope is invalid.")
    for name in RECORDED_STRATEGY_ORDER:
        try:
            comparison_outcome = comparison_strategies[name]["outcome"]
            evidence_outcome = evidence[name]["screening_review"]["outcome"]
        except (KeyError, TypeError) as exc:
            raise ValueError(
                "Recorded screening strategy outcome evidence is incomplete."
            ) from exc
        if comparison_outcome != "SCREEN_OUT" or evidence_outcome != "SCREEN_OUT":
            raise ValueError("Recorded screening strategy outcome is not closed.")
    return payload, digest


@dataclass(frozen=True)
class LockedFailureAttribution:
    assets: dict
    strategy_engines: dict
    contract: object
    screening_configuration: object
    manifest_sha256: str
    screening_report: dict
    screening_report_sha256: str
    attribution_configuration: dict


class FailureAttributionPreregistration:
    """Freeze diagnostics and volume semantics without replaying performance."""

    def __init__(
        self,
        screening_preregistration=None,
        required_manifest_sha256=DEVELOPMENT_MANIFEST_SHA256,
        required_screening_report_sha256=RECORDED_SCREENING_REPORT_SHA256,
    ):
        self.screening_preregistration = (
            screening_preregistration
            if screening_preregistration is not None
            else StrategyFamilyScreeningPreregistration()
        )
        self.required_manifest_sha256 = _validated_sha256(
            required_manifest_sha256, "Required manifest SHA-256"
        )
        self.required_screening_report_sha256 = _validated_sha256(
            required_screening_report_sha256,
            "Required screening-report SHA-256",
        )

    def declaration(self):
        return {
            "schema_version": ATTRIBUTION_SCHEMA_VERSION,
            "status": "FAILURE_ATTRIBUTION_EVIDENCE_LOCK_PENDING",
            "attribution_id": ATTRIBUTION_ID,
            "purpose": "CONTROLLED_ALPHA_DISCOVERY_FAILURE_ATTRIBUTION",
            "dataset_role": "INSPECTED_DEVELOPMENT_ONLY",
            "timeframe": "6h",
            "assets": ["BTC-USD", "ETH-USD"],
            "strategy_order": list(RECORDED_STRATEGY_ORDER),
            "required_manifest_sha256": self.required_manifest_sha256,
            "required_screening_report_sha256": (
                self.required_screening_report_sha256
            ),
            "configuration": failure_attribution_configuration(),
            "volume_analysis_mandatory": True,
            "volume_policy": volume_policy(),
            "interpretation_policy": interpretation_policy(),
            "attribution_authorized_before_evidence_lock": False,
            "separate_attribution_runner_review_required": True,
            **_safety_boundary(),
        }

    def lock(self, manifest_path, screening_report_path):
        locked_screening = self.screening_preregistration.lock(manifest_path)
        if locked_screening.manifest_sha256 != self.required_manifest_sha256:
            raise ValueError(
                "Locked development manifest does not match the attribution manifest."
            )
        payload, digest = load_recorded_screening_report(
            screening_report_path,
            expected_sha256=self.required_screening_report_sha256,
        )
        if payload.get("manifest_sha256") != locked_screening.manifest_sha256:
            raise ValueError(
                "Recorded screening manifest does not match the locked dataset manifest."
            )
        if tuple(locked_screening.strategy_engines) != RECORDED_STRATEGY_ORDER:
            raise ValueError("Locked strategy scope does not match recorded screening.")
        if tuple(sorted(locked_screening.assets)) != ("BTC-USD", "ETH-USD"):
            raise ValueError("Locked asset scope does not match attribution scope.")
        return LockedFailureAttribution(
            assets=locked_screening.assets,
            strategy_engines=locked_screening.strategy_engines,
            contract=locked_screening.contract,
            screening_configuration=locked_screening.configuration,
            manifest_sha256=locked_screening.manifest_sha256,
            screening_report=payload,
            screening_report_sha256=digest,
            attribution_configuration=failure_attribution_configuration(),
        )


def main(argv=None):
    parser = argparse.ArgumentParser(
        description=(
            "Declare or evidence-lock Failure Attribution and Volume Research "
            "Protocol v1 without replaying performance."
        )
    )
    parser.add_argument(
        "--manifest",
        help="Exact frozen native BTC/ETH six-hour development manifest.",
    )
    parser.add_argument(
        "--screening-report",
        help="Exact recorded Strategy Family Screening v1 report.",
    )
    args = parser.parse_args(argv)
    if bool(args.manifest) != bool(args.screening_report):
        parser.error("--manifest and --screening-report must be supplied together.")

    preregistration = FailureAttributionPreregistration()
    if args.manifest:
        locked = preregistration.lock(args.manifest, args.screening_report)
        result = {
            "schema_version": ATTRIBUTION_SCHEMA_VERSION,
            "status": "FAILURE_ATTRIBUTION_EVIDENCE_LOCKED",
            "attribution_id": ATTRIBUTION_ID,
            "manifest_sha256": locked.manifest_sha256,
            "screening_report_sha256": locked.screening_report_sha256,
            "dataset_role": "INSPECTED_DEVELOPMENT_ONLY",
            "timeframe": locked.contract.timeframe,
            "assets": list(locked.contract.products),
            "asset_rows": {
                name: len(frame) for name, frame in sorted(locked.assets.items())
            },
            "strategy_order": list(locked.strategy_engines),
            "configuration": locked.attribution_configuration,
            "volume_analysis_mandatory": True,
            "volume_policy": volume_policy(),
            "interpretation_policy": interpretation_policy(),
            "separate_attribution_runner_review_required": True,
            **_safety_boundary(),
        }
    else:
        result = preregistration.declaration()
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
