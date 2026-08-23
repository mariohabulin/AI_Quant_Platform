import hashlib
import json
import os
from pathlib import Path
import sys
from types import SimpleNamespace

import numpy as np
import pandas as pd
import pytest

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src")))

import timeframe_sensitivity_study as study_module
from research_evidence import canonical_json_bytes
from timeframe_sensitivity_study import (
    BASELINE_REFERENCE_TIMEFRAME,
    EXPLORATORY_TIMEFRAMES,
    FIRST_CANDIDATE_REPORT_SHA256,
    REPORT_FILENAME,
    STAGING_DIRECTORY_NAME,
    STUDY_DIRECTORY_NAME,
    STUDY_ID,
    STUDY_SCHEMA_VERSION,
    TIMEFRAME_ORDER,
    TIMEFRAME_SPECS,
    POSITIVE_INFINITY_PROFIT_FACTOR,
    TimeframeSensitivityStudyRunner,
    acquire_timeframe_dataset,
    study_declaration,
    timeframe_study_configuration,
    timeframe_study_strategy_engine,
    main,
)
from calendar_validation import CALENDAR_WINDOWING
from sparse_coinbase_research_dataset import SPARSE_NATIVE_GAP_POLICY


def market_frame(rows=8, frequency="h"):
    index = pd.date_range("2024-01-01", periods=rows, freq=frequency, tz="UTC")
    prices = np.arange(100.0, 100.0 + rows)
    return pd.DataFrame(
        {
            "Open": prices,
            "High": prices + 1.0,
            "Low": prices - 1.0,
            "Close": prices + 0.5,
            "Volume": np.full(rows, 10.0),
        },
        index=index,
    )


def fake_asset_result(status="REJECTED", offset=0.0):
    windows = [
        {
            "test": {
                "trade_history": [
                    {"profit_loss": 1.0 + offset},
                    {"profit_loss": -0.5 + offset},
                ]
            }
        },
        {
            "test": {
                "trade_history": [{"profit_loss": 2.0 + offset}]
            }
        },
    ]
    return {
        "strategy": "ema_crossover",
        "classification": {
            "status": status,
            "gates": {
                "positive_oos_return": False,
                "positive_oos_excess_return": False,
                "passes_statistical_falsification": False,
                "walk_forward_persistence": False,
            },
        },
        "out_of_sample": {
            "out_of_sample": {
                "comparison": {
                    "strategy_return": -0.10 + offset,
                    "benchmark_return": -0.05,
                    "excess_return": -0.05 + offset,
                },
                "performance": {
                    "max_drawdown": 25.0 + offset,
                    "number_of_trades": 2,
                },
            }
        },
        "walk_forward": {
            "summary": {
                "window_count": 2,
                "positive_test_excess_rate": 0.5,
            },
            "windows": windows,
        },
        "falsification": {
            "passes_statistical_falsification": False,
            "bootstrap": {"ci_lower": -2.0, "ci_upper": 3.0},
            "permutation": {"p_value": 0.4},
        },
    }


def fake_evaluation(status="REJECTED", offset=0.0):
    assets = {
        "BTC-USD": fake_asset_result(status, offset),
        "ETH-USD": fake_asset_result(status, offset + 0.01),
    }
    return {
        "strategy": "ema_crossover",
        "asset_count": 2,
        "assets": assets,
        "summary": {
            "mean_oos_strategy_return": -0.1 + offset,
            "mean_oos_excess_return": -0.05 + offset,
            "positive_oos_excess_asset_rate": 0.0,
            "mean_walk_forward_positive_excess_rate": 0.5,
        },
        "classification": {"status": status},
    }


