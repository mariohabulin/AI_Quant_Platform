"""Research-only EMA 20/50 sensitivity study across native candle timeframes."""

import argparse
from dataclasses import dataclass, replace
import hashlib
import json
from pathlib import Path

try:
    from coinbase_research_dataset import (
        FIRST_CANDIDATE_DATASET_CONTRACT,
        CoinbaseResearchDatasetBuilder,
        CoinbaseResearchDatasetContract,
        CoinbaseResearchDatasetLock,
    )
    from first_strategy_candidate import (
        BASELINE_COSTS,
        CANDIDATE_ID,
        STRESSED_COSTS,
        STRATEGY_NAME,
        first_candidate_configuration,
        first_candidate_strategy_engine,
    )
    from multi_asset import MultiAssetValidator
    from research_evidence import canonical_json_bytes
    from calendar_validation import CALENDAR_WINDOWING, CalendarMultiAssetValidator
    from sparse_coinbase_research_dataset import (
        SPARSE_NATIVE_GAP_POLICY,
        SparseCoinbaseResearchDatasetBuilder,
        SparseCoinbaseResearchDatasetLock,
    )
except ImportError:  # package import when src is not placed directly on sys.path
    from src.coinbase_research_dataset import (
        FIRST_CANDIDATE_DATASET_CONTRACT,
        CoinbaseResearchDatasetBuilder,
        CoinbaseResearchDatasetContract,
        CoinbaseResearchDatasetLock,
    )
    from src.first_strategy_candidate import (
        BASELINE_COSTS,
        CANDIDATE_ID,
        STRESSED_COSTS,
        STRATEGY_NAME,
        first_candidate_configuration,
        first_candidate_strategy_engine,
    )
    from src.multi_asset import MultiAssetValidator
    from src.research_evidence import canonical_json_bytes
    from src.calendar_validation import (
        CALENDAR_WINDOWING,
        CalendarMultiAssetValidator,
    )
    from src.sparse_coinbase_research_dataset import (
        SPARSE_NATIVE_GAP_POLICY,
        SparseCoinbaseResearchDatasetBuilder,
        SparseCoinbaseResearchDatasetLock,
    )


STUDY_SCHEMA_VERSION = 2
STUDY_ID = "ema-20-50-btc-eth-timeframe-sensitivity-v1"
TIMEFRAME_ORDER = ("1h", "6h", "1d")
BASELINE_REFERENCE_TIMEFRAME = "6h"
EXPLORATORY_TIMEFRAMES = ("1h", "1d")
STUDY_DIRECTORY_NAME = "study_v1"
STAGING_DIRECTORY_NAME = ".study_v1.staging"
REPORT_FILENAME = "timeframe_sensitivity_report.json"
CHECKSUM_FILENAME = "timeframe_sensitivity_report.sha256"
DEFAULT_OUTPUT_ROOT = Path("data/research/timeframe_sensitivity_v1")
FIRST_CANDIDATE_MANIFEST_SHA256 = (
    "6506dd2700b983a134a132890ef4c4ae6e84c0918ba65a5abff6ab2c204c4e7f"
)
FIRST_CANDIDATE_REPORT_SHA256 = (
    "6b79d0932ee334574ffdbef1aca73c8b900ab8fcb8fbafb857bdd327d38d547c"
)


@dataclass(frozen=True)
class TimeframeStudySpec:
    """One native timeframe with calendar-equivalent validation windows."""

    timeframe: str
    contract: CoinbaseResearchDatasetContract
    train_size: int
    test_size: int
    step_size: int
    source: str

    @property
    def train_duration_days(self):
        return (
            self.train_size * self.contract.granularity_seconds
        ) // 86400

    @property
    def test_duration_days(self):
        return (
            self.test_size * self.contract.granularity_seconds
        ) // 86400

    @property
    def step_duration_days(self):
        return (
            self.step_size * self.contract.granularity_seconds
        ) // 86400

    @property
    def nominal_ema_horizons_hours(self):
        bar_hours = self.contract.granularity_seconds / 3600.0
        return {
            "fast": 20 * bar_hours,
            "slow": 50 * bar_hours,
        }

    def as_dict(self):
        return {
            "timeframe": self.timeframe,
            "source": self.source,
            "contract": self.contract.as_dict(),
            "train_size": self.train_size,
            "test_size": self.test_size,
            "step_size": self.step_size,
            "train_duration_days": self.train_duration_days,
            "test_duration_days": self.test_duration_days,
            "step_duration_days": self.step_duration_days,
            "nominal_ema_horizons_hours": self.nominal_ema_horizons_hours,
        }


