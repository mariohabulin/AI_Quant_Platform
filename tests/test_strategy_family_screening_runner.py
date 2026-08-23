import hashlib
import json
import os
import sys
from types import SimpleNamespace
from typing import ClassVar

import numpy as np
import pandas as pd
import pytest

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src")))

import strategy_family_screening_runner as runner_module
from first_strategy_candidate import BASELINE_COSTS, STRESSED_COSTS
from research_evidence import canonical_json_bytes
from research_evidence_compaction import POSITIVE_INFINITY_PROFIT_FACTOR
from strategy_family_screening import (
    DEVELOPMENT_MANIFEST_SHA256,
    SCREENING_ID,
    SCREENING_OUTCOMES,
    StrategyFamilyScreeningPreregistration,
    screening_configuration,
    screening_interpretation_policy,
    screening_strategy_engines,
)
from strategy_family_screening_runner import (
    CHECKSUM_FILENAME,
    REPORT_FILENAME,
    SCREENING_DIRECTORY_NAME,
    SCREENING_REPORT_SCHEMA_VERSION,
    STAGING_DIRECTORY_NAME,
    StrategyFamilyScreeningRunner,
    main,
)

EXPECTED_STRATEGIES = (
    "adx",
    "atr",
    "bollinger",
    "donchian",
    "macd",
    "rsi",
    "stochastic",
    "supertrend",
)


def market_frame(rows=8):
    index = pd.date_range("2024-01-01", periods=rows, freq="6h", tz="UTC")
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


def fake_backtest(strategy, drawdown=10.0, profit_factor=1.5):
    return {
        "initial_capital": 5000.0,
        "final_capital": 5100.0,
        "trade_history": [
            {
                "entry_index": pd.Timestamp("2024-01-01T06:00:00Z"),
                "profit_loss": np.float64(5.0),
            }
        ],
        "equity_curve": [5000.0, 5100.0],
        "performance": {
            "max_drawdown": drawdown,
            "number_of_trades": 6,
            "profit_factor": profit_factor,
        },
        "comparison": {
            "strategy_return": 0.02,
            "benchmark_return": 0.01,
            "excess_return": 0.01,
        },
        "benchmark": {"entry_index": pd.Timestamp("2024-01-01T00:00:00Z")},
        "execution_timing": "next_bar_open",
        "strategy": strategy,
    }


def fake_asset_result(
    strategy,
    status,
    *,
    window_count=5,
    trades_per_window=6,
    drawdown=10.0,
    profit_factor=1.5,
):
    windows = []
    for index in range(window_count):
        test = fake_backtest(strategy, drawdown, profit_factor)
        test["trade_history"] = [
            {"profit_loss": 1.0, "execution_index": index}
            for _ in range(trades_per_window)
        ]
        windows.append(
            {
                "window": index,
                "train": fake_backtest(strategy, drawdown, profit_factor),
                "test": test,
            }
        )
    return {
        "strategy": strategy,
        "classification": {
            "status": status,
            "gates": {
                "positive_oos_return": status == "VALIDATED",
                "positive_oos_excess_return": status == "VALIDATED",
                "passes_statistical_falsification": status == "VALIDATED",
                "walk_forward_persistence": status == "VALIDATED",
            },
        },
        "out_of_sample": {
            "split": {"in_sample_rows": 4, "out_of_sample_rows": 4},
            "generalization": {"return_difference": 0.01},
            "in_sample": fake_backtest(strategy, drawdown, profit_factor),
            "out_of_sample": fake_backtest(strategy, drawdown, profit_factor),
        },
        "walk_forward": {
            "configuration": {"train_size": 2880, "test_size": 720},
            "summary": {
                "window_count": window_count,
                "positive_test_excess_rate": 0.8,
            },
            "windows": windows,
        },
        "falsification": {
            "passes_statistical_falsification": status == "VALIDATED",
            "bootstrap": {"ci_lower": 0.1, "ci_upper": 2.0},
            "permutation": {"p_value": 0.02},
        },
    }


def fake_evaluation(
    strategy,
    status="REJECTED",
    *,
    window_count=5,
    trades_per_window=6,
    drawdown=10.0,
    profit_factor=1.5,
):
    assets = {
        asset: fake_asset_result(
            strategy,
            status,
            window_count=window_count,
            trades_per_window=trades_per_window,
            drawdown=drawdown,
            profit_factor=profit_factor,
        )
        for asset in ("BTC-USD", "ETH-USD")
    }
    return {
        "strategy": strategy,
        "asset_count": 2,
        "assets": assets,
        "summary": {
            "mean_oos_strategy_return": 0.02,
            "mean_oos_excess_return": 0.01,
            "positive_oos_excess_asset_rate": 1.0,
            "mean_walk_forward_positive_excess_rate": 0.8,
        },
        "classification": {
            "status": status,
            "counts": {status: 2},
        },
    }


