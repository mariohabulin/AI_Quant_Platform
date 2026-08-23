"""One-shot canonical evidence runner for frozen strategy-family screening."""

import argparse
import hashlib
import json
from dataclasses import dataclass
from pathlib import Path

try:
    from first_strategy_candidate import BASELINE_COSTS, STRESSED_COSTS
    from multi_asset import MultiAssetValidator
    from research_evidence import canonical_json_bytes
    from research_evidence_compaction import (
        compact_multi_asset_evaluation,
        profile_summary,
    )
    from strategy_family_screening import (
        DEVELOPMENT_MANIFEST_SHA256,
        SCREENING_ID,
        SCREENING_OUTCOMES,
        StrategyFamilyScreeningPreregistration,
        screening_configuration,
        screening_interpretation_policy,
    )
except ImportError:  # package import when src is not placed directly on sys.path
    from src.first_strategy_candidate import BASELINE_COSTS, STRESSED_COSTS
    from src.multi_asset import MultiAssetValidator
    from src.research_evidence import canonical_json_bytes
    from src.research_evidence_compaction import (
        compact_multi_asset_evaluation,
        profile_summary,
    )
    from src.strategy_family_screening import (
        DEVELOPMENT_MANIFEST_SHA256,
        SCREENING_ID,
        SCREENING_OUTCOMES,
        StrategyFamilyScreeningPreregistration,
        screening_configuration,
        screening_interpretation_policy,
    )


SCREENING_REPORT_SCHEMA_VERSION = 1
SCREENING_DIRECTORY_NAME = "screening_v1"
STAGING_DIRECTORY_NAME = ".screening_v1.staging"
REPORT_FILENAME = "strategy_family_screening_report.json"
CHECKSUM_FILENAME = "strategy_family_screening_report.sha256"
DEFAULT_OUTPUT_ROOT = Path("data/research/strategy_family_screening_v1")
ALLOWED_VALIDATION_STATUSES = frozenset(
    {"VALIDATED", "CONDITIONAL", "REJECTED"}
)


@dataclass(frozen=True)
class RecordedStrategyFamilyScreening:
    report_path: Path
    checksum_path: Path
    report_sha256: str
    outcome_counts: dict
    mechanisms_retaining_interest: tuple
    status: str = "STRATEGY_FAMILY_SCREENING_RECORDED"

    def as_dict(self):
        return {
            "status": self.status,
            "report_path": str(self.report_path),
            "checksum_path": str(self.checksum_path),
            "report_sha256": self.report_sha256,
            "outcome_counts": self.outcome_counts,
            "mechanisms_retaining_interest": list(
                self.mechanisms_retaining_interest
            ),
            "development_screening_executed": True,
            "automatic_ranking_generated": False,
            "automatic_strategy_selection": False,
            "formal_candidate_evaluation": False,
            "candidate_v2_authorized": False,
            "optimization_authorized": False,
            "bounded_forward_paper_review_eligible": False,
            "bounded_forward_paper_authorized": False,
            "live_execution_authorized": False,
        }


