"""Immutable Alpha Development Protocol v2 declaration and evidence lock."""

import argparse
from dataclasses import dataclass
import hashlib
import json
from pathlib import Path
import re

try:
    from alpha_development_strategy import (
        ALPHA_DEVELOPMENT_VARIANTS,
        alpha_development_strategies,
    )
    from coinbase_research_dataset import (
        FIRST_CANDIDATE_DATASET_CONTRACT,
        CoinbaseResearchDatasetContract,
        CoinbaseResearchDatasetLock,
    )
    from research_evidence import canonical_json_bytes
    from strategy_engine import StrategyEngine
    from strategy_failure_attribution import (
        ATTRIBUTION_ID,
        RECORDED_SCREENING_REPORT_SHA256,
        RECORDED_STRATEGY_ORDER,
    )
    from strategy_family_screening import DEVELOPMENT_MANIFEST_SHA256
    from strategy_library import StrategyLibrary
    from venue_execution_research import venue_execution_policy
except ImportError:  # package import when src is not placed directly on sys.path
    from src.alpha_development_strategy import (
        ALPHA_DEVELOPMENT_VARIANTS,
        alpha_development_strategies,
    )
    from src.coinbase_research_dataset import (
        FIRST_CANDIDATE_DATASET_CONTRACT,
        CoinbaseResearchDatasetContract,
        CoinbaseResearchDatasetLock,
    )
    from src.research_evidence import canonical_json_bytes
    from src.strategy_engine import StrategyEngine
    from src.strategy_failure_attribution import (
        ATTRIBUTION_ID,
        RECORDED_SCREENING_REPORT_SHA256,
        RECORDED_STRATEGY_ORDER,
    )
    from src.strategy_family_screening import DEVELOPMENT_MANIFEST_SHA256
    from src.strategy_library import StrategyLibrary
    from src.venue_execution_research import venue_execution_policy


ALPHA_DEVELOPMENT_SCHEMA_VERSION = 2
ALPHA_DEVELOPMENT_ID = "adx-regime-volume-alpha-development-v2"
RECORDED_ATTRIBUTION_REPORT_SHA256 = (
    "e4193bff907a2121701e7ddc1d740894641c7bf427c9501fd4ecd4392a1f81f4"
)
VARIANT_ORDER = tuple(variant.variant_id for variant in ALPHA_DEVELOPMENT_VARIANTS)


def _validated_sha256(value, name):
    if not isinstance(value, str):
        raise TypeError(f"{name} must be a string.")
    if not re.fullmatch(r"[0-9a-f]{64}", value):
        raise ValueError(
            f"{name} must be exactly 64 lowercase hexadecimal characters."
        )
    return value


def _required_boolean(payload, name, expected):
    if payload.get(name) is not expected:
        raise ValueError(f"Recorded attribution {name} is invalid.")


def _conditioned_summary(payload, profile, asset, axis, label):
    try:
        attribution = payload["strategy_evidence"]["adx"]["profiles"][profile][
            "attribution"
        ]["assets"][asset]
        if axis == "volume":
            summary = attribution["volume"]["volume_regimes"][label]
        elif axis == "market_regime":
            summary = attribution["market_regime"]["regimes"][label]
        elif axis == "obv":
            summary = attribution["volume"]["obv_directions"][label]
        else:  # pragma: no cover - private caller freezes the axis set
            raise AssertionError("Unknown attribution axis.")
        trade_count = int(summary["trade_count"])
        net_profit_loss = float(summary["net_profit_loss"])
    except (KeyError, TypeError, ValueError) as exc:
        raise ValueError("Recorded ADX conditioned evidence is incomplete.") from exc
    return trade_count, net_profit_loss


def _validate_attribution_basis(payload):
    """Confirm the exact qualitative evidence used to form this hypothesis."""

    for asset, trades in (("BTC-USD", 25), ("ETH-USD", 21)):
        observed_trades, pnl = _conditioned_summary(
            payload, "baseline", asset, "volume", "HIGH"
        )
        if observed_trades != trades or pnl <= 0.0:
            raise ValueError("Recorded ADX high-volume basis is invalid.")

    for asset, trades in (("BTC-USD", 14), ("ETH-USD", 19)):
        observed_trades, pnl = _conditioned_summary(
            payload, "baseline", asset, "market_regime", "BULLISH_NORMAL"
        )
        if observed_trades != trades or pnl <= 0.0:
            raise ValueError("Recorded ADX bullish-normal basis is invalid.")

    btc_falling = _conditioned_summary(
        payload, "baseline", "BTC-USD", "obv", "FALLING"
    )[1]
    eth_falling = _conditioned_summary(
        payload, "baseline", "ETH-USD", "obv", "FALLING"
    )[1]
    btc_rising = _conditioned_summary(
        payload, "baseline", "BTC-USD", "obv", "RISING"
    )[1]
    eth_rising = _conditioned_summary(
        payload, "baseline", "ETH-USD", "obv", "RISING"
    )[1]
    if not (
        btc_falling < 0.0
        and eth_falling < 0.0
        and btc_rising < 0.0
        and eth_rising > 0.0
    ):
        raise ValueError("Recorded ADX OBV basis is invalid.")