class FakePreregistration:
    def __init__(self, manifest_sha256=DEVELOPMENT_MANIFEST_SHA256):
        self.calls = []
        self.locked = SimpleNamespace(
            manifest_sha256=manifest_sha256,
            contract=SimpleNamespace(
                dataset_id="coinbase-exchange-btc-eth-native-6h-20190101-20260801-v1",
                timeframe="6h",
                products=("BTC-USD", "ETH-USD"),
                as_dict=lambda: {
                    "dataset_id": "coinbase-exchange-btc-eth-native-6h-20190101-20260801-v1",
                    "timeframe": "6h",
                    "products": ["BTC-USD", "ETH-USD"],
                },
            ),
            configuration=screening_configuration(),
            strategy_engines=screening_strategy_engines(),
            assets={"BTC-USD": market_frame(), "ETH-USD": market_frame()},
        )

    def lock(self, manifest_path):
        self.calls.append(str(manifest_path))
        return self.locked

    def declaration(self):
        return StrategyFamilyScreeningPreregistration().declaration()


class FakeValidator:
    calls: ClassVar[list] = []
    results: ClassVar[dict] = {}

    def __init__(self, strategy_engine, **kwargs):
        self.strategy_engine = strategy_engine
        self.kwargs = kwargs
        type(self).calls.append(self)

    def run(self, assets):
        assert set(assets) == {"BTC-USD", "ETH-USD"}
        profile = (
            "baseline"
            if self.kwargs["slippage_rate"] == BASELINE_COSTS.slippage_rate
            else "stress"
        )
        strategy = self.strategy_engine.strategy_name
        settings = dict(type(self).results.get((strategy, profile), {}))
        return fake_evaluation(strategy, **settings)


@pytest.fixture(autouse=True)
def reset_fake_validator():
    FakeValidator.calls = []
    FakeValidator.results = {}


def runner(tmp_path, preregistration=None, validator_factory=FakeValidator):
    return StrategyFamilyScreeningRunner(
        output_root=tmp_path / "strategy_family_screening_v1",
        preregistration=preregistration or FakePreregistration(),
        validator_factory=validator_factory,
    )


def test_runner_evaluates_exact_order_once_under_baseline_and_stress(tmp_path):
    recorded = runner(tmp_path).run(tmp_path / "manifest.json")

    assert recorded.status == "STRATEGY_FAMILY_SCREENING_RECORDED"
    assert len(FakeValidator.calls) == 16
    assert [item.strategy_engine.strategy_name for item in FakeValidator.calls] == [
        name for name in EXPECTED_STRATEGIES for _profile in range(2)
    ]
    assert [item.kwargs["slippage_rate"] for item in FakeValidator.calls] == [
        rate
        for _name in EXPECTED_STRATEGIES
        for rate in (BASELINE_COSTS.slippage_rate, STRESSED_COSTS.slippage_rate)
    ]
    assert all(item.kwargs["train_size"] == 2880 for item in FakeValidator.calls)
    assert all(item.kwargs["test_size"] == 720 for item in FakeValidator.calls)
    assert all(item.kwargs["step_size"] == 720 for item in FakeValidator.calls)
    assert all(
        item.kwargs["execution_timing"] == "next_bar_open"
        for item in FakeValidator.calls
    )


def test_report_is_canonical_compact_and_retains_every_safety_boundary(tmp_path):
    recorded = runner(tmp_path).run(tmp_path / "manifest.json")
    report_bytes = recorded.report_path.read_bytes()
    payload = json.loads(report_bytes)

    assert canonical_json_bytes(payload) == report_bytes
    assert payload["schema_version"] == SCREENING_REPORT_SCHEMA_VERSION
    assert payload["status"] == "STRATEGY_FAMILY_SCREENING_COMPLETED"
    assert payload["screening_id"] == SCREENING_ID
    assert payload["manifest_sha256"] == DEVELOPMENT_MANIFEST_SHA256
    assert payload["strategy_order"] == list(EXPECTED_STRATEGIES)
    assert payload["development_data_only"] is True
    assert payload["development_screening_executed"] is True
    assert payload["automatic_ranking_generated"] is False
    assert payload["automatic_strategy_selection"] is False
    assert payload["formal_candidate_evaluation"] is False
    assert payload["candidate_v2_authorized"] is False
    assert payload["optimization_authorized"] is False
    assert payload["bounded_forward_paper_authorized"] is False
    assert payload["live_execution_authorized"] is False
    assert "winner" not in payload
    assert "ranking" not in payload
    assert b'"trade_history"' not in report_bytes
    assert b'"equity_curve"' not in report_bytes
    assert set(payload["strategy_evidence"]) == set(EXPECTED_STRATEGIES)

    expected_hash = hashlib.sha256(report_bytes).hexdigest()
    assert recorded.report_sha256 == expected_hash
    assert recorded.checksum_path.read_bytes() == (
        f"{expected_hash}  {REPORT_FILENAME}\n".encode("ascii")
    )