def _study_contract(timeframe, granularity_seconds):
    version = (
        "timeframe-study-v1-gap-aware-v2"
        if timeframe == "1h"
        else "timeframe-study-v1"
    )
    observation = "observed-native" if timeframe == "1h" else "native"
    return CoinbaseResearchDatasetContract(
        dataset_id=(
            f"coinbase-exchange-btc-eth-{observation}-"
            f"{timeframe}-20190101-20260801-{version}"
        ),
        products=("BTC-USD", "ETH-USD"),
        granularity_seconds=granularity_seconds,
        start="2019-01-01T00:00:00Z",
        end="2026-08-01T00:00:00Z",
    )


TIMEFRAME_SPECS = {
    "1h": TimeframeStudySpec(
        timeframe="1h",
        contract=_study_contract("1h", 3600),
        train_size=17280,
        test_size=4320,
        step_size=4320,
        source="NEW_EXPLORATORY_EVALUATION",
    ),
    "6h": TimeframeStudySpec(
        timeframe="6h",
        contract=FIRST_CANDIDATE_DATASET_CONTRACT,
        train_size=2880,
        test_size=720,
        step_size=720,
        source="RECORDED_CANDIDATE_V1_REFERENCE",
    ),
    "1d": TimeframeStudySpec(
        timeframe="1d",
        contract=_study_contract("1d", 86400),
        train_size=720,
        test_size=180,
        step_size=180,
        source="NEW_EXPLORATORY_EVALUATION",
    ),
}


def timeframe_study_configuration(timeframe):
    if timeframe not in TIMEFRAME_SPECS:
        raise ValueError("Unsupported study timeframe.")
    spec = TIMEFRAME_SPECS[timeframe]
    return replace(
        first_candidate_configuration(),
        train_size=spec.train_size,
        test_size=spec.test_size,
        step_size=spec.step_size,
    )


def timeframe_study_strategy_engine():
    return first_candidate_strategy_engine()


def study_declaration():
    return {
        "schema_version": STUDY_SCHEMA_VERSION,
        "status": "TIMEFRAME_STUDY_DECLARED",
        "study_id": STUDY_ID,
        "study_type": "EXPLORATORY_DEVELOPMENT_EVIDENCE",
        "strategy_name": STRATEGY_NAME,
        "same_nominal_ema_periods": {"fast": 20, "slow": 50},
        "timeframes": list(TIMEFRAME_ORDER),
        "exploratory_timeframes": list(EXPLORATORY_TIMEFRAMES),
        "reference_timeframe": BASELINE_REFERENCE_TIMEFRAME,
        "specifications": {
            timeframe: TIMEFRAME_SPECS[timeframe].as_dict()
            for timeframe in TIMEFRAME_ORDER
        },
        "comparison_rule": (
            "Use equal 720-day train and 180-day non-overlapping test durations; "
            "report fixed-order evidence without ranking or winner selection."
        ),
        "one_hour_gap_policy": dict(SPARSE_NATIVE_GAP_POLICY),
        "one_hour_windowing": CALENDAR_WINDOWING,
        "development_data_only": True,
        "candidate_v1_reopened": False,
        "automatic_timeframe_selection": False,
        "formal_candidate_evaluation": False,
        "evaluation_executed": False,
        "candidate_v2_authorized": False,
        "optimization_authorized": False,
        "bounded_forward_paper_review_eligible": False,
        "bounded_forward_paper_authorized": False,
        "live_execution_authorized": False,
    }


def acquire_timeframe_dataset(
    timeframe,
    output_directory,
    builder_factory=None,
):
    if timeframe == BASELINE_REFERENCE_TIMEFRAME:
        raise ValueError(
            "The recorded 6h reference must be reused; refusing duplicate acquisition."
        )
    if timeframe not in EXPLORATORY_TIMEFRAMES:
        raise ValueError("Unsupported study timeframe.")
    if builder_factory is None:
        builder_factory = (
            SparseCoinbaseResearchDatasetBuilder
            if timeframe == "1h"
            else CoinbaseResearchDatasetBuilder
        )
    builder = builder_factory(TIMEFRAME_SPECS[timeframe].contract)
    return builder.build(output_directory, overwrite=False)


