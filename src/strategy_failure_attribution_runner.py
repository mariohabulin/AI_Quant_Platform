"""One-shot evidence runner for causal strategy-failure attribution."""

import argparse
from dataclasses import dataclass
import hashlib
import json
from pathlib import Path

try:
    from failure_attribution_metrics import FailureAttributionMetrics
    from first_strategy_candidate import BASELINE_COSTS, STRESSED_COSTS
    from multi_asset import MultiAssetValidator
    from research_evidence import canonical_json_bytes
    from research_evidence_compaction import compact_multi_asset_evaluation
    from strategy_failure_attribution import (
        ATTRIBUTION_ID,
        RECORDED_SCREENING_REPORT_SHA256,
        RECORDED_STRATEGY_ORDER,
        ZERO_COSTS,
        FailureAttributionPreregistration,
        failure_attribution_configuration,
        interpretation_policy,
        volume_policy,
    )
    from strategy_family_screening import DEVELOPMENT_MANIFEST_SHA256
except ImportError:  # package import when src is not placed directly on sys.path
    from src.failure_attribution_metrics import FailureAttributionMetrics
    from src.first_strategy_candidate import BASELINE_COSTS, STRESSED_COSTS
    from src.multi_asset import MultiAssetValidator
    from src.research_evidence import canonical_json_bytes
    from src.research_evidence_compaction import compact_multi_asset_evaluation
    from src.strategy_failure_attribution import (
        ATTRIBUTION_ID,
        RECORDED_SCREENING_REPORT_SHA256,
        RECORDED_STRATEGY_ORDER,
        ZERO_COSTS,
        FailureAttributionPreregistration,
        failure_attribution_configuration,
        interpretation_policy,
        volume_policy,
    )
    from src.strategy_family_screening import DEVELOPMENT_MANIFEST_SHA256


ATTRIBUTION_REPORT_SCHEMA_VERSION = 1
ATTRIBUTION_DIRECTORY_NAME = "attribution_v1"
STAGING_DIRECTORY_NAME = ".attribution_v1.staging"
REPORT_FILENAME = "failure_attribution_report.json"
CHECKSUM_FILENAME = "failure_attribution_report.sha256"
DEFAULT_OUTPUT_ROOT = Path("data/research/strategy_failure_attribution_v1")
PROFILE_ORDER = ("zero_cost", "baseline", "stress")
PROFILE_COSTS = {
    "zero_cost": ZERO_COSTS,
    "baseline": BASELINE_COSTS,
    "stress": STRESSED_COSTS,
}


@dataclass(frozen=True)
class RecordedFailureAttribution:
    report_path: Path
    checksum_path: Path
    report_sha256: str
    diagnostic_multi_asset_replays: int
    strategy_count: int
    status: str = "FAILURE_ATTRIBUTION_RECORDED"

    def as_dict(self):
        return {
            "status": self.status,
            "report_path": str(self.report_path),
            "checksum_path": str(self.checksum_path),
            "report_sha256": self.report_sha256,
            "diagnostic_multi_asset_replays": (
                self.diagnostic_multi_asset_replays
            ),
            "strategy_count": self.strategy_count,
            "failure_attribution_executed": True,
            "performance_replay_executed": True,
            "volume_analysis_executed": True,
            "market_regime_analysis_executed": True,
            "automatic_ranking_generated": False,
            "automatic_strategy_selection": False,
            "new_alpha_hypothesis_generated": False,
            "candidate_v2_authorized": False,
            "optimization_authorized": False,
            "bounded_forward_paper_review_eligible": False,
            "bounded_forward_paper_authorized": False,
            "live_execution_authorized": False,
        }