def test_outcomes_are_gate_based_and_never_ranked(tmp_path):
    for profile in ("baseline", "stress"):
        FakeValidator.results[("adx", profile)] = {"status": "VALIDATED"}
    FakeValidator.results[("atr", "baseline")] = {"status": "VALIDATED"}
    FakeValidator.results[("atr", "stress")] = {"status": "REJECTED"}
    FakeValidator.results[("bollinger", "baseline")] = {"status": "VALIDATED"}
    FakeValidator.results[("bollinger", "stress")] = {"status": "CONDITIONAL"}

    payload = json.loads(
        runner(tmp_path).run(tmp_path / "manifest.json").report_path.read_bytes()
    )
    comparison = payload["comparison"]

    assert comparison["strategy_order"] == list(EXPECTED_STRATEGIES)
    assert comparison["selection_policy"] == (
        "DESCRIPTIVE_MULTIPLE_COMPARISON_GUARD"
    )
    assert comparison["automatic_ranking_generated"] is False
    assert comparison["automatic_strategy_selection"] is False
    assert comparison["strategies"]["adx"]["outcome"] == (
        "MECHANISM_RETAINS_INTEREST"
    )
    assert comparison["strategies"]["atr"]["outcome"] == "SCREEN_OUT"
    assert comparison["strategies"]["bollinger"]["outcome"] == "INCONCLUSIVE"
    assert comparison["mechanisms_retaining_interest"] == ["adx"]
    assert comparison["outcome_counts"] == {
        "INCONCLUSIVE": 1,
        "MECHANISM_RETAINS_INTEREST": 1,
        "SCREEN_OUT": 6,
    }
    assert tuple(sorted(comparison["outcome_counts"])) == tuple(
        sorted(SCREENING_OUTCOMES)
    )


@pytest.mark.parametrize(
    ("settings", "failed_gate"),
    [
        ({"window_count": 4}, "minimum_walk_forward_windows"),
        ({"trades_per_window": 5}, "minimum_unseen_trades_per_asset"),
        ({"drawdown": 20.01}, "oos_drawdown_within_limit"),
    ],
)
def test_retains_interest_requires_frozen_volume_and_drawdown_gates(
    tmp_path, settings, failed_gate
):
    for profile in ("baseline", "stress"):
        FakeValidator.results[("adx", profile)] = {
            "status": "VALIDATED",
            **settings,
        }

    payload = json.loads(
        runner(tmp_path).run(tmp_path / "manifest.json").report_path.read_bytes()
    )
    review = payload["strategy_evidence"]["adx"]["screening_review"]

    assert review["outcome"] == "INCONCLUSIVE"
    assert review["gates"][failed_gate] is False
    assert failed_gate in review["failed_gates"]


def test_existing_final_or_staging_refuses_before_dataset_lock(tmp_path):
    preregistration = FakePreregistration()
    output_root = tmp_path / "strategy_family_screening_v1"
    (output_root / SCREENING_DIRECTORY_NAME).mkdir(parents=True)
    screening_runner = StrategyFamilyScreeningRunner(
        output_root=output_root,
        preregistration=preregistration,
        validator_factory=FakeValidator,
    )

    with pytest.raises(FileExistsError, match="already exists"):
        screening_runner.run(tmp_path / "manifest.json")
    assert preregistration.calls == []
    assert FakeValidator.calls == []

    (output_root / SCREENING_DIRECTORY_NAME).rmdir()
    (output_root / STAGING_DIRECTORY_NAME).mkdir()
    with pytest.raises(FileExistsError, match="incomplete"):
        screening_runner.run(tmp_path / "manifest.json")
    assert preregistration.calls == []
    assert FakeValidator.calls == []


def test_runner_rejects_non_frozen_manifest_before_evaluation(tmp_path):
    preregistration = FakePreregistration(manifest_sha256="0" * 64)

    with pytest.raises(ValueError, match="exact frozen screening dataset"):
        runner(tmp_path, preregistration=preregistration).run(
            tmp_path / "manifest.json"
        )

    assert len(preregistration.calls) == 1
    assert FakeValidator.calls == []