def reference_payload():
    return {
        "schema_version": 1,
        "status": "EVALUATION_COMPLETED",
        "candidate": {
            "candidate_id": "ema-crossover-20-50-btc-eth-native-6h-v1",
            "strategy_name": "ema_crossover",
            "timeframe": "6h",
            "assets": ["BTC-USD", "ETH-USD"],
        },
        "configuration": timeframe_study_configuration("6h").as_dict(),
        "manifest_sha256": (
            "6506dd2700b983a134a132890ef4c4ae6e84c0918ba65a5abff6ab2c204c4e7f"
        ),
        "protocol_report": {
            "status": "REJECTED",
            "baseline_evaluation": fake_evaluation(offset=0.06),
            "cost_stress_evaluation": fake_evaluation(offset=0.07),
        },
        "evaluation_executed": True,
        "optimization_authorized": False,
        "bounded_forward_paper_review_eligible": False,
        "bounded_forward_paper_authorized": False,
        "live_execution_authorized": False,
    }


def write_reference(tmp_path, payload=None):
    payload = reference_payload() if payload is None else payload
    report_directory = tmp_path / "evaluation_v1"
    report_directory.mkdir(parents=True)
    report_path = report_directory / "evaluation_report.json"
    report_bytes = canonical_json_bytes(payload)
    report_path.write_bytes(report_bytes)
    digest = hashlib.sha256(report_bytes).hexdigest()
    report_path.with_name("evaluation_report.sha256").write_bytes(
        f"{digest}  evaluation_report.json\n".encode("ascii")
    )
    return report_path, digest


class FakeLocker:
    calls = []

    def __init__(self, contract):
        self.contract = contract

    def lock(self, manifest_path):
        type(self).calls.append((self.contract, Path(manifest_path)))
        manifest = {}
        if self.contract.timeframe == "1h":
            manifest = {
                "gap_policy": SPARSE_NATIVE_GAP_POLICY,
                "assets": {
                    "BTC-USD": {
                        "expected_rows": 66456,
                        "rows": 66437,
                        "missing_rows": 19,
                        "missing_timestamps": ["2019-04-11T13:00:00Z"],
                        "max_consecutive_missing_buckets": 3,
                        "recovery_status": "exhausted_2_passes",
                    },
                    "ETH-USD": {
                        "expected_rows": 66456,
                        "rows": 66455,
                        "missing_rows": 1,
                        "missing_timestamps": ["2019-04-11T13:00:00Z"],
                        "max_consecutive_missing_buckets": 1,
                        "recovery_status": "exhausted_2_passes",
                    },
                },
            }
        return SimpleNamespace(
            contract=self.contract,
            manifest_sha256=self.contract.timeframe[0] * 64,
            manifest=manifest,
            assets={
                "BTC-USD": market_frame(),
                "ETH-USD": market_frame(),
            },
        )


class FakeValidator:
    calls = []

    def __init__(self, strategy_engine, **kwargs):
        self.strategy_engine = strategy_engine
        self.kwargs = kwargs
        type(self).calls.append(self)

    def run(self, assets):
        assert set(assets) == {"BTC-USD", "ETH-USD"}
        return fake_evaluation(offset=self.kwargs["slippage_rate"])


@pytest.fixture(autouse=True)
def reset_fakes():
    FakeLocker.calls = []
    FakeValidator.calls = []


def runner(tmp_path, reference_hash):
    return TimeframeSensitivityStudyRunner(
        output_root=tmp_path / "timeframe_sensitivity_v1",
        reference_report_sha256=reference_hash,
        dataset_locker_factory=FakeLocker,
        sparse_dataset_locker_factory=FakeLocker,
        validator_factory=FakeValidator,
        calendar_validator_factory=FakeValidator,
    )


