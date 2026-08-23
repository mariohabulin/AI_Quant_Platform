"""Immutable research-only boundary for default strategy-family screening."""

import argparse
import hashlib
import json
import re
from dataclasses import dataclass

try:
    from coinbase_research_dataset import (
        FIRST_CANDIDATE_DATASET_CONTRACT,
        CoinbaseResearchDatasetContract,
        CoinbaseResearchDatasetLock,
    )
    from first_strategy_candidate import first_candidate_configuration
    from research_evidence import canonical_json_bytes
    from strategy_engine import StrategyEngine
    from strategy_library import StrategyLibrary
    from strategy_research_inventory import STRATEGY_SPECS
except ImportError:  # package import when src is not placed directly on sys.path
    from src.coinbase_research_dataset import (
        FIRST_CANDIDATE_DATASET_CONTRACT,
        CoinbaseResearchDatasetContract,
        CoinbaseResearchDatasetLock,
    )
    from src.first_strategy_candidate import first_candidate_configuration
    from src.research_evidence import canonical_json_bytes
    from src.strategy_engine import StrategyEngine
    from src.strategy_library import StrategyLibrary
    from src.strategy_research_inventory import STRATEGY_SPECS


STRATEGY_FAMILY_SCREENING_SCHEMA_VERSION = 1
SCREENING_ID = "default-strategy-families-btc-eth-native-6h-development-v1"
DEVELOPMENT_MANIFEST_SHA256 = (
    "6506dd2700b983a134a132890ef4c4ae6e84c0918ba65a5abff6ab2c204c4e7f"
)
SCREENING_OUTCOMES = (
    "MECHANISM_RETAINS_INTEREST",
    "SCREEN_OUT",
    "INCONCLUSIVE",
)
SCREENING_SPECS = tuple(
    spec
    for spec in STRATEGY_SPECS
    if spec.research_status == "UNEVALUATED_RESEARCH_COMPONENT"
)

SCREENING_QUESTIONS = {
    "adx": (
        "Can unmodified ADX trend-strength gating reduce churn and retain "
        "cross-asset evidence after baseline and stressed costs?"
    ),
    "atr": (
        "Can an unmodified ATR volatility breakout trade sparsely enough to "
        "survive costs while bounding drawdown across both assets?"
    ),
    "bollinger": (
        "Can unmodified Bollinger mean reversion persist across both assets "
        "without regime-dependent drawdown failure?"
    ),
    "donchian": (
        "Can an unmodified Donchian breakout retain persistent cross-asset "
        "excess evidence after baseline and stressed costs?"
    ),
    "macd": (
        "Can an unmodified MACD crossover improve persistence and cost "
        "survival relative to the closed EMA mechanism?"
    ),
    "rsi": (
        "Can unmodified RSI mean reversion retain positive absolute and "
        "excess evidence while bounding drawdown across both assets?"
    ),
    "stochastic": (
        "Can an unmodified Stochastic extreme-zone crossover avoid excessive "
        "turnover and retain stressed cross-asset evidence?"
    ),
    "supertrend": (
        "Can an unmodified volatility-adjusted Supertrend mechanism reduce "
        "whipsaw and retain stressed cross-asset persistence?"
    ),
}


def _validated_sha256(value):
    if not isinstance(value, str):
        raise TypeError("Required manifest SHA-256 must be a string.")
    if not re.fullmatch(r"[0-9a-f]{64}", value):
        raise ValueError(
            "Required manifest SHA-256 must be exactly 64 lowercase hex characters."
        )
    return value


def screening_configuration():
    """Reuse the exact candidate-v1 splits, seed, timing, gates and costs."""

    return first_candidate_configuration()


def _strategy_payload(spec):
    identity = {
        "strategy_name": spec.strategy_name,
        "family": spec.family,
        "mechanism": spec.mechanism,
        "default_parameters": dict(spec.default_parameters),
    }
    return {
        **identity,
        "screening_question": SCREENING_QUESTIONS[spec.strategy_name],
        "configuration_fingerprint": hashlib.sha256(
            canonical_json_bytes(identity)
        ).hexdigest(),
        "parameter_variants": 1,
        "parameter_sweep_authorized": False,
        "combination_authorized": False,
        "formal_candidate": False,
    }


def screening_strategy_engines():
    """Construct one explicit default-only Strategy Engine per frozen spec."""

    engines = {}
    for spec in SCREENING_SPECS:
        strategy = spec.factory(**dict(spec.default_parameters))
        if strategy.name != spec.strategy_name:
            raise ValueError("Screening strategy identity does not match inventory.")
        library = StrategyLibrary()
        library.register(strategy)
        engines[spec.strategy_name] = StrategyEngine(library, spec.strategy_name)
    return engines


def screening_interpretation_policy():
    return {
        "outcomes": list(SCREENING_OUTCOMES),
        "comparison_mode": "DESCRIPTIVE_MULTIPLE_COMPARISON_GUARD",
        "ranking": "PROHIBITED",
        "winner_selection": "PROHIBITED",
        "formal_validation_claim": "PROHIBITED",
        "screen_out_rule": (
            "SCREEN_OUT_IF_BASELINE_OR_STRESS_MULTI_ASSET_CLASSIFICATION_REJECTED"
        ),
        "retains_interest_rule": (
            "RETAIN_ONLY_IF_BASELINE_AND_STRESS_MULTI_ASSET_VALIDATED_AND_"
            "FROZEN_VOLUME_DRAWDOWN_GATES_PASS"
        ),
        "otherwise": "INCONCLUSIVE",
        "ties": "NO_TIEBREAK_OR_RANKING",
        "future_candidate_requires_new_preregistration": True,
        "future_candidate_requires_genuinely_unseen_data": True,
        "inspected_results_may_only_form_a_new_hypothesis": True,
    }