def load_recorded_attribution_report(
    report_path,
    expected_sha256=RECORDED_ATTRIBUTION_REPORT_SHA256,
):
    """Load only the exact canonical, safely closed attribution evidence."""

    expected_sha256 = _validated_sha256(
        expected_sha256, "Required attribution-report SHA-256"
    )
    path = Path(report_path)
    if not path.is_file():
        raise FileNotFoundError(f"Recorded attribution report does not exist: {path}")
    report_bytes = path.read_bytes()
    digest = hashlib.sha256(report_bytes).hexdigest()
    if digest != expected_sha256:
        raise ValueError("Recorded attribution report does not match frozen SHA-256.")
    checksum_path = path.with_name("failure_attribution_report.sha256")
    if not checksum_path.is_file():
        raise FileNotFoundError("Recorded attribution checksum sidecar is missing.")
    expected_sidecar = f"{digest}  {path.name}\n".encode("ascii")
    if checksum_path.read_bytes() != expected_sidecar:
        raise ValueError("Recorded attribution checksum sidecar is invalid.")
    try:
        payload = json.loads(report_bytes)
    except json.JSONDecodeError as exc:
        raise ValueError("Recorded attribution report is not valid JSON.") from exc
    if canonical_json_bytes(payload) != report_bytes:
        raise ValueError("Recorded attribution report is not canonical JSON.")

    if (
        payload.get("schema_version") != 1
        or payload.get("status") != "FAILURE_ATTRIBUTION_COMPLETED"
        or payload.get("attribution_id") != ATTRIBUTION_ID
        or payload.get("manifest_sha256") != DEVELOPMENT_MANIFEST_SHA256
        or payload.get("screening_report_sha256")
        != RECORDED_SCREENING_REPORT_SHA256
        or payload.get("dataset_role") != "INSPECTED_DEVELOPMENT_ONLY"
        or payload.get("strategy_count") != 8
        or payload.get("strategy_order") != list(RECORDED_STRATEGY_ORDER)
        or payload.get("diagnostic_multi_asset_replays") != 24
        or payload.get("profile_order") != ["zero_cost", "baseline", "stress"]
    ):
        raise ValueError("Recorded attribution identity or scope is invalid.")

    for name in (
        "failure_attribution_executed",
        "performance_replay_executed",
        "volume_analysis_executed",
        "market_regime_analysis_executed",
    ):
        _required_boolean(payload, name, True)
    for name in (
        "automatic_ranking_generated",
        "automatic_strategy_selection",
        "parameter_sweep_executed",
        "strategy_combination_executed",
        "formal_candidate_evaluation",
        "new_alpha_hypothesis_generated",
        "candidate_v2_authorized",
        "optimization_authorized",
        "bounded_forward_paper_review_eligible",
        "bounded_forward_paper_authorized",
        "live_execution_authorized",
    ):
        _required_boolean(payload, name, False)
    if payload.get("selected_strategy") is not None:
        raise ValueError("Recorded attribution unexpectedly selected a strategy.")
    _validate_attribution_basis(payload)
    return payload, digest


def alpha_development_strategy_engines():
    engines = {}
    for strategy in alpha_development_strategies():
        library = StrategyLibrary()
        library.register(strategy)
        engines[strategy.variant.variant_id] = StrategyEngine(library, strategy.name)
    if tuple(engines) != VARIANT_ORDER:
        raise ValueError("Alpha-development variant order changed.")
    return engines