def test_declaration_freezes_research_only_scope_without_evaluation():
    declaration = study_declaration()

    assert declaration["status"] == "TIMEFRAME_STUDY_DECLARED"
    assert declaration["schema_version"] == STUDY_SCHEMA_VERSION == 3
    assert declaration["study_id"] == STUDY_ID
    assert declaration["timeframes"] == list(TIMEFRAME_ORDER)
    assert declaration["exploratory_timeframes"] == list(EXPLORATORY_TIMEFRAMES)
    assert declaration["reference_timeframe"] == BASELINE_REFERENCE_TIMEFRAME == "6h"
    assert declaration["same_nominal_ema_periods"] == {"fast": 20, "slow": 50}
    assert declaration["candidate_v1_reopened"] is False
    assert declaration["automatic_timeframe_selection"] is False
    assert declaration["formal_candidate_evaluation"] is False
    assert declaration["one_hour_gap_policy"] == SPARSE_NATIVE_GAP_POLICY
    assert declaration["one_hour_windowing"] == CALENDAR_WINDOWING
    assert declaration["optimization_authorized"] is False
    assert declaration["bounded_forward_paper_review_eligible"] is False
    assert declaration["bounded_forward_paper_authorized"] is False
    assert declaration["live_execution_authorized"] is False


def test_specs_freeze_exact_native_datasets_and_calendar_equivalent_windows():
    assert tuple(TIMEFRAME_SPECS) == TIMEFRAME_ORDER
    assert [TIMEFRAME_SPECS[item].contract.expected_rows_per_product for item in TIMEFRAME_ORDER] == [
        66456,
        11076,
        2769,
    ]
    assert [TIMEFRAME_SPECS[item].train_size for item in TIMEFRAME_ORDER] == [
        17280,
        2880,
        720,
    ]
    assert [TIMEFRAME_SPECS[item].test_size for item in TIMEFRAME_ORDER] == [
        4320,
        720,
        180,
    ]
    assert all(spec.train_duration_days == 720 for spec in TIMEFRAME_SPECS.values())
    assert all(spec.test_duration_days == 180 for spec in TIMEFRAME_SPECS.values())
    assert TIMEFRAME_SPECS["6h"].source == "RECORDED_CANDIDATE_V1_REFERENCE"
    assert TIMEFRAME_SPECS["1h"].source == "NEW_EXPLORATORY_EVALUATION"
    assert TIMEFRAME_SPECS["1d"].source == "NEW_EXPLORATORY_EVALUATION"
    assert TIMEFRAME_SPECS["1h"].contract.dataset_id.endswith(
        "timeframe-study-v1-gap-aware-v2"
    )


def test_configuration_preserves_costs_timing_seed_and_equivalent_windows():
    one_hour = timeframe_study_configuration("1h")
    six_hour = timeframe_study_configuration("6h")
    one_day = timeframe_study_configuration("1d")

    assert (one_hour.train_size, six_hour.train_size, one_day.train_size) == (
        17280,
        2880,
        720,
    )
    assert (one_hour.test_size, six_hour.test_size, one_day.test_size) == (
        4320,
        720,
        180,
    )
    for configuration in (one_hour, six_hour, one_day):
        assert configuration.step_size == configuration.test_size
        assert configuration.execution_timing == "next_bar_open"
        assert configuration.random_seed == 20260822
        assert configuration.baseline_costs.total_rate > 0.0
        assert configuration.stressed_costs.total_rate > configuration.baseline_costs.total_rate

    with pytest.raises(ValueError, match="Unsupported study timeframe"):
        timeframe_study_configuration("15m")


def test_strategy_engine_retains_same_nominal_ema_twenty_fifty():
    engine = timeframe_study_strategy_engine()

    assert engine.strategy_name == "ema_crossover"
    assert engine.strategy.fast_period == 20
    assert engine.strategy.slow_period == 50


def test_acquisition_allows_only_new_exploratory_timeframes(tmp_path):
    calls = []

    class FakeBuilder:
        def __init__(self, contract):
            calls.append(contract)

        def build(self, output_directory, overwrite=False):
            return {
                "manifest_path": Path(output_directory) / "manifest.json",
                "manifest_sha256": "a" * 64,
                "checksum_path": Path(output_directory) / "manifest.sha256",
                "assets": {},
                "overwrite": overwrite,
            }

    result = acquire_timeframe_dataset(
        "1h",
        tmp_path,
        builder_factory=FakeBuilder,
    )

    assert calls == [TIMEFRAME_SPECS["1h"].contract]
    assert result["overwrite"] is False
    with pytest.raises(ValueError, match="recorded 6h reference"):
        acquire_timeframe_dataset("6h", tmp_path, builder_factory=FakeBuilder)
    with pytest.raises(ValueError, match="Unsupported study timeframe"):
        acquire_timeframe_dataset("15m", tmp_path, builder_factory=FakeBuilder)


