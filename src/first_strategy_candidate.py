"""Immutable pre-registration for the first AI Alpha strategy candidate."""

import argparse
from dataclasses import dataclass
import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd

try:
    from coinbase_research_dataset import (
        CANONICAL_COLUMN_ORDER,
        DATASET_MANIFEST_SCHEMA_VERSION,
        FIRST_CANDIDATE_DATASET_CONTRACT,
        CoinbaseResearchDatasetContract,
        dataset_canonicalization_metadata,
        dataset_source_metadata,
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
        CANONICAL_COLUMN_ORDER,
        DATASET_MANIFEST_SCHEMA_VERSION,
        FIRST_CANDIDATE_DATASET_CONTRACT,
        CoinbaseResearchDatasetContract,
        dataset_canonicalization_metadata,
        dataset_source_metadata,
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
        if not isinstance(contract, CoinbaseResearchDatasetContract):
            raise TypeError("Contract must be a CoinbaseResearchDatasetContract.")
        self.contract = contract

    @staticmethod
    def _sha256(path):
        return hashlib.sha256(Path(path).read_bytes()).hexdigest()

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

    def _load_and_validate_manifest(self, manifest_path):
        manifest_path = Path(manifest_path)
        manifest_bytes = manifest_path.read_bytes()
        manifest_sha256 = hashlib.sha256(manifest_bytes).hexdigest()
        try:
            manifest = json.loads(manifest_bytes.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise ValueError("Dataset manifest is not valid canonical JSON.") from exc
        canonical_bytes = (
            json.dumps(manifest, indent=2, sort_keys=True) + "\n"
        ).encode("utf-8")
        if canonical_bytes != manifest_bytes:
            raise ValueError("Dataset manifest is not canonical JSON.")
        if set(manifest) != {
            "schema_version", "contract", "source", "canonicalization", "assets"
        }:
            raise ValueError("Dataset manifest fields are invalid.")
        if manifest.get("schema_version") != DATASET_MANIFEST_SCHEMA_VERSION:
            raise ValueError("Dataset manifest schema version is invalid.")
        if manifest.get("contract") != self.contract.as_dict():
            raise ValueError("Dataset manifest does not match the frozen contract.")
        if manifest.get("source") != dataset_source_metadata():
            raise ValueError("Dataset manifest source contract is invalid.")
        if manifest.get("canonicalization") != dataset_canonicalization_metadata():
            raise ValueError("Dataset canonicalization contract is invalid.")
        assets_evidence = manifest.get("assets")
        if not isinstance(assets_evidence, dict):
            raise ValueError("Dataset manifest assets evidence is missing.")
        if tuple(sorted(assets_evidence)) != self.contract.products:
            raise ValueError("Dataset manifest asset scope is invalid.")
        checksum_path = manifest_path.with_name("manifest.sha256")
        if not checksum_path.is_file():
            raise ValueError("Dataset manifest SHA-256 sidecar is missing.")
        expected_checksum = f"{manifest_sha256}  manifest.json\n".encode("ascii")
        if checksum_path.read_bytes() != expected_checksum:
            raise ValueError("Dataset manifest SHA-256 sidecar is invalid.")
        return manifest, manifest_sha256

    def _load_asset(self, manifest_path, product_id, evidence):
        required = {
            "file", "sha256", "rows", "first_timestamp", "last_timestamp"
        }
        if not isinstance(evidence, dict) or set(evidence) != required:
            raise ValueError(f"Dataset evidence for {product_id} is incomplete.")
        filename = evidence["file"]
        if not isinstance(filename, str) or not filename:
            raise ValueError("Dataset manifest file name is invalid.")
        if Path(filename).name != filename:
            raise ValueError("Dataset manifest file names must be basenames.")
        path = Path(manifest_path).parent / filename
        if not path.is_file():
            raise ValueError(f"Dataset file is missing for {product_id}.")
        observed_sha256 = self._sha256(path)
        expected_sha256 = evidence["sha256"]
        if (
            not isinstance(expected_sha256, str)
            or len(expected_sha256) != 64
            or any(character not in "0123456789abcdef" for character in expected_sha256)
        ):
            raise ValueError(f"Dataset SHA-256 evidence is invalid for {product_id}.")
        if observed_sha256 != expected_sha256:
            raise ValueError(f"Dataset SHA-256 mismatch for {product_id}.")
        frame = pd.read_csv(path)
        required_columns = list(CANONICAL_COLUMN_ORDER)
        if list(frame.columns) != required_columns:
            raise ValueError(f"Dataset columns are invalid for {product_id}.")
        expected_rows = evidence["rows"]
        if not isinstance(expected_rows, int) or isinstance(expected_rows, bool):
            raise ValueError(f"Dataset row evidence is invalid for {product_id}.")
        if len(frame) != expected_rows:
            raise ValueError(f"Dataset row count mismatch for {product_id}.")
        if len(frame) != self.contract.expected_rows_per_product:
            raise ValueError(f"Dataset is incomplete for {product_id}.")
        timestamps = pd.to_datetime(frame.pop("Timestamp"), utc=True, errors="raise")
        expected = pd.date_range(
            self.contract.start_timestamp,
            self.contract.end_timestamp,
            freq=pd.Timedelta(seconds=self.contract.granularity_seconds),
            inclusive="left",
        )
        if not pd.DatetimeIndex(timestamps).equals(expected):
            raise ValueError(f"Dataset time grid mismatch for {product_id}.")
        if evidence["first_timestamp"] != expected[0].strftime("%Y-%m-%dT%H:%M:%SZ"):
            raise ValueError(f"Dataset first timestamp mismatch for {product_id}.")
        if evidence["last_timestamp"] != expected[-1].strftime("%Y-%m-%dT%H:%M:%SZ"):
            raise ValueError(f"Dataset last timestamp mismatch for {product_id}.")
        try:
            frame = frame.apply(pd.to_numeric, errors="raise")
        except (TypeError, ValueError) as exc:
            raise ValueError(f"Dataset values are invalid for {product_id}.") from exc
        values = frame[["Open", "High", "Low", "Close", "Volume"]].to_numpy()
        if not np.isfinite(values).all():
            raise ValueError(f"Dataset values must be finite for {product_id}.")
        if (frame[["Open", "High", "Low", "Close"]] <= 0.0).any().any():
            raise ValueError(f"Dataset OHLC values must be positive for {product_id}.")
        if (frame["Volume"] < 0.0).any():
            raise ValueError(f"Dataset volume cannot be negative for {product_id}.")
        price_maximum = frame[["Open", "Low", "Close"]].max(axis=1)
        price_minimum = frame[["Open", "High", "Close"]].min(axis=1)
        if (frame["High"] < price_maximum).any() or (
            frame["Low"] > price_minimum
        ).any():
            raise ValueError(f"Dataset OHLC geometry is invalid for {product_id}.")
        frame.index = expected
        frame.index.name = "Timestamp"
        return frame

    def lock(self, manifest_path):
        manifest, manifest_sha256 = self._load_and_validate_manifest(manifest_path)
        assets = {
            product_id: self._load_asset(
                manifest_path,
                product_id,
                manifest["assets"][product_id],
            )
            for product_id in self.contract.products
        }
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