def protective_exit_boundary():
    return {
        "status": "REQUIRED_BEFORE_PERFORMANCE_RUNNER",
        "current_backtester_limitation": (
            "RISK_ENGINE_SIZES_AND_RECORDS_LEVELS_BUT_DOES_NOT_EXECUTE_"
            "INTRABAR_PROTECTIVE_EXITS"
        ),
        "entry_execution": "FOLLOWING_BAR_OPEN",
        "risk_distance_source": "2_X_SIGNAL_BAR_ATR_14",
        "stop_price": "EXECUTION_OPEN_MINUS_SIGNAL_BAR_RISK_DISTANCE",
        "target_price": "EXECUTION_OPEN_PLUS_3_X_RISK_DISTANCE",
        "gap_through_stop": "EXIT_AT_FIRST_AVAILABLE_BAR_OPEN",
        "stop_and_target_same_bar": "CONSERVATIVE_STOP_FIRST",
        "protective_exit_costs_applied": True,
        "partial_fill_model": "NOT_REQUIRED_FOR_TAKER_ONLY_V2_RUNNER",
        "implementation_verified": False,
        "performance_runner_authorized": False,
    }


def alpha_development_configuration():
    variants = [variant.as_dict() for variant in ALPHA_DEVELOPMENT_VARIANTS]
    return {
        "variant_order": list(VARIANT_ORDER),
        "variants": variants,
        "comparison": {
            "type": "FIXED_CAUSAL_ABLATION_CHAIN",
            "ranking": "PROHIBITED",
            "winner_selection": "PROHIBITED",
            "parameter_sweep": "PROHIBITED",
            "marginal_profit_addition": "PROHIBITED",
            "joint_intersections_must_be_evaluated_directly": True,
        },
        "risk": {
            "risk_per_trade_fraction": 0.005,
            "maximum_position_fraction": 0.50,
            "maximum_portfolio_drawdown_fraction": 0.20,
            "maximum_daily_new_risk_fraction": 0.02,
            "maximum_weekly_new_risk_fraction": 0.05,
            "minimum_reward_risk_ratio": 3.0,
            "leverage": "NONE",
            "shorting": False,
        },
        "turnover_cost_budget": {
            "annual_total_executed_notional_multiple_maximum": 24.0,
            "annual_baseline_cost_fraction_of_initial_capital_maximum": 0.20,
            "budget_breach_outcome": "SCREEN_OUT",
            "cost_survival_required_on_both_assets": True,
        },
        "temporal_development": {
            "dataset_role": "INSPECTED_DEVELOPMENT_ONLY",
            "walk_forward_train_bars": 2880,
            "walk_forward_test_bars": 720,
            "walk_forward_step_bars": 720,
            "minimum_windows_per_asset": 5,
            "minimum_development_trades_per_asset": 20,
            "formal_future_candidate_minimum_unseen_trades_per_asset": 30,
            "calibration_in_this_protocol": False,
            "future_calibration_requires_separate_preregistration": True,
            "future_final_validation_requires_genuinely_unseen_data": True,
        },
        "venue_execution": venue_execution_policy(),
        "protective_exit": protective_exit_boundary(),
    }


def alpha_development_interpretation_policy():
    return {
        "purpose": "TEST_JOINT_CAUSAL_MECHANISM_NOT_FIND_HINDSIGHT_WINNER",
        "allowed_outcomes": [
            "MECHANISM_RETAINS_DEVELOPMENT_INTEREST",
            "SCREEN_OUT",
            "INCONCLUSIVE",
        ],
        "development_interest_is_formal_validation": False,
        "development_interest_is_candidate_v2": False,
        "no_variant_may_be_promoted_automatically": True,
        "new_candidate_requires_new_immutable_identity": True,
        "new_candidate_requires_genuinely_unseen_validation": True,
    }


def _safety_boundary():
    return {
        "joint_performance_evaluation_executed": False,
        "protective_exit_engine_implemented": False,
        "parameter_calibration_executed": False,
        "automatic_ranking_generated": False,
        "automatic_strategy_selection": False,
        "candidate_v2_authorized": False,
        "optimization_authorized": False,
        "bounded_forward_paper_review_eligible": False,
        "bounded_forward_paper_authorized": False,
        "live_execution_authorized": False,
    }


@dataclass(frozen=True)
class LockedAlphaDevelopment:
    contract: CoinbaseResearchDatasetContract
    assets: dict
    manifest_sha256: str
    attribution_report: dict
    attribution_report_sha256: str
    strategy_engines: dict
    configuration: dict