class StrategyFamilyScreeningRunner:
    """Evaluate each frozen default twice and atomically record evidence once."""

    def __init__(
        self,
        output_root=DEFAULT_OUTPUT_ROOT,
        preregistration=None,
        validator_factory=MultiAssetValidator,
    ):
        self.output_root = Path(output_root)
        self.output_directory = self.output_root / SCREENING_DIRECTORY_NAME
        self.staging_directory = self.output_root / STAGING_DIRECTORY_NAME
        self.preregistration = (
            preregistration
            if preregistration is not None
            else StrategyFamilyScreeningPreregistration()
        )
        self.validator_factory = validator_factory

    def _assert_not_previously_executed(self):
        if self.output_directory.exists():
            raise FileExistsError(
                "Strategy-family screening evidence already exists; refusing "
                "to overwrite or repeat the frozen development screen."
            )
        if self.staging_directory.exists():
            raise FileExistsError(
                "An incomplete strategy-family screening staging directory "
                "exists; review it before any retry."
            )

    @staticmethod
    def _validate_locked_screening(locked):
        if locked.manifest_sha256 != DEVELOPMENT_MANIFEST_SHA256:
            raise ValueError(
                "Manifest SHA-256 does not match the exact frozen screening dataset."
            )
        if locked.configuration != screening_configuration():
            raise ValueError("Locked screening configuration is invalid.")
        expected_assets = ("BTC-USD", "ETH-USD")
        if (
            locked.contract.dataset_id
            != "coinbase-exchange-btc-eth-native-6h-20190101-20260801-v1"
            or locked.contract.timeframe != "6h"
            or tuple(locked.contract.products) != expected_assets
        ):
            raise ValueError("Locked screening dataset contract is invalid.")
        if tuple(sorted(locked.assets)) != expected_assets:
            raise ValueError("Locked screening asset scope is invalid.")
        expected_order = (
            "adx",
            "atr",
            "bollinger",
            "donchian",
            "macd",
            "rsi",
            "stochastic",
            "supertrend",
        )
        if tuple(locked.strategy_engines) != expected_order:
            raise ValueError("Locked screening strategy order is invalid.")
        if any(
            name != engine.strategy_name
            for name, engine in locked.strategy_engines.items()
        ):
            raise ValueError("Locked screening strategy identity is invalid.")

    @staticmethod
    def _validate_strategy_declarations(declaration, strategy_engines):
        strategy_order = tuple(strategy_engines)
        try:
            strategies = declaration["strategies"]
            observed_order = tuple(item["strategy_name"] for item in strategies)
        except (KeyError, TypeError) as exc:
            raise ValueError("Screening strategy declarations are incomplete.") from exc
        if observed_order != strategy_order:
            raise ValueError("Screening strategy declarations are out of scope.")
        declarations = {}
        for item in strategies:
            try:
                identity = {
                    "strategy_name": item["strategy_name"],
                    "family": item["family"],
                    "mechanism": item["mechanism"],
                    "default_parameters": item["default_parameters"],
                }
                fingerprint = item["configuration_fingerprint"]
            except (KeyError, TypeError) as exc:
                raise ValueError(
                    "Screening strategy declaration identity is incomplete."
                ) from exc
            expected_fingerprint = hashlib.sha256(
                canonical_json_bytes(identity)
            ).hexdigest()
            if fingerprint != expected_fingerprint:
                raise ValueError(
                    "Screening strategy declaration fingerprint is invalid."
                )
            strategy = strategy_engines[item["strategy_name"]].strategy
            if any(
                not hasattr(strategy, parameter)
                or getattr(strategy, parameter) != value
                for parameter, value in item["default_parameters"].items()
            ):
                raise ValueError("Locked screening strategy parameters are invalid.")
            declarations[item["strategy_name"]] = item
        return declarations

    @staticmethod
    def _validate_evaluation(result, strategy_name):
        if not isinstance(result, dict):
            raise TypeError("Multi-asset validator must return a dictionary.")
        if result.get("strategy") != strategy_name:
            raise ValueError("Screening evaluation strategy identity is invalid.")
        if result.get("asset_count") != 2:
            raise ValueError("Screening evaluation asset count is invalid.")
        assets = result.get("assets")
        if not isinstance(assets, dict) or tuple(sorted(assets)) != (
            "BTC-USD",
            "ETH-USD",
        ):
            raise ValueError("Screening evaluation asset scope is invalid.")
        classification = result.get("classification")
        if (
            not isinstance(classification, dict)
            or classification.get("status") not in ALLOWED_VALIDATION_STATUSES
        ):
            raise ValueError("Screening evaluation classification is invalid.")
        for asset_name, asset_result in assets.items():
            if asset_result.get("strategy") != strategy_name:
                raise ValueError(
                    f"Screening evaluation strategy identity is invalid for {asset_name}."
                )
            status = asset_result.get("classification", {}).get("status")
            if status not in ALLOWED_VALIDATION_STATUSES:
                raise ValueError(
                    f"Screening asset classification is invalid for {asset_name}."
                )

    def _evaluate_profile(self, engine, assets, configuration, costs):
        validator = self.validator_factory(
            engine,
            **configuration.validator_kwargs(costs),
        )
        result = validator.run(assets)
        self._validate_evaluation(result, engine.strategy_name)
        return compact_multi_asset_evaluation(result)

    @staticmethod
    def _screening_review(baseline, stress, configuration):
        profile_evidence = {"baseline": baseline, "stress": stress}
        assets = tuple(sorted(baseline["assets"]))
        if tuple(sorted(stress["assets"])) != assets:
            raise ValueError("Baseline and stress asset scopes do not match.")

        minimum_windows = all(
            profile["assets"][asset]["walk_forward"]["summary"]["window_count"]
            >= configuration.min_walk_forward_windows
            for profile in profile_evidence.values()
            for asset in assets
        )
        minimum_trades = all(
            profile["assets"][asset]["walk_forward"]["unseen_trade_count"]
            >= configuration.min_unseen_trades_per_asset
            for profile in profile_evidence.values()
            for asset in assets
        )
        drawdown_within_limit = all(
            profile["assets"][asset]["out_of_sample"]["out_of_sample"][
                "performance"
            ]["max_drawdown"]
            <= configuration.max_oos_drawdown_percent
            for profile in profile_evidence.values()
            for asset in assets
        )
        gates = {
            "baseline_multi_asset_validated": (
                baseline["classification"]["status"] == "VALIDATED"
            ),
            "cost_stress_multi_asset_validated": (
                stress["classification"]["status"] == "VALIDATED"
            ),
            "minimum_walk_forward_windows": minimum_windows,
            "minimum_unseen_trades_per_asset": minimum_trades,
            "oos_drawdown_within_limit": drawdown_within_limit,
        }
        if "REJECTED" in {
            baseline["classification"]["status"],
            stress["classification"]["status"],
        }:
            outcome = "SCREEN_OUT"
        elif all(gates.values()):
            outcome = "MECHANISM_RETAINS_INTEREST"
        else:
            outcome = "INCONCLUSIVE"
        return {
            "outcome": outcome,
            "gates": gates,
            "failed_gates": [name for name, passed in gates.items() if not passed],
            "thresholds": {
                "min_walk_forward_windows": (
                    configuration.min_walk_forward_windows
                ),
                "min_unseen_trades_per_asset": (
                    configuration.min_unseen_trades_per_asset
                ),
                "max_oos_drawdown_percent": (
                    configuration.max_oos_drawdown_percent
                ),
            },
            "candidate_v2_authorized": False,
            "bounded_forward_paper_authorized": False,
            "live_execution_authorized": False,
        }

    @staticmethod
    def _strategy_comparison(strategy_evidence, strategy_order):
        strategies = {}
        outcome_counts = {outcome: 0 for outcome in SCREENING_OUTCOMES}
        retaining_interest = []
        for strategy_name in strategy_order:
            evidence = strategy_evidence[strategy_name]
            baseline = evidence["baseline_evaluation"]
            stress = evidence["cost_stress_evaluation"]
            review = evidence["screening_review"]
            outcome = review["outcome"]
            outcome_counts[outcome] += 1
            if outcome == "MECHANISM_RETAINS_INTEREST":
                retaining_interest.append(strategy_name)
            assets = {}
            for asset_name in sorted(baseline["assets"]):
                assets[asset_name] = {
                    "baseline": profile_summary(baseline["assets"][asset_name]),
                    "stress": profile_summary(stress["assets"][asset_name]),
                }
            strategies[strategy_name] = {
                "outcome": outcome,
                "gates": review["gates"],
                "failed_gates": review["failed_gates"],
                "baseline_aggregate_classification": baseline[
                    "classification"
                ]["status"],
                "cost_stress_aggregate_classification": stress[
                    "classification"
                ]["status"],
                "assets": assets,
            }
        return {
            "strategy_order": list(strategy_order),
            "selection_policy": "DESCRIPTIVE_MULTIPLE_COMPARISON_GUARD",
            "automatic_ranking_generated": False,
            "automatic_strategy_selection": False,
            "outcome_counts": outcome_counts,
            "mechanisms_retaining_interest": retaining_interest,
            "strategies": strategies,
        }

    def run(self, manifest_path):
        self._assert_not_previously_executed()
        locked = self.preregistration.lock(manifest_path)
        self._validate_locked_screening(locked)
        strategy_order = tuple(locked.strategy_engines)
        declarations = self._validate_strategy_declarations(
            self.preregistration.declaration(),
            locked.strategy_engines,
        )

        strategy_evidence = {}
        for strategy_name in strategy_order:
            engine = locked.strategy_engines[strategy_name]
            baseline = self._evaluate_profile(
                engine,
                locked.assets,
                locked.configuration,
                BASELINE_COSTS,
            )
            stress = self._evaluate_profile(
                engine,
                locked.assets,
                locked.configuration,
                STRESSED_COSTS,
            )
            strategy_evidence[strategy_name] = {
                "strategy_identity": declarations[strategy_name],
                "baseline_evaluation": baseline,
                "cost_stress_evaluation": stress,
                "screening_review": self._screening_review(
                    baseline,
                    stress,
                    locked.configuration,
                ),
            }

        comparison = self._strategy_comparison(
            strategy_evidence,
            strategy_order,
        )
        payload = {
            "schema_version": SCREENING_REPORT_SCHEMA_VERSION,
            "status": "STRATEGY_FAMILY_SCREENING_COMPLETED",
            "screening_id": SCREENING_ID,
            "screening_type": "DESCRIPTIVE_DEVELOPMENT_EVIDENCE",
            "manifest_sha256": locked.manifest_sha256,
            "data_version": (
                f"{locked.contract.dataset_id};"
                f"manifest_sha256={locked.manifest_sha256}"
            ),
            "dataset_contract": locked.contract.as_dict(),
            "dataset_role": "INSPECTED_DEVELOPMENT_ONLY",
            "development_data_only": True,
            "strategy_order": list(strategy_order),
            "strategy_count": len(strategy_order),
            "configuration": locked.configuration.as_dict(),
            "interpretation_policy": screening_interpretation_policy(),
            "strategy_evidence": strategy_evidence,
            "comparison": comparison,
            "screening_executed": True,
            "performance_evaluation_executed": True,
            "development_screening_executed": True,
            "automatic_ranking_generated": False,
            "automatic_strategy_selection": False,
            "parameter_sweep_executed": False,
            "strategy_combination_executed": False,
            "formal_candidate_evaluation": False,
            "selected_strategy": None,
            "candidate_v2_authorized": False,
            "optimization_authorized": False,
            "bounded_forward_paper_review_eligible": False,
            "bounded_forward_paper_authorized": False,
            "live_execution_authorized": False,
        }
        report_bytes = canonical_json_bytes(payload)
        report_sha256 = hashlib.sha256(report_bytes).hexdigest()
        checksum_bytes = f"{report_sha256}  {REPORT_FILENAME}\n".encode("ascii")

        self.output_root.mkdir(parents=True, exist_ok=True)
        self.staging_directory.mkdir(exist_ok=False)
        staged_report = self.staging_directory / REPORT_FILENAME
        staged_checksum = self.staging_directory / CHECKSUM_FILENAME
        staged_report.write_bytes(report_bytes)
        staged_checksum.write_bytes(checksum_bytes)
        self.staging_directory.rename(self.output_directory)

        return RecordedStrategyFamilyScreening(
            report_path=self.output_directory / REPORT_FILENAME,
            checksum_path=self.output_directory / CHECKSUM_FILENAME,
            report_sha256=report_sha256,
            outcome_counts=comparison["outcome_counts"],
            mechanisms_retaining_interest=tuple(
                comparison["mechanisms_retaining_interest"]
            ),
        )


def main(argv=None):
    parser = argparse.ArgumentParser(
        description=(
            "Execute and atomically record the frozen default-only strategy-family "
            "development screen once."
        )
    )
    parser.add_argument(
        "--manifest",
        required=True,
        help="Path to the exact locked native BTC/ETH six-hour manifest.",
    )
    args = parser.parse_args(argv)
    recorded = StrategyFamilyScreeningRunner().run(args.manifest)
    print(json.dumps(recorded.as_dict(), indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