def test_runner_rejects_declaration_fingerprint_drift_before_evaluation(tmp_path):
    class DriftedDeclaration(FakePreregistration):
        def declaration(self):
            declaration = super().declaration()
            declaration["strategies"][0]["configuration_fingerprint"] = "0" * 64
            return declaration

    with pytest.raises(ValueError, match="fingerprint"):
        runner(tmp_path, preregistration=DriftedDeclaration()).run(
            tmp_path / "manifest.json"
        )

    assert FakeValidator.calls == []


def test_runner_rejects_engine_parameter_drift_before_evaluation(tmp_path):
    preregistration = FakePreregistration()
    preregistration.locked.strategy_engines["adx"].strategy.threshold = 26.0

    with pytest.raises(ValueError, match="parameters"):
        runner(tmp_path, preregistration=preregistration).run(
            tmp_path / "manifest.json"
        )

    assert FakeValidator.calls == []


@pytest.mark.parametrize(
    ("mutation", "message"),
    [
        (lambda result: result.__setitem__("strategy", "ema_crossover"), "identity"),
        (lambda result: result.__setitem__("asset_count", 1), "asset count"),
        (lambda result: result["assets"].pop("ETH-USD"), "asset scope"),
        (
            lambda result: result["classification"].__setitem__(
                "status", "PAPER_CANDIDATE"
            ),
            "classification",
        ),
    ],
)
def test_runner_fails_closed_on_invalid_validator_evidence(
    tmp_path, mutation, message
):
    class InvalidValidator(FakeValidator):
        def run(self, assets):
            result = super().run(assets)
            mutation(result)
            return result

    with pytest.raises(ValueError, match=message):
        runner(tmp_path, validator_factory=InvalidValidator).run(
            tmp_path / "manifest.json"
        )

    assert not (
        tmp_path / "strategy_family_screening_v1" / SCREENING_DIRECTORY_NAME
    ).exists()
    assert not (
        tmp_path / "strategy_family_screening_v1" / STAGING_DIRECTORY_NAME
    ).exists()


def test_positive_infinite_profit_factor_is_encoded_before_persistence(tmp_path):
    FakeValidator.results[("adx", "baseline")] = {
        "profit_factor": float("inf")
    }

    payload = json.loads(
        runner(tmp_path).run(tmp_path / "manifest.json").report_path.read_bytes()
    )
    baseline = payload["strategy_evidence"]["adx"]["baseline_evaluation"]
    encoded = baseline["assets"]["BTC-USD"]["walk_forward"]["windows"][0][
        "test"
    ]["performance"]["profit_factor"]

    assert encoded == POSITIVE_INFINITY_PROFIT_FACTOR
    assert baseline["raw_evaluation_encoding"] == {
        "positive_infinite_profit_factor_count": 24,
        "positive_infinite_profit_factor_value": POSITIVE_INFINITY_PROFIT_FACTOR,
    }


@pytest.mark.parametrize("value", [float("nan"), float("-inf")])
def test_other_non_finite_evidence_fails_before_staging(tmp_path, value):
    FakeValidator.results[("adx", "baseline")] = {"profit_factor": value}

    with pytest.raises(ValueError, match="Out of range float values"):
        runner(tmp_path).run(tmp_path / "manifest.json")

    assert not (
        tmp_path / "strategy_family_screening_v1" / SCREENING_DIRECTORY_NAME
    ).exists()
    assert not (
        tmp_path / "strategy_family_screening_v1" / STAGING_DIRECTORY_NAME
    ).exists()


def test_cli_prints_bounded_recorded_summary_only(monkeypatch, tmp_path, capsys):
    class FakeRecorded:
        def as_dict(self):
            return {
                "status": "STRATEGY_FAMILY_SCREENING_RECORDED",
                "report_sha256": "a" * 64,
                "development_screening_executed": True,
                "candidate_v2_authorized": False,
                "bounded_forward_paper_authorized": False,
                "live_execution_authorized": False,
            }

    class FakeRunner:
        def run(self, manifest_path):
            assert manifest_path == str(tmp_path / "manifest.json")
            return FakeRecorded()

    monkeypatch.setattr(
        runner_module,
        "StrategyFamilyScreeningRunner",
        FakeRunner,
    )

    assert main(["--manifest", str(tmp_path / "manifest.json")]) == 0
    output = json.loads(capsys.readouterr().out)
    assert output["status"] == "STRATEGY_FAMILY_SCREENING_RECORDED"
    assert output["candidate_v2_authorized"] is False
    assert output["live_execution_authorized"] is False


def test_runner_constants_and_policy_remain_bound_to_protocol():
    assert SCREENING_REPORT_SCHEMA_VERSION == 1
    assert screening_interpretation_policy()["outcomes"] == list(
        SCREENING_OUTCOMES
    )
    assert REPORT_FILENAME == "strategy_family_screening_report.json"
    assert CHECKSUM_FILENAME == "strategy_family_screening_report.sha256"
