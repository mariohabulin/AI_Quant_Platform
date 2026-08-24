"""One-shot canonical runner for frozen Alpha Development Protocol v2."""

import argparse
from dataclasses import dataclass
import hashlib
import json
import math
from pathlib import Path

import pandas as pd

try:
    from alpha_development_protocol import (
        ALPHA_DEVELOPMENT_ID,
        RECORDED_ATTRIBUTION_REPORT_SHA256,
        VARIANT_ORDER,
        AlphaDevelopmentPreregistration,
        alpha_development_configuration,
        alpha_development_evaluation_configuration,
        alpha_development_interpretation_policy,
        alpha_development_protective_exit_policy,
        alpha_development_risk_engine,
        alpha_development_strategy_engines,
    )
    from first_strategy_candidate import BASELINE_COSTS, STRESSED_COSTS
    from multi_asset import MultiAssetValidator
    from research_evidence import canonical_json_bytes
    from research_evidence_compaction import (
        compact_multi_asset_evaluation,
        profile_summary,
    )
    from strategy_family_screening import DEVELOPMENT_MANIFEST_SHA256
    from venue_execution_research import (
        VENUE_EXECUTION_SCENARIOS,
        venue_execution_policy,
    )
except ImportError:  # package import when src is not placed directly on sys.path
    from src.alpha_development_protocol import (
        ALPHA_DEVELOPMENT_ID,
        RECORDED_ATTRIBUTION_REPORT_SHA256,
        VARIANT_ORDER,
        AlphaDevelopmentPreregistration,
        alpha_development_configuration,
        alpha_development_evaluation_configuration,
        alpha_development_interpretation_policy,
        alpha_development_protective_exit_policy,
        alpha_development_risk_engine,
        alpha_development_strategy_engines,
    )
    from src.first_strategy_candidate import BASELINE_COSTS, STRESSED_COSTS
    from src.multi_asset import MultiAssetValidator
    from src.research_evidence import canonical_json_bytes
    from src.research_evidence_compaction import (
        compact_multi_asset_evaluation,
        profile_summary,
    )
    from src.strategy_family_screening import DEVELOPMENT_MANIFEST_SHA256
    from src.venue_execution_research import (
        VENUE_EXECUTION_SCENARIOS,
        venue_execution_policy,
    )


ALPHA_DEVELOPMENT_REPORT_SCHEMA_VERSION = 1
DEVELOPMENT_DIRECTORY_NAME = "development_v2"
STAGING_DIRECTORY_NAME = ".development_v2.staging"
REPORT_FILENAME = "alpha_development_report.json"
CHECKSUM_FILENAME = "alpha_development_report.sha256"
DEFAULT_OUTPUT_ROOT = Path("data/research/alpha_development_v2")
ALLOWED_VALIDATION_STATUSES = frozenset(
    {"VALIDATED", "CONDITIONAL", "REJECTED"}
)
DEVELOPMENT_OUTCOMES = (
    "MECHANISM_RETAINS_DEVELOPMENT_INTEREST",
    "SCREEN_OUT",
    "INCONCLUSIVE",
)
EXECUTABLE_SCENARIOS = tuple(
    scenario for scenario in VENUE_EXECUTION_SCENARIOS
    if scenario.executable_in_v2_runner
)
SCENARIO_ORDER = tuple(scenario.label for scenario in EXECUTABLE_SCENARIOS)