def test_acquisition_dispatches_sparse_builder_only_for_one_hour(
    monkeypatch,
    tmp_path,
):
    calls = []

    class SparseBuilder:
        def __init__(self, contract):
            calls.append(("sparse", contract.timeframe))

        def build(self, output_directory, overwrite=False):
            return {"builder": "sparse"}

    class ContinuousBuilder:
        def __init__(self, contract):
            calls.append(("continuous", contract.timeframe))

        def build(self, output_directory, overwrite=False):
            return {"builder": "continuous"}

    monkeypatch.setattr(
        study_module,
        "SparseCoinbaseResearchDatasetBuilder",
        SparseBuilder,
    )
    monkeypatch.setattr(
        study_module,
        "CoinbaseResearchDatasetBuilder",
        ContinuousBuilder,
    )

    assert acquire_timeframe_dataset("1h", tmp_path / "1h")["builder"] == "sparse"
    assert acquire_timeframe_dataset("1d", tmp_path / "1d")["builder"] == (
        "continuous"
    )
    assert calls == [("sparse", "1h"), ("continuous", "1d")]


def test_runner_reuses_reference_and_evaluates_only_one_hour_and_one_day(tmp_path):
    reference_path, reference_hash = write_reference(tmp_path)
    recorded = runner(tmp_path, reference_hash).run(
        {"1h": tmp_path / "1h.json", "1d": tmp_path / "1d.json"},
        reference_path,
    )

    assert recorded.status == "TIMEFRAME_STUDY_RECORDED"
    assert recorded.report_path.name == REPORT_FILENAME
    assert len(FakeLocker.calls) == 2
    assert [call[0].timeframe for call in FakeLocker.calls] == ["1h", "1d"]
    assert len(FakeValidator.calls) == 4
    assert [item.kwargs["train_size"] for item in FakeValidator.calls] == [
        17280,
        17280,
        720,
        720,
    ]
    assert all(item.kwargs["execution_timing"] == "next_bar_open" for item in FakeValidator.calls)
    assert ["calendar_start" in item.kwargs for item in FakeValidator.calls] == [
        True,
        True,
        False,
        False,
    ]

    report_bytes = recorded.report_path.read_bytes()
    payload = json.loads(report_bytes)
    assert payload["status"] == "TIMEFRAME_SENSITIVITY_COMPLETED"
    assert set(payload["timeframe_evidence"]) == set(TIMEFRAME_ORDER)
    assert payload["timeframe_order"] == list(TIMEFRAME_ORDER)
    assert payload["timeframe_evidence"]["6h"]["source"] == (
        "RECORDED_CANDIDATE_V1_REFERENCE"
    )
    assert payload["timeframe_evidence"]["1h"]["source"] == (
        "NEW_EXPLORATORY_EVALUATION"
    )
    one_hour = payload["timeframe_evidence"]["1h"]
    assert one_hour["windowing"] == CALENDAR_WINDOWING
    assert one_hour["dataset_gap_evidence"]["gap_policy"] == (
        SPARSE_NATIVE_GAP_POLICY
    )
    assert one_hour["dataset_gap_evidence"]["assets"]["BTC-USD"][
        "missing_rows"
    ] == 19
    assert "dataset_gap_evidence" not in payload["timeframe_evidence"]["1d"]
    assert payload["reference_report_sha256"] == reference_hash
    assert payload["candidate_v1_reopened"] is False
    assert payload["automatic_timeframe_selection"] is False
    assert payload["formal_candidate_evaluation"] is False
    assert payload["exploratory_evaluation_executed"] is True
    assert payload["candidate_v2_authorized"] is False
    assert payload["optimization_authorized"] is False
    assert payload["bounded_forward_paper_review_eligible"] is False
    assert payload["bounded_forward_paper_authorized"] is False
    assert payload["live_execution_authorized"] is False
    assert "winner" not in payload
    assert "ranking" not in payload
    assert b'"trade_history"' not in report_bytes
    assert b'"equity_curve"' not in report_bytes
    compact_baseline = payload["timeframe_evidence"]["1h"][
        "baseline_evaluation"
    ]
    assert len(compact_baseline["raw_evaluation_sha256"]) == 64
    assert compact_baseline["raw_evaluation_canonical_bytes"] > 0
    assert compact_baseline["raw_trade_level_evidence_persisted"] is False

    expected_hash = hashlib.sha256(report_bytes).hexdigest()
    assert recorded.report_sha256 == expected_hash
    assert recorded.checksum_path.read_bytes() == (
        f"{expected_hash}  {REPORT_FILENAME}\n".encode("ascii")
    )