class FailureAttributionRunner:
    """Replay the exact matrix once and atomically record explanatory evidence."""

    def __init__(
        self,
        output_root=DEFAULT_OUTPUT_ROOT,
        preregistration=None,
        validator_factory=MultiAssetValidator,
        metrics_factory=FailureAttributionMetrics,
    ):
        self.output_root = Path(output_root)
        self.output_directory = self.output_root / ATTRIBUTION_DIRECTORY_NAME
        self.staging_directory = self.output_root / STAGING_DIRECTORY_NAME
        self.preregistration = (
            preregistration
            if preregistration is not None
            else FailureAttributionPreregistration()
        )
        self.validator_factory = validator_factory
        self.metrics_factory = metrics_factory

    def _assert_not_previously_executed(self):
        if self.output_directory.exists():
            raise FileExistsError(
                "Failure-attribution evidence already exists; refusing to "
                "overwrite or repeat the frozen diagnostic matrix."
            )
        if self.staging_directory.exists():
            raise FileExistsError(
                "An incomplete failure-attribution staging directory exists; "
                "review it before any retry."
            )

    @staticmethod
    def _validate_locked(locked):
        if locked.manifest_sha256 != DEVELOPMENT_MANIFEST_SHA256:
            raise ValueError("Locked attribution manifest SHA-256 is invalid.")
        if locked.screening_report_sha256 != RECORDED_SCREENING_REPORT_SHA256:
            raise ValueError("Locked screening-report SHA-256 is invalid.")
        if locked.attribution_configuration != failure_attribution_configuration():
            raise ValueError("Locked attribution configuration is invalid.")
        if tuple(locked.strategy_engines) != RECORDED_STRATEGY_ORDER:
            raise ValueError("Locked attribution strategy scope or order is invalid.")
        if tuple(sorted(locked.assets)) != ("BTC-USD", "ETH-USD"):
            raise ValueError("Locked attribution asset scope is invalid.")
        if (
            locked.contract.dataset_id
            != "coinbase-exchange-btc-eth-native-6h-20190101-20260801-v1"
            or locked.contract.timeframe != "6h"
            or tuple(locked.contract.products) != ("BTC-USD", "ETH-USD")
            or locked.contract.granularity_seconds != 21600
        ):
            raise ValueError("Locked attribution dataset contract is invalid.")
        if any(
            name != engine.strategy_name
            for name, engine in locked.strategy_engines.items()
        ):
            raise ValueError("Locked attribution strategy identity is invalid.")

    @staticmethod
    def _validate_declaration(declaration):
        required_false = (
            "failure_attribution_executed",
            "performance_replay_executed",
            "automatic_ranking_generated",
            "automatic_strategy_selection",
            "parameter_sweep_authorized",
            "strategy_combination_authorized",
            "candidate_v2_authorized",
            "bounded_forward_paper_authorized",
            "live_execution_authorized",
        )
        if (
            declaration.get("attribution_id") != ATTRIBUTION_ID
            or declaration.get("required_manifest_sha256")
            != DEVELOPMENT_MANIFEST_SHA256
            or declaration.get("required_screening_report_sha256")
            != RECORDED_SCREENING_REPORT_SHA256
            or declaration.get("strategy_order") != list(RECORDED_STRATEGY_ORDER)
            or declaration.get("configuration")
            != failure_attribution_configuration()
            or any(declaration.get(flag) is not False for flag in required_false)
        ):
            raise ValueError("Failure-attribution declaration boundary is invalid.")

    @staticmethod
    def _validate_raw_evaluation(result, strategy_name, assets):
        if not isinstance(result, dict):
            raise TypeError("Multi-asset diagnostic result must be a dictionary.")
        if result.get("strategy") != strategy_name:
            raise ValueError("Diagnostic strategy identity drifted during replay.")
        if result.get("asset_count") != len(assets):
            raise ValueError("Diagnostic asset count is invalid.")
        observed_assets = result.get("assets")
        if not isinstance(observed_assets, dict) or tuple(sorted(observed_assets)) != tuple(
            sorted(assets)
        ):
            raise ValueError("Diagnostic asset scope drifted during replay.")
        for name, item in observed_assets.items():
            if item.get("strategy") != strategy_name:
                raise ValueError(f"Diagnostic strategy identity drifted for {name}.")
            try:
                execution_timing = item["out_of_sample"]["out_of_sample"][
                    "execution_timing"
                ]
            except (KeyError, TypeError) as exc:
                raise ValueError("Diagnostic OOS execution evidence is incomplete.") from exc
            if execution_timing != "next_bar_open":
                raise ValueError("Diagnostic execution timing drifted.")

    def _evaluate(self, engine, assets, configuration, costs):
        validator = self.validator_factory(
            engine,
            **configuration.validator_kwargs(costs),
        )
        result = validator.run(assets)
        self._validate_raw_evaluation(result, engine.strategy_name, assets)
        return result

    @staticmethod
    def _profile_asset_values(raw_result, diagnostics, asset_name):
        asset = raw_result["assets"][asset_name]
        oos = asset["out_of_sample"]["out_of_sample"]
        return {
            "oos_strategy_return": float(oos["comparison"]["strategy_return"]),
            "oos_benchmark_return": float(oos["comparison"]["benchmark_return"]),
            "oos_excess_return": float(oos["comparison"]["excess_return"]),
            "net_profit_loss": diagnostics["cost_turnover"]["net_profit_loss"],
            "gross_profit_loss": diagnostics["cost_turnover"][
                "gross_profit_loss"
            ],
            "total_costs": diagnostics["cost_turnover"]["total_costs"],
            "turnover_multiple_of_initial_capital": diagnostics[
                "cost_turnover"
            ]["turnover_multiple_of_initial_capital"],
            "exposure_percent": diagnostics["exposure_holding"][
                "exposure_percent"
            ],
            "max_drawdown_percent": diagnostics["drawdown"][
                "max_drawdown_percent"
            ],
            "walk_forward_positive_excess_rate": float(
                asset["walk_forward"]["summary"]["positive_test_excess_rate"]
            ),
            "passes_statistical_falsification": bool(
                asset["falsification"]["passes_statistical_falsification"]
            ),
            "validation_classification": asset["classification"]["status"],
        }

    @staticmethod
    def _diagnostic_flags(profile_values, configuration):
        zero = profile_values["zero_cost"]
        baseline = profile_values["baseline"]
        stress = profile_values["stress"]
        flags = []
        if zero["oos_strategy_return"] > 0.0:
            flags.append("ZERO_COST_OOS_RETURN_POSITIVE")
        else:
            flags.append("NO_POSITIVE_ZERO_COST_OOS_RETURN")
        if zero["oos_strategy_return"] > 0.0 and baseline["oos_strategy_return"] <= 0.0:
            flags.append("BASELINE_COST_SURVIVAL_FAILED")
        if baseline["oos_strategy_return"] > 0.0 and stress["oos_strategy_return"] <= 0.0:
            flags.append("STRESS_COST_SURVIVAL_FAILED")
        if baseline["max_drawdown_percent"] > configuration.max_oos_drawdown_percent:
            flags.append("BASELINE_DRAWDOWN_LIMIT_EXCEEDED")
        if stress["max_drawdown_percent"] > configuration.max_oos_drawdown_percent:
            flags.append("STRESS_DRAWDOWN_LIMIT_EXCEEDED")
        if baseline["walk_forward_positive_excess_rate"] < (
            configuration.min_positive_walk_forward_excess_rate
        ):
            flags.append("BASELINE_WALK_FORWARD_PERSISTENCE_FAILED")
        if stress["walk_forward_positive_excess_rate"] < (
            configuration.min_positive_walk_forward_excess_rate
        ):
            flags.append("STRESS_WALK_FORWARD_PERSISTENCE_FAILED")
        if not baseline["passes_statistical_falsification"]:
            flags.append("BASELINE_FALSIFICATION_FAILED")
        if not stress["passes_statistical_falsification"]:
            flags.append("STRESS_FALSIFICATION_FAILED")
        return flags

    def _cross_profile(self, raw_profiles, diagnostic_profiles, configuration):
        assets = {}
        for asset_name in ("BTC-USD", "ETH-USD"):
            values = {
                profile: self._profile_asset_values(
                    raw_profiles[profile],
                    diagnostic_profiles[profile][asset_name],
                    asset_name,
                )
                for profile in PROFILE_ORDER
            }
            assets[asset_name] = {
                "profiles": values,
                "oos_strategy_return": {
                    profile: values[profile]["oos_strategy_return"]
                    for profile in PROFILE_ORDER
                },
                "zero_to_baseline_oos_return_change": (
                    values["baseline"]["oos_strategy_return"]
                    - values["zero_cost"]["oos_strategy_return"]
                ),
                "baseline_to_stress_oos_return_change": (
                    values["stress"]["oos_strategy_return"]
                    - values["baseline"]["oos_strategy_return"]
                ),
                "diagnostic_flags": self._diagnostic_flags(
                    values, configuration
                ),
            }
        return {
            "profile_order": list(PROFILE_ORDER),
            "comparison_purpose": "FAILURE_ATTRIBUTION_NOT_RANKING",
            "assets": assets,
        }

    def run(self, manifest_path, screening_report_path):
        self._assert_not_previously_executed()
        locked = self.preregistration.lock(manifest_path, screening_report_path)
        self._validate_locked(locked)
        self._validate_declaration(self.preregistration.declaration())
        configuration = locked.screening_configuration
        metrics = self.metrics_factory(
            granularity_seconds=locked.contract.granularity_seconds
        )

        strategy_evidence = {}
        for strategy_name in RECORDED_STRATEGY_ORDER:
            engine = locked.strategy_engines[strategy_name]
            raw_profiles = {}
            diagnostic_profiles = {}
            persisted_profiles = {}
            for profile in PROFILE_ORDER:
                costs = PROFILE_COSTS[profile]
                raw = self._evaluate(
                    engine, locked.assets, configuration, costs
                )
                diagnostics = {
                    asset_name: metrics.analyze(
                        locked.assets[asset_name], raw["assets"][asset_name]
                    )
                    for asset_name in sorted(locked.assets)
                }
                raw_profiles[profile] = raw
                diagnostic_profiles[profile] = diagnostics
                persisted_profiles[profile] = {
                    "costs": costs.as_dict(),
                    "evaluation": compact_multi_asset_evaluation(raw),
                    "attribution": {"assets": diagnostics},
                }
            strategy_evidence[strategy_name] = {
                "profiles": persisted_profiles,
                "cross_profile_attribution": self._cross_profile(
                    raw_profiles, diagnostic_profiles, configuration
                ),
            }

        payload = {
            "schema_version": ATTRIBUTION_REPORT_SCHEMA_VERSION,
            "status": "FAILURE_ATTRIBUTION_COMPLETED",
            "attribution_id": ATTRIBUTION_ID,
            "attribution_type": "INSPECTED_DEVELOPMENT_FAILURE_DIAGNOSTIC",
            "manifest_sha256": locked.manifest_sha256,
            "screening_report_sha256": locked.screening_report_sha256,
            "dataset_contract": locked.contract.as_dict(),
            "dataset_role": "INSPECTED_DEVELOPMENT_ONLY",
            "strategy_order": list(RECORDED_STRATEGY_ORDER),
            "strategy_count": len(RECORDED_STRATEGY_ORDER),
            "profile_order": list(PROFILE_ORDER),
            "diagnostic_multi_asset_replays": (
                len(RECORDED_STRATEGY_ORDER) * len(PROFILE_ORDER)
            ),
            "configuration": failure_attribution_configuration(),
            "volume_policy": volume_policy(),
            "interpretation": interpretation_policy(),
            "strategy_evidence": strategy_evidence,
            "failure_attribution_executed": True,
            "performance_replay_executed": True,
            "volume_analysis_executed": True,
            "market_regime_analysis_executed": True,
            "automatic_ranking_generated": False,
            "automatic_strategy_selection": False,
            "parameter_sweep_executed": False,
            "strategy_combination_executed": False,
            "formal_candidate_evaluation": False,
            "selected_strategy": None,
            "new_alpha_hypothesis_generated": False,
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

        return RecordedFailureAttribution(
            report_path=self.output_directory / REPORT_FILENAME,
            checksum_path=self.output_directory / CHECKSUM_FILENAME,
            report_sha256=report_sha256,
            diagnostic_multi_asset_replays=(
                len(RECORDED_STRATEGY_ORDER) * len(PROFILE_ORDER)
            ),
            strategy_count=len(RECORDED_STRATEGY_ORDER),
        )


def main(argv=None):
    parser = argparse.ArgumentParser(
        description=(
            "Execute and atomically record the frozen strategy-failure "
            "attribution matrix once."
        )
    )
    parser.add_argument("--manifest", help="Exact frozen six-hour manifest.")
    parser.add_argument(
        "--screening-report", help="Exact recorded family-screening report."
    )
    args = parser.parse_args(argv)
    if bool(args.manifest) != bool(args.screening_report):
        parser.error("--manifest and --screening-report must be supplied together.")
    if not args.manifest:
        parser.error("Both frozen evidence paths are required.")
    recorded = FailureAttributionRunner().run(
        args.manifest, args.screening_report
    )
    print(json.dumps(recorded.as_dict(), indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