def _finite_float(value, name):
    try:
        result = float(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{name} must be numeric.") from exc
    if not math.isfinite(result):
        raise ValueError(f"{name} must be finite.")
    return result


@dataclass(frozen=True)
class RecordedAlphaDevelopment:
    report_path: Path
    checksum_path: Path
    report_sha256: str
    outcome_counts: dict
    mechanisms_retaining_interest: tuple
    joint_multi_asset_evaluations: int
    status: str = "ALPHA_DEVELOPMENT_RECORDED"

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
            "joint_multi_asset_evaluations": (
                self.joint_multi_asset_evaluations
            ),
            "joint_development_evaluation_executed": True,
            "protective_exit_engine_active": True,
            "automatic_ranking_generated": False,
            "automatic_strategy_selection": False,
            "parameter_calibration_executed": False,
            "formal_candidate_evaluation": False,
            "candidate_v2_authorized": False,
            "optimization_authorized": False,
            "bounded_forward_paper_review_eligible": False,
            "bounded_forward_paper_authorized": False,
            "live_execution_authorized": False,
        }


class AlphaDevelopmentRunner:
    """Evaluate the three fixed joint mechanisms under three taker scenarios."""

    def __init__(
        self,
        output_root=DEFAULT_OUTPUT_ROOT,
        preregistration=None,
        validator_factory=MultiAssetValidator,
        risk_engine_factory=alpha_development_risk_engine,
        protective_exit_policy_factory=(
            alpha_development_protective_exit_policy
        ),
    ):
        for factory, name in (
            (validator_factory, "Validator factory"),
            (risk_engine_factory, "Risk Engine factory"),
            (protective_exit_policy_factory, "Protective Exit Policy factory"),
        ):
            if not callable(factory):
                raise TypeError(f"{name} must be callable.")
        self.output_root = Path(output_root)
        self.output_directory = self.output_root / DEVELOPMENT_DIRECTORY_NAME
        self.staging_directory = self.output_root / STAGING_DIRECTORY_NAME
        self.preregistration = (
            preregistration
            if preregistration is not None
            else AlphaDevelopmentPreregistration()
        )
        self.validator_factory = validator_factory
        self.risk_engine_factory = risk_engine_factory
        self.protective_exit_policy_factory = protective_exit_policy_factory

    def _assert_not_previously_executed(self):
        if self.output_directory.exists():
            raise FileExistsError(
                "Alpha v2 development evidence already exists; refusing to "
                "overwrite or repeat the frozen joint evaluation."
            )
        if self.staging_directory.exists():
            raise FileExistsError(
                "An incomplete Alpha v2 staging directory exists; review it "
                "before any retry."
            )

    @staticmethod
    def _validate_scenarios():
        policy = venue_execution_policy()
        if list(SCENARIO_ORDER) != policy["runner_allowed_labels"]:
            raise ValueError("Executable venue scenario order changed.")
        if len(EXECUTABLE_SCENARIOS) != 3:
            raise ValueError("Alpha v2 requires exactly three taker scenarios.")
        if any(scenario.order_role != "TAKER" for scenario in EXECUTABLE_SCENARIOS):
            raise ValueError("Alpha v2 runner cannot execute maker scenarios.")
        expected_roles = (
            "DEPLOYABILITY_BASELINE",
            "DEPLOYABILITY_STRESS",
            "VENUE_SENSITIVITY_ONLY",
        )
        if tuple(scenario.evidence_role for scenario in EXECUTABLE_SCENARIOS) != (
            expected_roles
        ):
            raise ValueError("Alpha v2 venue evidence roles changed.")

    @staticmethod
    def _validate_locked_development(locked):
        if locked.manifest_sha256 != DEVELOPMENT_MANIFEST_SHA256:
            raise ValueError("Alpha v2 manifest SHA-256 is invalid.")
        if locked.attribution_report_sha256 != RECORDED_ATTRIBUTION_REPORT_SHA256:
            raise ValueError("Alpha v2 attribution SHA-256 is invalid.")
        if locked.configuration != alpha_development_configuration():
            raise ValueError("Locked Alpha v2 configuration changed.")
        expected_assets = ("BTC-USD", "ETH-USD")
        if (
            locked.contract.dataset_id
            != "coinbase-exchange-btc-eth-native-6h-20190101-20260801-v1"
            or locked.contract.timeframe != "6h"
            or tuple(locked.contract.products) != expected_assets
            or tuple(sorted(locked.assets)) != expected_assets
        ):
            raise ValueError("Locked Alpha v2 dataset scope is invalid.")
        if tuple(locked.strategy_engines) != VARIANT_ORDER:
            raise ValueError("Locked Alpha v2 variant order changed.")
        expected_engines = alpha_development_strategy_engines()
        for variant_id, engine in locked.strategy_engines.items():
            expected = expected_engines[variant_id]
            if (
                engine.strategy_name != expected.strategy_name
                or engine.strategy.configuration()
                != expected.strategy.configuration()
            ):
                raise ValueError("Locked Alpha v2 strategy identity changed.")

    @staticmethod
    def _validate_evaluation(result, strategy_name, protective_policy):
        if not isinstance(result, dict):
            raise TypeError("Multi-asset validator must return a dictionary.")
        if result.get("strategy") != strategy_name:
            raise ValueError("Alpha v2 evaluation strategy identity is invalid.")
        if result.get("asset_count") != 2:
            raise ValueError("Alpha v2 evaluation asset count is invalid.")
        assets = result.get("assets")
        if not isinstance(assets, dict) or tuple(sorted(assets)) != (
            "BTC-USD",
            "ETH-USD",
        ):
            raise ValueError("Alpha v2 evaluation asset scope is invalid.")
        classification = result.get("classification", {})
        if classification.get("status") not in ALLOWED_VALIDATION_STATUSES:
            raise ValueError("Alpha v2 aggregate classification is invalid.")
        expected_policy = protective_policy.as_dict()
        for asset_name, asset_result in assets.items():
            if asset_result.get("strategy") != strategy_name:
                raise ValueError(
                    f"Alpha v2 strategy identity is invalid for {asset_name}."
                )
            if asset_result.get("classification", {}).get("status") not in (
                ALLOWED_VALIDATION_STATUSES
            ):
                raise ValueError(
                    f"Alpha v2 asset classification is invalid for {asset_name}."
                )
            oos = asset_result.get("out_of_sample", {})
            for partition in ("in_sample", "out_of_sample"):
                if oos.get(partition, {}).get("protective_exit_policy") != (
                    expected_policy
                ):
                    raise ValueError(
                        "Alpha v2 evaluation did not activate the exact "
                        f"protective policy for {asset_name}."
                    )
            for window in asset_result.get("walk_forward", {}).get("windows", []):
                for partition in ("train", "test"):
                    if window.get(partition, {}).get(
                        "protective_exit_policy"
                    ) != expected_policy:
                        raise ValueError(
                            "Alpha v2 walk-forward evidence lost the exact "
                            f"protective policy for {asset_name}."
                        )

    def _evaluate_scenario(self, engine, assets, scenario):
        configuration = alpha_development_evaluation_configuration()
        risk_engine = self.risk_engine_factory()
        protective_policy = self.protective_exit_policy_factory()
        kwargs = configuration.validator_kwargs(scenario)
        kwargs.update(
            {
                "risk_engine": risk_engine,
                "protective_exit_policy": protective_policy,
            }
        )
        result = self.validator_factory(engine, **kwargs).run(assets)
        self._validate_evaluation(
            result,
            engine.strategy_name,
            protective_policy,
        )
        return result, compact_multi_asset_evaluation(result), protective_policy

    @staticmethod
    def _oos_operational_summary(asset_result, expected_policy):
        try:
            oos = asset_result["out_of_sample"]
            split = oos["split"]
            partition = oos["out_of_sample"]
            trades = partition["trade_history"]
            initial_capital = _finite_float(
                partition["initial_capital"], "Initial capital"
            )
            start = pd.Timestamp(split["out_of_sample_start"])
            end = pd.Timestamp(split["out_of_sample_end"])
        except (KeyError, TypeError, ValueError) as exc:
            raise ValueError("Alpha v2 raw OOS evidence is incomplete.") from exc
        if initial_capital <= 0.0 or not isinstance(trades, list):
            raise ValueError("Alpha v2 OOS capital or trades are invalid.")
        seconds = (end - start).total_seconds() + 21600.0
        years = seconds / (365.25 * 24.0 * 3600.0)
        if not math.isfinite(years) or years <= 0.0:
            raise ValueError("Alpha v2 OOS duration is invalid.")

        round_trip_notional = 0.0
        total_costs = 0.0
        exit_reason_counts = {
            "SIGNAL": 0,
            "PROTECTIVE_STOP": 0,
            "PROTECTIVE_TARGET": 0,
            "TERMINAL_FORCE_CLOSE": 0,
        }
        protective_exit_count = 0
        for trade in trades:
            if not isinstance(trade, dict):
                raise ValueError("Every Alpha v2 OOS trade must be a dictionary.")
            shares = _finite_float(trade.get("shares"), "Trade shares")
            entry_price = _finite_float(
                trade.get("entry_price"), "Trade entry price"
            )
            exit_price = _finite_float(
                trade.get("exit_price"), "Trade exit price"
            )
            costs = _finite_float(trade.get("total_costs"), "Trade total costs")
            if shares <= 0.0 or entry_price <= 0.0 or exit_price <= 0.0:
                raise ValueError("Alpha v2 trade execution evidence must be positive.")
            if costs < 0.0:
                raise ValueError("Alpha v2 trade costs cannot be negative.")
            round_trip_notional += shares * (entry_price + exit_price)
            total_costs += costs
            reason = trade.get("exit_reason")
            if reason not in exit_reason_counts:
                raise ValueError("Alpha v2 trade exit reason is invalid.")
            exit_reason_counts[reason] += 1
            protective_exit_count += int(
                trade.get("protective_exit_executed") is True
            )
        turnover_multiple = round_trip_notional / initial_capital
        cost_fraction = total_costs / initial_capital
        return {
            "oos_years": years,
            "trade_count": len(trades),
            "round_trip_executed_notional": round_trip_notional,
            "round_trip_notional_multiple_of_initial_capital": (
                turnover_multiple
            ),
            "annualized_round_trip_notional_multiple": (
                turnover_multiple / years
            ),
            "total_costs": total_costs,
            "cost_fraction_of_initial_capital": cost_fraction,
            "annualized_cost_fraction_of_initial_capital": (
                cost_fraction / years
            ),
            "exit_reason_counts": exit_reason_counts,
            "protective_exit_count": protective_exit_count,
            "protective_policy_active": (
                partition.get("protective_exit_policy") == expected_policy
            ),
        }

    @classmethod
    def _operational_assets(cls, raw, policy):
        expected_policy = policy.as_dict()
        return {
            asset_name: cls._oos_operational_summary(
                asset_result, expected_policy
            )
            for asset_name, asset_result in sorted(raw["assets"].items())
        }

    @staticmethod
    def _review_variant(profile_evidence, configuration):
        baseline = profile_evidence[BASELINE_COSTS.label]
        stress = profile_evidence[STRESSED_COSTS.label]
        gated_profiles = (baseline, stress)
        assets = ("BTC-USD", "ETH-USD")
        budget = configuration["turnover_cost_budget"]
        evaluation = configuration["evaluation"]

        gates = {
            "baseline_multi_asset_validated": (
                baseline["evaluation"]["classification"]["status"]
                == "VALIDATED"
            ),
            "cost_stress_multi_asset_validated": (
                stress["evaluation"]["classification"]["status"]
                == "VALIDATED"
            ),
            "baseline_positive_oos_return_both_assets": all(
                baseline["summary"][asset]["oos_strategy_return"] > 0.0
                for asset in assets
            ),
            "minimum_walk_forward_windows": all(
                profile["summary"][asset]["walk_forward_window_count"]
                >= evaluation["min_walk_forward_windows"]
                for profile in gated_profiles
                for asset in assets
            ),
            "minimum_development_trades_per_asset": all(
                profile["summary"][asset][
                    "unseen_walk_forward_trade_count"
                ] >= evaluation["min_unseen_trades_per_asset"]
                for profile in gated_profiles
                for asset in assets
            ),
            "oos_drawdown_within_limit": all(
                profile["summary"][asset]["oos_max_drawdown_percent"]
                <= evaluation["max_oos_drawdown_percent"]
                for profile in gated_profiles
                for asset in assets
            ),
            "annual_turnover_within_budget": all(
                baseline["operational_assets"][asset][
                    "annualized_round_trip_notional_multiple"
                ]
                <= budget["annual_total_executed_notional_multiple_maximum"]
                for asset in assets
            ),
            "annual_baseline_cost_within_budget": all(
                baseline["operational_assets"][asset][
                    "annualized_cost_fraction_of_initial_capital"
                ]
                <= budget[
                    "annual_baseline_cost_fraction_of_initial_capital_maximum"
                ]
                for asset in assets
            ),
            "protective_exit_policy_active_all_scenarios": all(
                profile["operational_assets"][asset][
                    "protective_policy_active"
                ]
                for profile in profile_evidence.values()
                for asset in assets
            ),
        }
        baseline_status = baseline["evaluation"]["classification"]["status"]
        stress_status = stress["evaluation"]["classification"]["status"]
        hard_screen_out = (
            "REJECTED" in {baseline_status, stress_status}
            or not gates["oos_drawdown_within_limit"]
            or not gates["annual_turnover_within_budget"]
            or not gates["annual_baseline_cost_within_budget"]
            or not gates["protective_exit_policy_active_all_scenarios"]
        )
        if hard_screen_out:
            outcome = "SCREEN_OUT"
        elif all(gates.values()):
            outcome = "MECHANISM_RETAINS_DEVELOPMENT_INTEREST"
        else:
            outcome = "INCONCLUSIVE"
        return {
            "outcome": outcome,
            "gates": gates,
            "failed_gates": [name for name, passed in gates.items() if not passed],
            "thresholds": {
                "min_walk_forward_windows": evaluation[
                    "min_walk_forward_windows"
                ],
                "min_development_trades_per_asset": evaluation[
                    "min_unseen_trades_per_asset"
                ],
                "max_oos_drawdown_percent": evaluation[
                    "max_oos_drawdown_percent"
                ],
                **budget,
            },
            "development_interest_is_formal_validation": False,
            "candidate_v2_authorized": False,
            "bounded_forward_paper_authorized": False,
            "live_execution_authorized": False,
        }

    @staticmethod
    def _comparison(variant_evidence):
        outcome_counts = {outcome: 0 for outcome in DEVELOPMENT_OUTCOMES}
        retaining_interest = []
        variants = {}
        for variant_id in VARIANT_ORDER:
            evidence = variant_evidence[variant_id]
            outcome = evidence["development_review"]["outcome"]
            outcome_counts[outcome] += 1
            if outcome == "MECHANISM_RETAINS_DEVELOPMENT_INTEREST":
                retaining_interest.append(variant_id)
            variants[variant_id] = {
                "outcome": outcome,
                "gates": evidence["development_review"]["gates"],
                "failed_gates": evidence["development_review"][
                    "failed_gates"
                ],
                "scenarios": {
                    label: {
                        "aggregate_classification": profile["evaluation"][
                            "classification"
                        ]["status"],
                        "assets": profile["summary"],
                        "operational_assets": profile[
                            "operational_assets"
                        ],
                    }
                    for label, profile in evidence["profiles"].items()
                },
            }
        return {
            "variant_order": list(VARIANT_ORDER),
            "comparison_mode": "FIXED_CAUSAL_ABLATION_NOT_RANKING",
            "automatic_ranking_generated": False,
            "automatic_strategy_selection": False,
            "selected_variant": None,
            "outcome_counts": outcome_counts,
            "mechanisms_retaining_interest": retaining_interest,
            "variants": variants,
        }

    def run(self, manifest_path, attribution_report_path):
        self._assert_not_previously_executed()
        self._validate_scenarios()
        locked = self.preregistration.lock(
            manifest_path, attribution_report_path
        )
        self._validate_locked_development(locked)
        configuration = alpha_development_configuration()

        variant_evidence = {}
        for variant_id in VARIANT_ORDER:
            engine = locked.strategy_engines[variant_id]
            profiles = {}
            for scenario in EXECUTABLE_SCENARIOS:
                raw, compact, policy = self._evaluate_scenario(
                    engine, locked.assets, scenario
                )
                profiles[scenario.label] = {
                    "scenario": scenario.as_dict(),
                    "evaluation": compact,
                    "summary": {
                        asset_name: profile_summary(asset_result)
                        for asset_name, asset_result in sorted(
                            compact["assets"].items()
                        )
                    },
                    "operational_assets": self._operational_assets(raw, policy),
                }
            variant_evidence[variant_id] = {
                "strategy_identity": engine.strategy.configuration(),
                "profiles": profiles,
                "development_review": self._review_variant(
                    profiles, configuration
                ),
            }

        comparison = self._comparison(variant_evidence)
        payload = {
            "schema_version": ALPHA_DEVELOPMENT_REPORT_SCHEMA_VERSION,
            "status": "ALPHA_DEVELOPMENT_COMPLETED",
            "alpha_development_id": ALPHA_DEVELOPMENT_ID,
            "development_type": "FIXED_JOINT_CAUSAL_ABLATION",
            "manifest_sha256": locked.manifest_sha256,
            "attribution_report_sha256": locked.attribution_report_sha256,
            "dataset_contract": locked.contract.as_dict(),
            "dataset_role": "INSPECTED_DEVELOPMENT_ONLY",
            "development_data_only": True,
            "variant_order": list(VARIANT_ORDER),
            "variant_count": len(VARIANT_ORDER),
            "scenario_order": list(SCENARIO_ORDER),
            "scenario_count": len(SCENARIO_ORDER),
            "joint_multi_asset_evaluations": (
                len(VARIANT_ORDER) * len(SCENARIO_ORDER)
            ),
            "configuration": configuration,
            "interpretation_policy": alpha_development_interpretation_policy(),
            "venue_execution_policy": venue_execution_policy(),
            "variant_evidence": variant_evidence,
            "comparison": comparison,
            "joint_development_evaluation_executed": True,
            "protective_exit_engine_active": True,
            "parameter_sweep_executed": False,
            "parameter_calibration_executed": False,
            "automatic_ranking_generated": False,
            "automatic_strategy_selection": False,
            "selected_variant": None,
            "formal_candidate_evaluation": False,
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

        return RecordedAlphaDevelopment(
            report_path=self.output_directory / REPORT_FILENAME,
            checksum_path=self.output_directory / CHECKSUM_FILENAME,
            report_sha256=report_sha256,
            outcome_counts=comparison["outcome_counts"],
            mechanisms_retaining_interest=tuple(
                comparison["mechanisms_retaining_interest"]
            ),
            joint_multi_asset_evaluations=(
                len(VARIANT_ORDER) * len(SCENARIO_ORDER)
            ),
        )


def main(argv=None):
    parser = argparse.ArgumentParser(
        description=(
            "Execute and atomically record the frozen Alpha Development v2 "
            "joint-mechanism evaluation once."
        )
    )
    parser.add_argument("--manifest", required=True)
    parser.add_argument("--attribution-report", required=True)
    args = parser.parse_args(argv)
    recorded = AlphaDevelopmentRunner().run(
        args.manifest, args.attribution_report
    )
    print(json.dumps(recorded.as_dict(), indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