def test_comparison_reports_fixed_order_metrics_without_selecting_winner(tmp_path):
    reference_path, reference_hash = write_reference(tmp_path)
    recorded = runner(tmp_path, reference_hash).run(
        {"1h": tmp_path / "1h.json", "1d": tmp_path / "1d.json"},
        reference_path,
    )
    comparison = json.loads(recorded.report_path.read_bytes())["comparison"]

    assert comparison["timeframe_order"] == list(TIMEFRAME_ORDER)
    assert comparison["selection_policy"] == "NONE_EXPLORATORY_ONLY"
    assert comparison["automatic_ranking_generated"] is False
    btc = comparison["timeframes"]["1h"]["assets"]["BTC-USD"]["baseline"]
    assert btc == {
        "bootstrap_ci_lower": -2.0,
        "bootstrap_ci_upper": 3.0,
        "oos_benchmark_return": -0.05,
        "oos_excess_return": pytest.approx(-0.0495),
        "oos_max_drawdown_percent": pytest.approx(25.0005),
        "oos_strategy_return": pytest.approx(-0.0995),
        "oos_trade_count": 2,
        "passes_statistical_falsification": False,
        "permutation_p_value": 0.4,
        "positive_walk_forward_excess_rate": 0.5,
        "unseen_walk_forward_trade_count": 3,
        "validation_classification": "REJECTED",
        "walk_forward_window_count": 2,
    }


def test_runner_refuses_unknown_manifest_scope_before_any_lock(tmp_path):
    reference_path, reference_hash = write_reference(tmp_path)

    with pytest.raises(ValueError, match="exactly 1h and 1d"):
        runner(tmp_path, reference_hash).run(
            {"1h": tmp_path / "1h.json", "6h": tmp_path / "6h.json"},
            reference_path,
        )

    assert FakeLocker.calls == []
    assert FakeValidator.calls == []


def test_existing_final_or_staging_evidence_refuses_execution_first(tmp_path):
    reference_path, reference_hash = write_reference(tmp_path)
    output_root = tmp_path / "timeframe_sensitivity_v1"
    (output_root / STUDY_DIRECTORY_NAME).mkdir(parents=True)

    with pytest.raises(FileExistsError, match="already exists"):
        runner(tmp_path, reference_hash).run(
            {"1h": tmp_path / "1h.json", "1d": tmp_path / "1d.json"},
            reference_path,
        )

    assert FakeLocker.calls == []
    (output_root / STUDY_DIRECTORY_NAME).rmdir()
    (output_root / STAGING_DIRECTORY_NAME).mkdir()

    with pytest.raises(FileExistsError, match="incomplete"):
        runner(tmp_path, reference_hash).run(
            {"1h": tmp_path / "1h.json", "1d": tmp_path / "1d.json"},
            reference_path,
        )

    assert FakeLocker.calls == []


