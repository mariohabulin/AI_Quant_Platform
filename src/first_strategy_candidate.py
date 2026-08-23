"""Immutable pre-registration for the first AI Alpha strategy candidate."""

import argparse
from dataclasses import dataclass
import json

try:
    from coinbase_research_dataset import (
        FIRST_CANDIDATE_DATASET_CONTRACT,
        CoinbaseResearchDatasetLock,
    )
    from strategies.ema_strategy import EMAStrategy
    from strategy_engine import StrategyEngine
    from strategy_evaluation_protocol import (
        ExecutionCostProfile,
        StrategyCandidate,
        StrategyEvaluationConfig,
    )
    from strategy_library import StrategyLibrary
except ImportError:  # package import when src is not placed directly on sys.path
    from src.coinbase_research_dataset import (
        FIRST_CANDIDATE_DATASET_CONTRACT,
        CoinbaseResearchDatasetLock,
    )
    from src.strategies.ema_strategy import EMAStrategy
    from src.strategy_engine import StrategyEngine
    from src.strategy_evaluation_protocol import (
        ExecutionCostProfile,
        StrategyCandidate,
        StrategyEvaluationConfig,
    )
    from src.strategy_library import StrategyLibrary


CANDIDATE_ID = "ema-crossover-20-50-btc-eth-native-6h-v1"
STRATEGY_NAME = "ema_crossover"
HYPOTHESIS = (
    "A frozen long-only EMA 20/50 crossover on native Coinbase six-hour spot "
    "candles will retain positive unseen absolute and buy-and-hold excess "
    "return across BTC-USD and ETH-USD after low-volume taker costs and an "
    "adverse execution-cost stress profile."
)
PARAMETER_SET_ID = "fast_period=20;slow_period=50;long_only=true;leverage=none"

BASELINE_COSTS = ExecutionCostProfile(
    label="coinbase_low_volume_taker_baseline_v1",
    commission_rate=0.006,
    slippage_rate=0.0005,
    spread_rate=0.001,
)
STRESSED_COSTS = ExecutionCostProfile(
    label="coinbase_adverse_market_order_stress_v1",
    commission_rate=0.006,
    slippage_rate=0.0015,
    spread_rate=0.003,
)


def first_candidate_configuration():
    return StrategyEvaluationConfig(
        train_size=2880,
        test_size=720,
        step_size=720,
        expanding=True,
        in_sample_fraction=0.70,
        initial_capital=5000.0,
        simulations=5000,
        confidence_level=0.95,
        random_seed=20260822,
        min_positive_walk_forward_excess_rate=0.60,
        min_assets=2,
        min_validated_asset_rate=1.0,
        max_rejected_asset_rate=0.0,
        min_walk_forward_windows=5,
        min_unseen_trades_per_asset=30,
        max_oos_drawdown_percent=20.0,
        baseline_costs=BASELINE_COSTS,
        stressed_costs=STRESSED_COSTS,
        execution_timing="next_bar_open",
        terminal_position_policy="force_close_at_final_close",
    )


def first_candidate_strategy_engine():
    library = StrategyLibrary()
    library.register(EMAStrategy(fast_period=20, slow_period=50))
    return StrategyEngine(library, STRATEGY_NAME)


@dataclass(frozen=True)
class LockedFirstCandidate:
    candidate: StrategyCandidate
    configuration: StrategyEvaluationConfig
    strategy_engine: object
    assets: dict
    manifest_sha256: str


class FirstStrategyCandidatePreregistration:
    """Freeze the candidate now and finalize identity only from hashed data."""

    def __init__(self, contract=FIRST_CANDIDATE_DATASET_CONTRACT):
        self.contract = contract
        self.dataset_lock = CoinbaseResearchDatasetLock(contract)

    def declaration(self):
        configuration = first_candidate_configuration()
        baseline_one_way = (
            BASELINE_COSTS.commission_rate
            + BASELINE_COSTS.slippage_rate
            + BASELINE_COSTS.spread_rate / 2.0
        )
        stress_one_way = (
            STRESSED_COSTS.commission_rate
            + STRESSED_COSTS.slippage_rate
            + STRESSED_COSTS.spread_rate / 2.0
        )
        return {
            "status": "DATASET_LOCK_PENDING",
            "candidate_id": CANDIDATE_ID,
            "strategy_name": STRATEGY_NAME,
            "hypothesis": HYPOTHESIS,
            "parameter_set_id": PARAMETER_SET_ID,
            "timeframe": self.contract.timeframe,
            "assets": list(self.contract.products),
            "dataset_contract": self.contract.as_dict(),
            "configuration": configuration.as_dict(),
            "modeled_one_way_friction": {
                "baseline_rate": baseline_one_way,
                "stress_rate": stress_one_way,
            },
            "optimization_authorized": False,
            "evaluation_authorized_before_dataset_lock": False,
            "live_execution_authorized": False,
        }

    def lock(self, manifest_path):
        dataset = self.dataset_lock.lock(manifest_path)
        manifest_sha256 = dataset.manifest_sha256
        assets = dataset.assets
        candidate = StrategyCandidate(
            candidate_id=CANDIDATE_ID,
            strategy_name=STRATEGY_NAME,
            hypothesis=HYPOTHESIS,
            parameter_set_id=PARAMETER_SET_ID,
            data_version=(
                f"{self.contract.dataset_id};manifest_sha256={manifest_sha256}"
            ),
            timeframe=self.contract.timeframe,
            assets=self.contract.products,
        )
        return LockedFirstCandidate(
            candidate=candidate,
            configuration=first_candidate_configuration(),
            strategy_engine=first_candidate_strategy_engine(),
            assets=assets,
            manifest_sha256=manifest_sha256,
        )


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="Declare or data-lock the first strategy candidate."
    )
    parser.add_argument(
        "--manifest",
        help="Validate a canonical dataset manifest and print the locked identity.",
    )
    args = parser.parse_args(argv)
    preregistration = FirstStrategyCandidatePreregistration()
    if args.manifest:
        locked = preregistration.lock(args.manifest)
        result = {
            "status": "DATASET_LOCKED",
            "candidate": locked.candidate.as_dict(),
            "configuration": locked.configuration.as_dict(),
            "manifest_sha256": locked.manifest_sha256,
            "asset_rows": {
                product_id: len(frame)
                for product_id, frame in sorted(locked.assets.items())
            },
            "evaluation_executed": False,
            "optimization_authorized": False,
            "live_execution_authorized": False,
        }
    else:
        result = preregistration.declaration()
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