@dataclass(frozen=True)
class RecordedTimeframeSensitivityStudy:
    report_path: Path
    checksum_path: Path
    report_sha256: str
    status: str = "TIMEFRAME_STUDY_RECORDED"

    def as_dict(self):
        return {
            "status": self.status,
            "report_path": str(self.report_path),
            "checksum_path": str(self.checksum_path),
            "report_sha256": self.report_sha256,
            "candidate_v1_reopened": False,
            "automatic_timeframe_selection": False,
            "formal_candidate_evaluation": False,
            "exploratory_evaluation_executed": True,
            "candidate_v2_authorized": False,
            "optimization_authorized": False,
            "bounded_forward_paper_review_eligible": False,
            "bounded_forward_paper_authorized": False,
            "live_execution_authorized": False,
        }


class TimeframeSensitivityStudyRunner:
    """Record one exploratory 1h/6h/1d comparison without promotion logic."""

    def __init__(
        self,
        output_root=DEFAULT_OUTPUT_ROOT,
        reference_report_sha256=FIRST_CANDIDATE_REPORT_SHA256,
        dataset_locker_factory=CoinbaseResearchDatasetLock,
        sparse_dataset_locker_factory=None,
        validator_factory=MultiAssetValidator,
        calendar_validator_factory=None,
        strategy_engine_factory=timeframe_study_strategy_engine,
    ):
        self.output_root = Path(output_root)
        self.output_directory = self.output_root / STUDY_DIRECTORY_NAME
        self.staging_directory = self.output_root / STAGING_DIRECTORY_NAME
        self.reference_report_sha256 = reference_report_sha256
        self.dataset_locker_factory = dataset_locker_factory
        self.sparse_dataset_locker_factory = sparse_dataset_locker_factory
        if self.sparse_dataset_locker_factory is None:
            self.sparse_dataset_locker_factory = (
                SparseCoinbaseResearchDatasetLock
                if dataset_locker_factory is CoinbaseResearchDatasetLock
                else dataset_locker_factory
            )
        self.validator_factory = validator_factory
        self.calendar_validator_factory = calendar_validator_factory
        if self.calendar_validator_factory is None:
            self.calendar_validator_factory = (
                CalendarMultiAssetValidator
                if validator_factory is MultiAssetValidator
                else validator_factory
            )
        self.strategy_engine_factory = strategy_engine_factory

    def _assert_not_previously_executed(self):
        if self.output_directory.exists():
            raise FileExistsError(
                "Timeframe sensitivity evidence already exists; refusing to overwrite "
                "or repeat the study."
            )
        if self.staging_directory.exists():
            raise FileExistsError(
                "An incomplete timeframe sensitivity staging directory exists; "
                "review it before any retry."
            )

    @staticmethod
    def _validate_manifest_scope(manifest_paths):
        if not isinstance(manifest_paths, dict):
            raise TypeError("Manifest paths must be a timeframe mapping.")
        if set(manifest_paths) != set(EXPLORATORY_TIMEFRAMES):
            raise ValueError("Manifest paths must contain exactly 1h and 1d.")

    def _load_reference_report(self, report_path):
        report_path = Path(report_path)
        report_bytes = report_path.read_bytes()
        digest = hashlib.sha256(report_bytes).hexdigest()
        if digest != self.reference_report_sha256:
            raise ValueError(
                "Reference SHA-256 does not match the exact frozen candidate-v1 report."
            )
        sidecar_path = report_path.with_name("evaluation_report.sha256")
        expected_sidecar = f"{digest}  evaluation_report.json\n".encode("ascii")
        if not sidecar_path.is_file() or sidecar_path.read_bytes() != expected_sidecar:
            raise ValueError("Candidate-v1 evaluation report sidecar is invalid.")
        try:
            payload = json.loads(report_bytes.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise ValueError("Candidate-v1 reference report is not valid JSON.") from exc

        candidate = payload.get("candidate")
        expected_identity = {
            "candidate_id": CANDIDATE_ID,
            "strategy_name": STRATEGY_NAME,
            "timeframe": "6h",
            "assets": ["BTC-USD", "ETH-USD"],
        }
        if not isinstance(candidate, dict) or any(
            candidate.get(key) != value for key, value in expected_identity.items()
        ):
            raise ValueError("Candidate-v1 reference report candidate identity is invalid.")
        if payload.get("status") != "EVALUATION_COMPLETED":
            raise ValueError("Candidate-v1 reference evaluation is not complete.")
        if payload.get("manifest_sha256") != FIRST_CANDIDATE_MANIFEST_SHA256:
            raise ValueError("Candidate-v1 reference manifest identity is invalid.")
        if payload.get("configuration") != timeframe_study_configuration("6h").as_dict():
            raise ValueError("Candidate-v1 reference configuration is invalid.")
        protocol_report = payload.get("protocol_report")
        if (
            not isinstance(protocol_report, dict)
            or protocol_report.get("status") != "REJECTED"
            or "baseline_evaluation" not in protocol_report
            or "cost_stress_evaluation" not in protocol_report
        ):
            raise ValueError("Candidate-v1 reference protocol evidence is invalid.")
        for flag in (
            "optimization_authorized",
            "bounded_forward_paper_review_eligible",
            "bounded_forward_paper_authorized",
            "live_execution_authorized",
        ):
            if payload.get(flag) is not False:
                raise ValueError("Candidate-v1 reference authorization boundary is invalid.")
        return payload, digest

    def _lock_exploratory_datasets(self, manifest_paths):
        locked = {}
        for timeframe in EXPLORATORY_TIMEFRAMES:
            spec = TIMEFRAME_SPECS[timeframe]
            locker_factory = (
                self.sparse_dataset_locker_factory
                if timeframe == "1h"
                else self.dataset_locker_factory
            )
            dataset = locker_factory(spec.contract).lock(
                manifest_paths[timeframe]
            )
            if dataset.contract != spec.contract:
                raise ValueError("Locked dataset contract does not match the study spec.")
            if tuple(sorted(dataset.assets)) != spec.contract.products:
                raise ValueError("Locked dataset assets do not match the study scope.")
            locked[timeframe] = dataset
        return locked

    def _evaluate_profile(self, timeframe, assets, configuration, costs):
        validator_factory = self.validator_factory
        validator_kwargs = configuration.validator_kwargs(costs)
        if timeframe == "1h":
            spec = TIMEFRAME_SPECS[timeframe]
            validator_factory = self.calendar_validator_factory
            validator_kwargs.update(
                calendar_start=spec.contract.start,
                calendar_end=spec.contract.end,
                granularity_seconds=spec.contract.granularity_seconds,
            )
        validator = validator_factory(
            self.strategy_engine_factory(),
            **validator_kwargs,
        )
        return validator.run(assets)

    @staticmethod
    def _dataset_gap_evidence(dataset):
        manifest = dataset.manifest
        asset_keys = (
            "expected_rows",
            "rows",
            "missing_rows",
            "missing_timestamps",
            "max_consecutive_missing_buckets",
            "recovery_status",
        )
        return {
            "gap_policy": manifest["gap_policy"],
            "assets": {
                product_id: {
                    key: manifest["assets"][product_id][key]
                    for key in asset_keys
                }
                for product_id in sorted(manifest["assets"])
            },
        }

    @staticmethod
    def _compact_backtest_run(result):
        retained = {}
        for key in (
            "initial_capital",
            "final_capital",
            "performance",
            "comparison",
            "benchmark",
            "execution_timing",
        ):
            if key in result:
                retained[key] = result[key]
        return retained

    @classmethod
    def _compact_oos_evidence(cls, result):
        retained = {}
        for key in ("split", "generalization"):
            if key in result:
                retained[key] = result[key]
        for key in ("in_sample", "out_of_sample"):
            if key in result:
                retained[key] = cls._compact_backtest_run(result[key])
        return retained

    @classmethod
    def _compact_walk_forward_evidence(cls, result):
        windows = []
        unseen_trade_count = 0
        for window in result["windows"]:
            compact_window = {
                key: value
                for key, value in window.items()
                if key not in {"train", "test"}
            }
            for segment in ("train", "test"):
                if segment in window:
                    compact_window[segment] = cls._compact_backtest_run(
                        window[segment]
                    )
            unseen_trade_count += len(
                window.get("test", {}).get("trade_history", [])
            )
            windows.append(compact_window)
        return {
            "configuration": result.get("configuration"),
            "summary": result["summary"],
            "unseen_trade_count": unseen_trade_count,
            "windows": windows,
        }

    @classmethod
    def _compact_evaluation(cls, result):
        raw_bytes = canonical_json_bytes(result)
        assets = {}
        for asset_name, asset_result in sorted(result["assets"].items()):
            assets[asset_name] = {
                "strategy": asset_result["strategy"],
                "classification": asset_result["classification"],
                "out_of_sample": cls._compact_oos_evidence(
                    asset_result["out_of_sample"]
                ),
                "walk_forward": cls._compact_walk_forward_evidence(
                    asset_result["walk_forward"]
                ),
                "falsification": asset_result["falsification"],
            }
        return {
            "strategy": result["strategy"],
            "asset_count": result["asset_count"],
            "summary": result["summary"],
            "classification": result["classification"],
            "assets": assets,
            "raw_evaluation_sha256": hashlib.sha256(raw_bytes).hexdigest(),
            "raw_evaluation_canonical_bytes": len(raw_bytes),
            "raw_trade_level_evidence_persisted": False,
        }

    def _new_timeframe_evidence(self, timeframe, dataset):
        configuration = timeframe_study_configuration(timeframe)
        baseline = self._compact_evaluation(
            self._evaluate_profile(
                timeframe,
                dataset.assets,
                configuration,
                BASELINE_COSTS,
            )
        )
        stress = self._compact_evaluation(
            self._evaluate_profile(
                timeframe,
                dataset.assets,
                configuration,
                STRESSED_COSTS,
            )
        )
        evidence = {
            "source": "NEW_EXPLORATORY_EVALUATION",
            "dataset_contract": dataset.contract.as_dict(),
            "manifest_sha256": dataset.manifest_sha256,
            "configuration": configuration.as_dict(),
            "windowing": (
                CALENDAR_WINDOWING
                if timeframe == "1h"
                else "FIXED_ROW_COUNT_CONTINUOUS_GRID"
            ),
            "baseline_evaluation": baseline,
            "cost_stress_evaluation": stress,
        }
        if timeframe == "1h":
            evidence["dataset_gap_evidence"] = self._dataset_gap_evidence(
                dataset
            )
        return evidence

    @classmethod
    def _reference_timeframe_evidence(cls, reference, digest):
        protocol_report = reference["protocol_report"]
        return {
            "source": "RECORDED_CANDIDATE_V1_REFERENCE",
            "reference_report_sha256": digest,
            "recorded_protocol_outcome": protocol_report["status"],
            "dataset_contract": TIMEFRAME_SPECS["6h"].contract.as_dict(),
            "manifest_sha256": reference["manifest_sha256"],
            "configuration": reference["configuration"],
            "baseline_evaluation": cls._compact_evaluation(
                protocol_report["baseline_evaluation"]
            ),
            "cost_stress_evaluation": cls._compact_evaluation(
                protocol_report["cost_stress_evaluation"]
            ),
        }

    @staticmethod
    def _profile_summary(asset_result):
        out_of_sample = asset_result["out_of_sample"]["out_of_sample"]
        comparison = out_of_sample["comparison"]
        performance = out_of_sample["performance"]
        walk_forward = asset_result["walk_forward"]
        falsification = asset_result["falsification"]
        return {
            "validation_classification": asset_result["classification"]["status"],
            "oos_strategy_return": comparison["strategy_return"],
            "oos_benchmark_return": comparison["benchmark_return"],
            "oos_excess_return": comparison["excess_return"],
            "oos_max_drawdown_percent": performance["max_drawdown"],
            "oos_trade_count": performance["number_of_trades"],
            "walk_forward_window_count": walk_forward["summary"]["window_count"],
            "unseen_walk_forward_trade_count": walk_forward[
                "unseen_trade_count"
            ],
            "positive_walk_forward_excess_rate": walk_forward["summary"][
                "positive_test_excess_rate"
            ],
            "passes_statistical_falsification": falsification[
                "passes_statistical_falsification"
            ],
            "bootstrap_ci_lower": falsification["bootstrap"]["ci_lower"],
            "bootstrap_ci_upper": falsification["bootstrap"]["ci_upper"],
            "permutation_p_value": falsification["permutation"]["p_value"],
        }

    @classmethod
    def _comparison(cls, timeframe_evidence):
        comparison = {}
        for timeframe in TIMEFRAME_ORDER:
            evidence = timeframe_evidence[timeframe]
            baseline = evidence["baseline_evaluation"]
            stress = evidence["cost_stress_evaluation"]
            assets = {}
            for asset_name in TIMEFRAME_SPECS[timeframe].contract.products:
                assets[asset_name] = {
                    "baseline": cls._profile_summary(
                        baseline["assets"][asset_name]
                    ),
                    "stress": cls._profile_summary(
                        stress["assets"][asset_name]
                    ),
                }
            comparison[timeframe] = {
                "source": evidence["source"],
                "baseline_aggregate_classification": baseline["classification"][
                    "status"
                ],
                "cost_stress_aggregate_classification": stress["classification"][
                    "status"
                ],
                "assets": assets,
            }
        return {
            "timeframe_order": list(TIMEFRAME_ORDER),
            "selection_policy": "NONE_EXPLORATORY_ONLY",
            "automatic_ranking_generated": False,
            "timeframes": comparison,
        }

    def run(self, manifest_paths, reference_report_path):
        self._assert_not_previously_executed()
        self._validate_manifest_scope(manifest_paths)
        reference, reference_digest = self._load_reference_report(
            reference_report_path
        )
        locked = self._lock_exploratory_datasets(manifest_paths)

        timeframe_evidence = {
            "1h": self._new_timeframe_evidence("1h", locked["1h"]),
            "6h": self._reference_timeframe_evidence(
                reference,
                reference_digest,
            ),
            "1d": self._new_timeframe_evidence("1d", locked["1d"]),
        }
        payload = {
            "schema_version": STUDY_SCHEMA_VERSION,
            "status": "TIMEFRAME_SENSITIVITY_COMPLETED",
            "study_id": STUDY_ID,
            "study_type": "EXPLORATORY_DEVELOPMENT_EVIDENCE",
            "strategy_name": STRATEGY_NAME,
            "same_nominal_ema_periods": {"fast": 20, "slow": 50},
            "timeframe_order": list(TIMEFRAME_ORDER),
            "reference_report_sha256": reference_digest,
            "timeframe_evidence": timeframe_evidence,
            "comparison": self._comparison(timeframe_evidence),
            "development_data_only": True,
            "candidate_v1_reopened": False,
            "automatic_timeframe_selection": False,
            "formal_candidate_evaluation": False,
            "exploratory_evaluation_executed": True,
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

        return RecordedTimeframeSensitivityStudy(
            report_path=self.output_directory / REPORT_FILENAME,
            checksum_path=self.output_directory / CHECKSUM_FILENAME,
            report_sha256=report_sha256,
        )


def _acquisition_summary(timeframe, result):
    return {
        "status": "TIMEFRAME_DATASET_LOCKED",
        "study_id": STUDY_ID,
        "timeframe": timeframe,
        "manifest_path": str(result["manifest_path"]),
        "manifest_sha256": result["manifest_sha256"],
        "checksum_path": str(result["checksum_path"]),
        "assets": result["assets"],
        "evaluation_executed": False,
        "candidate_v2_authorized": False,
        "optimization_authorized": False,
        "bounded_forward_paper_review_eligible": False,
        "bounded_forward_paper_authorized": False,
        "live_execution_authorized": False,
    }


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="Declare, acquire or run Timeframe Sensitivity Study v1."
    )
    subparsers = parser.add_subparsers(dest="command")

    acquire_parser = subparsers.add_parser(
        "acquire",
        help="Acquire one new exploratory native-timeframe dataset.",
    )
    acquire_parser.add_argument(
        "--timeframe",
        required=True,
        choices=EXPLORATORY_TIMEFRAMES,
    )
    acquire_parser.add_argument("--output", required=True)

    run_parser = subparsers.add_parser(
        "run",
        help="Run and record the one-shot research-only comparison.",
    )
    run_parser.add_argument("--manifest-1h", required=True)
    run_parser.add_argument("--manifest-1d", required=True)
    run_parser.add_argument("--reference-report", required=True)

    args = parser.parse_args(argv)
    if args.command == "acquire":
        result = acquire_timeframe_dataset(args.timeframe, args.output)
        output = _acquisition_summary(args.timeframe, result)
    elif args.command == "run":
        recorded = TimeframeSensitivityStudyRunner().run(
            {
                "1h": args.manifest_1h,
                "1d": args.manifest_1d,
            },
            args.reference_report,
        )
        output = recorded.as_dict()
    else:
        output = study_declaration()
    print(json.dumps(output, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