def test_reference_report_requires_exact_hash_sidecar_and_closed_v1_identity(tmp_path):
    reference_path, reference_hash = write_reference(tmp_path)

    with pytest.raises(ValueError, match="exact frozen candidate-v1 report"):
        runner(tmp_path, "f" * 64).run(
            {"1h": tmp_path / "1h.json", "1d": tmp_path / "1d.json"},
            reference_path,
        )

    reference_path.with_name("evaluation_report.sha256").write_text(
        "bad sidecar\n", encoding="ascii"
    )
    with pytest.raises(ValueError, match="sidecar"):
        runner(tmp_path / "second", reference_hash).run(
            {"1h": tmp_path / "1h.json", "1d": tmp_path / "1d.json"},
            reference_path,
        )

    identity_path, identity_hash = write_reference(
        tmp_path / "identity",
        {
            **reference_payload(),
            "candidate": {
                **reference_payload()["candidate"],
                "timeframe": "1h",
            },
        },
    )
    with pytest.raises(ValueError, match="candidate identity"):
        runner(tmp_path / "third", identity_hash).run(
            {"1h": tmp_path / "1h.json", "1d": tmp_path / "1d.json"},
            identity_path,
        )


def test_non_finite_study_evidence_fails_before_staging(tmp_path):
    reference_path, reference_hash = write_reference(tmp_path)

    class NonFiniteValidator(FakeValidator):
        def run(self, assets):
            result = super().run(assets)
            result["summary"]["bad"] = float("nan")
            return result

    study_runner = TimeframeSensitivityStudyRunner(
        output_root=tmp_path / "non_finite",
        reference_report_sha256=reference_hash,
        dataset_locker_factory=FakeLocker,
        validator_factory=NonFiniteValidator,
    )

    with pytest.raises(ValueError, match="Out of range float values"):
        study_runner.run(
            {"1h": tmp_path / "1h.json", "1d": tmp_path / "1d.json"},
            reference_path,
        )

    assert not (tmp_path / "non_finite" / STUDY_DIRECTORY_NAME).exists()
    assert not (tmp_path / "non_finite" / STAGING_DIRECTORY_NAME).exists()


def test_positive_infinite_profit_factor_is_explicitly_encoded(tmp_path):
    reference_path, reference_hash = write_reference(tmp_path)

    class InfiniteProfitFactorValidator(FakeValidator):
        def run(self, assets):
            result = super().run(assets)
            result["assets"]["BTC-USD"]["walk_forward"]["windows"][0][
                "test"
            ]["performance"] = {
                "number_of_trades": 1,
                "profit_factor": float("inf"),
            }
            return result

    study_runner = TimeframeSensitivityStudyRunner(
        output_root=tmp_path / "positive_infinity",
        reference_report_sha256=reference_hash,
        dataset_locker_factory=FakeLocker,
        sparse_dataset_locker_factory=FakeLocker,
        validator_factory=InfiniteProfitFactorValidator,
        calendar_validator_factory=InfiniteProfitFactorValidator,
    )

    recorded = study_runner.run(
        {"1h": tmp_path / "1h.json", "1d": tmp_path / "1d.json"},
        reference_path,
    )

    payload = json.loads(recorded.report_path.read_bytes())
    baseline = payload["timeframe_evidence"]["1h"]["baseline_evaluation"]
    encoded = baseline["assets"]["BTC-USD"]["walk_forward"]["windows"][0][
        "test"
    ]["performance"]["profit_factor"]
    assert encoded == POSITIVE_INFINITY_PROFIT_FACTOR
    assert baseline["raw_evaluation_encoding"] == {
        "positive_infinite_profit_factor_count": 1,
        "positive_infinite_profit_factor_value": (
            POSITIVE_INFINITY_PROFIT_FACTOR
        ),
    }