class AlphaDevelopmentPreregistration:
    """Freeze v2 hypotheses without evaluating joint performance."""

    def __init__(
        self,
        contract=FIRST_CANDIDATE_DATASET_CONTRACT,
        required_manifest_sha256=DEVELOPMENT_MANIFEST_SHA256,
        required_attribution_report_sha256=RECORDED_ATTRIBUTION_REPORT_SHA256,
        dataset_lock=None,
        attribution_report_loader=load_recorded_attribution_report,
    ):
        if not isinstance(contract, CoinbaseResearchDatasetContract):
            raise TypeError("Contract must be a CoinbaseResearchDatasetContract.")
        if not callable(attribution_report_loader):
            raise TypeError("Attribution report loader must be callable.")
        self.contract = contract
        self.required_manifest_sha256 = _validated_sha256(
            required_manifest_sha256, "Required manifest SHA-256"
        )
        self.required_attribution_report_sha256 = _validated_sha256(
            required_attribution_report_sha256,
            "Required attribution-report SHA-256",
        )
        self.dataset_lock = dataset_lock or CoinbaseResearchDatasetLock(contract)
        self.attribution_report_loader = attribution_report_loader

    def declaration(self):
        return {
            "schema_version": ALPHA_DEVELOPMENT_SCHEMA_VERSION,
            "status": "ALPHA_DEVELOPMENT_EVIDENCE_LOCK_PENDING",
            "alpha_development_id": ALPHA_DEVELOPMENT_ID,
            "purpose": "BOUNDED_JOINT_CAUSAL_ALPHA_DEVELOPMENT",
            "dataset_role": "INSPECTED_DEVELOPMENT_ONLY",
            "timeframe": self.contract.timeframe,
            "assets": list(self.contract.products),
            "required_manifest_sha256": self.required_manifest_sha256,
            "required_attribution_report_sha256": (
                self.required_attribution_report_sha256
            ),
            "variant_order": list(VARIANT_ORDER),
            "configuration": alpha_development_configuration(),
            "interpretation_policy": alpha_development_interpretation_policy(),
            "joint_evaluation_authorized_before_evidence_lock": False,
            "separate_protective_exit_review_required": True,
            "separate_performance_runner_review_required": True,
            **_safety_boundary(),
        }

    def lock(self, manifest_path, attribution_report_path):
        dataset = self.dataset_lock.lock(manifest_path)
        if dataset.manifest_sha256 != self.required_manifest_sha256:
            raise ValueError("Dataset does not match the frozen development manifest.")
        payload, digest = self.attribution_report_loader(
            attribution_report_path,
            expected_sha256=self.required_attribution_report_sha256,
        )
        if payload.get("manifest_sha256") != dataset.manifest_sha256:
            raise ValueError("Attribution evidence and dataset manifest do not match.")
        if tuple(sorted(dataset.assets)) != tuple(self.contract.products):
            raise ValueError("Locked asset scope does not match alpha development.")
        return LockedAlphaDevelopment(
            contract=self.contract,
            assets=dataset.assets,
            manifest_sha256=dataset.manifest_sha256,
            attribution_report=payload,
            attribution_report_sha256=digest,
            strategy_engines=alpha_development_strategy_engines(),
            configuration=alpha_development_configuration(),
        )


def main(argv=None):
    parser = argparse.ArgumentParser(
        description=(
            "Declare or evidence-lock Alpha Development Protocol v2 without "
            "evaluating joint performance."
        )
    )
    parser.add_argument("--manifest", help="Exact frozen six-hour manifest.")
    parser.add_argument(
        "--attribution-report", help="Exact closed Failure Attribution v1 report."
    )
    args = parser.parse_args(argv)
    if bool(args.manifest) != bool(args.attribution_report):
        parser.error("--manifest and --attribution-report must be supplied together.")

    preregistration = AlphaDevelopmentPreregistration()
    if args.manifest:
        locked = preregistration.lock(args.manifest, args.attribution_report)
        result = {
            "schema_version": ALPHA_DEVELOPMENT_SCHEMA_VERSION,
            "status": "ALPHA_DEVELOPMENT_EVIDENCE_LOCKED",
            "alpha_development_id": ALPHA_DEVELOPMENT_ID,
            "manifest_sha256": locked.manifest_sha256,
            "attribution_report_sha256": locked.attribution_report_sha256,
            "dataset_role": "INSPECTED_DEVELOPMENT_ONLY",
            "timeframe": locked.contract.timeframe,
            "assets": list(locked.contract.products),
            "asset_rows": {
                name: len(frame) for name, frame in sorted(locked.assets.items())
            },
            "variant_order": list(locked.strategy_engines),
            "configuration": locked.configuration,
            "interpretation_policy": alpha_development_interpretation_policy(),
            "separate_protective_exit_review_required": True,
            "separate_performance_runner_review_required": True,
            **_safety_boundary(),
        }
    else:
        result = preregistration.declaration()
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