def _safety_boundary():
    return {
        "screening_executed": False,
        "performance_evaluation_executed": False,
        "automatic_ranking_authorized": False,
        "parameter_sweep_authorized": False,
        "strategy_combination_authorized": False,
        "candidate_v2_authorized": False,
        "optimization_authorized": False,
        "bounded_forward_paper_review_eligible": False,
        "bounded_forward_paper_authorized": False,
        "live_execution_authorized": False,
    }


@dataclass(frozen=True)
class LockedStrategyFamilyScreening:
    contract: CoinbaseResearchDatasetContract
    configuration: object
    strategy_engines: dict
    assets: dict
    manifest_sha256: str


class StrategyFamilyScreeningPreregistration:
    """Freeze a development screen without executing performance research."""

    def __init__(
        self,
        contract=FIRST_CANDIDATE_DATASET_CONTRACT,
        required_manifest_sha256=DEVELOPMENT_MANIFEST_SHA256,
    ):
        if not isinstance(contract, CoinbaseResearchDatasetContract):
            raise TypeError("Contract must be a CoinbaseResearchDatasetContract.")
        self.contract = contract
        self.required_manifest_sha256 = _validated_sha256(
            required_manifest_sha256
        )
        self.dataset_lock = CoinbaseResearchDatasetLock(contract)

    def declaration(self):
        configuration = screening_configuration()
        return {
            "schema_version": STRATEGY_FAMILY_SCREENING_SCHEMA_VERSION,
            "status": "STRATEGY_FAMILY_SCREENING_DATASET_LOCK_PENDING",
            "screening_id": SCREENING_ID,
            "purpose": "DEFAULT_ONLY_STRATEGY_FAMILY_DEVELOPMENT_SCREEN",
            "timeframe": self.contract.timeframe,
            "assets": list(self.contract.products),
            "dataset_contract": self.contract.as_dict(),
            "required_manifest_sha256": self.required_manifest_sha256,
            "dataset_role": "INSPECTED_DEVELOPMENT_ONLY",
            "resolution_role": "FIXED_RESEARCH_WORKING_RESOLUTION_NOT_WINNER",
            "resolution_rationale": {
                "one_hour": "RECORDED_TURNOVER_AND_COST_FAILURE",
                "six_hour": "BALANCED_DEVELOPMENT_EVIDENCE_DENSITY",
                "one_day": "RECORDED_LOW_TRADE_DENSITY",
                "selection_claim": False,
            },
            "strategy_count": len(SCREENING_SPECS),
            "strategy_order": [spec.strategy_name for spec in SCREENING_SPECS],
            "strategies": [_strategy_payload(spec) for spec in SCREENING_SPECS],
            "configuration": configuration.as_dict(),
            "interpretation_policy": screening_interpretation_policy(),
            "screening_authorized_before_dataset_lock": False,
            "separate_screening_runner_review_required": True,
            **_safety_boundary(),
        }

    def lock(self, manifest_path):
        dataset = self.dataset_lock.lock(manifest_path)
        if dataset.manifest_sha256 != self.required_manifest_sha256:
            raise ValueError(
                "Dataset does not match the frozen screening manifest SHA-256."
            )
        return LockedStrategyFamilyScreening(
            contract=self.contract,
            configuration=screening_configuration(),
            strategy_engines=screening_strategy_engines(),
            assets=dataset.assets,
            manifest_sha256=dataset.manifest_sha256,
        )


def main(argv=None):
    parser = argparse.ArgumentParser(
        description=(
            "Declare or data-lock Strategy Family Screening Protocol v1 "
            "without evaluating performance."
        )
    )
    parser.add_argument(
        "--manifest",
        help="Validate the exact frozen 6h development dataset without screening.",
    )
    args = parser.parse_args(argv)
    preregistration = StrategyFamilyScreeningPreregistration()
    if args.manifest:
        locked = preregistration.lock(args.manifest)
        result = {
            "schema_version": STRATEGY_FAMILY_SCREENING_SCHEMA_VERSION,
            "status": "STRATEGY_FAMILY_SCREENING_LOCKED",
            "screening_id": SCREENING_ID,
            "manifest_sha256": locked.manifest_sha256,
            "data_version": (
                f"{locked.contract.dataset_id};"
                f"manifest_sha256={locked.manifest_sha256}"
            ),
            "dataset_role": "INSPECTED_DEVELOPMENT_ONLY",
            "timeframe": locked.contract.timeframe,
            "assets": list(locked.contract.products),
            "asset_rows": {
                product_id: len(frame)
                for product_id, frame in sorted(locked.assets.items())
            },
            "strategy_order": list(locked.strategy_engines),
            "configuration": locked.configuration.as_dict(),
            "interpretation_policy": screening_interpretation_policy(),
            "separate_screening_runner_review_required": True,
            **_safety_boundary(),
        }
    else:
        result = preregistration.declaration()
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