def test_negative_infinite_profit_factor_still_fails_before_staging(tmp_path):
    reference_path, reference_hash = write_reference(tmp_path)

    class NegativeInfiniteProfitFactorValidator(FakeValidator):
        def run(self, assets):
            result = super().run(assets)
            result["assets"]["BTC-USD"]["walk_forward"]["windows"][0][
                "test"
            ]["performance"] = {"profit_factor": float("-inf")}
            return result

    study_runner = TimeframeSensitivityStudyRunner(
        output_root=tmp_path / "negative_infinity",
        reference_report_sha256=reference_hash,
        dataset_locker_factory=FakeLocker,
        sparse_dataset_locker_factory=FakeLocker,
        validator_factory=NegativeInfiniteProfitFactorValidator,
        calendar_validator_factory=NegativeInfiniteProfitFactorValidator,
    )

    with pytest.raises(ValueError, match="Out of range float values"):
        study_runner.run(
            {"1h": tmp_path / "1h.json", "1d": tmp_path / "1d.json"},
            reference_path,
        )

    assert not (tmp_path / "negative_infinity" / STUDY_DIRECTORY_NAME).exists()
    assert not (tmp_path / "negative_infinity" / STAGING_DIRECTORY_NAME).exists()


def test_declaration_cli_is_non_activating(capsys):
    assert main([]) == 0
    output = json.loads(capsys.readouterr().out)

    assert output["status"] == "TIMEFRAME_STUDY_DECLARED"
    assert output["evaluation_executed"] is False
    assert output["live_execution_authorized"] is False


def test_run_cli_prints_only_recorded_summary(monkeypatch, tmp_path, capsys):
    class FakeRecorded:
        def as_dict(self):
            return {
                "status": "TIMEFRAME_STUDY_RECORDED",
                "report_sha256": "a" * 64,
                "live_execution_authorized": False,
            }

    class FakeRunner:
        def run(self, manifests, reference_report):
            assert manifests == {
                "1h": str(tmp_path / "1h.json"),
                "1d": str(tmp_path / "1d.json"),
            }
            assert reference_report == str(tmp_path / "reference.json")
            return FakeRecorded()

    monkeypatch.setattr(study_module, "TimeframeSensitivityStudyRunner", FakeRunner)

    assert main(
        [
            "run",
            "--manifest-1h",
            str(tmp_path / "1h.json"),
            "--manifest-1d",
            str(tmp_path / "1d.json"),
            "--reference-report",
            str(tmp_path / "reference.json"),
        ]
    ) == 0
    output = json.loads(capsys.readouterr().out)
    assert output["status"] == "TIMEFRAME_STUDY_RECORDED"
    assert output["live_execution_authorized"] is False


def test_production_reference_hash_remains_exactly_frozen():
    assert FIRST_CANDIDATE_REPORT_SHA256 == (
        "6b79d0932ee334574ffdbef1aca73c8b900ab8fcb8fbafb857bdd327d38d547c"
    )


def test_committed_candidate_v1_report_is_the_exact_accepted_reference(tmp_path):
    report_path = (
        Path(__file__).resolve().parents[1]
        / "data"
        / "research"
        / "first_candidate_v1"
        / "evaluation_v1"
        / "evaluation_report.json"
    )

    payload, digest = TimeframeSensitivityStudyRunner(
        output_root=tmp_path,
    )._load_reference_report(report_path)

    assert digest == FIRST_CANDIDATE_REPORT_SHA256
    assert payload["protocol_report"]["status"] == "REJECTED"
    assert payload["candidate"]["timeframe"] == "6h"

    evidence = TimeframeSensitivityStudyRunner._reference_timeframe_evidence(
        payload,
        digest,
    )
    assert evidence["baseline_evaluation"]["assets"]["BTC-USD"][
        "walk_forward"
    ]["unseen_trade_count"] == 75
    assert evidence["cost_stress_evaluation"]["assets"]["ETH-USD"][
        "walk_forward"
    ]["unseen_trade_count"] == 74
    assert len(evidence["baseline_evaluation"]["raw_evaluation_sha256"]) == 64
    compact_bytes = canonical_json_bytes(evidence)
    assert len(compact_bytes) < 1_000_000
    assert b'"trade_history"' not in compact_bytes
    assert b'"equity_curve"' not in compact_bytes
