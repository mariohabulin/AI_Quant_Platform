import hashlib
import json
import os
from pathlib import Path
import sys
from types import SimpleNamespace
from typing import ClassVar

import numpy as np
import pandas as pd
import pytest

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src")))

import alpha_development_runner as runner_module
from alpha_development_protocol import (
    ALPHA_DEVELOPMENT_ID,
    RECORDED_ATTRIBUTION_REPORT_SHA256,
    VARIANT_ORDER,
    alpha_development_configuration,
    alpha_development_interpretation_policy,
    alpha_development_protective_exit_policy,
    alpha_development_strategy_engines,
)
from alpha_development_runner import (
    ALPHA_DEVELOPMENT_REPORT_SCHEMA_VERSION,
    CHECKSUM_FILENAME,
    DEVELOPMENT_DIRECTORY_NAME,
    DEVELOPMENT_OUTCOMES,
    REPORT_FILENAME,
    SCENARIO_ORDER,
    STAGING_DIRECTORY_NAME,
    AlphaDevelopmentRunner,
    main,
)
from first_strategy_candidate import BASELINE_COSTS, STRESSED_COSTS
from research_evidence import canonical_json_bytes
from strategy_family_screening import DEVELOPMENT_MANIFEST_SHA256
from venue_execution_research import VENUE_EXECUTION_SCENARIOS


def market_frame(rows=8):
    index = pd.date_range("2024-01-01", periods=rows, freq="6h", tz="UTC")
    prices = np.arange(100.0, 100.0 + rows)
    return pd.DataFrame(
        {
            "Open": prices,
            "High": prices + 1.0,
            "Low": prices - 1.0,
            "Close": prices + 0.5,
            "Volume": np.full(rows, 1000.0),
        },
        index=index,
    )


def fake_trade(*, shares=10.0, total_costs=5.0, reason="PROTECTIVE_TARGET"):
    return {
        "entry_index": pd.Timestamp("2024-01-01T06:00:00Z"),
        "exit_index": pd.Timestamp("2024-01-02T00:00:00Z"),
        "entry_signal_index": pd.Timestamp("2024-01-01T00:00:00Z"),
        "exit_signal_index": None,
        "entry_market_price": 100.0,
        "exit_market_price": 106.0,
        "entry_price": 100.5,
        "exit_price": 105.5,
        "shares": shares,
        "gross_profit_loss": 60.0,
        "total_commission": total_costs * 0.8,
        "execution_cost": total_costs * 0.2,
        "total_costs": total_costs,
        "profit_loss": 60.0 - total_costs,
        "exit_reason": reason,
        "protective_exit_executed": reason.startswith("PROTECTIVE"),
        "protective_exit_type": "TARGET_INTRABAR",
    }


def fake_backtest(
    strategy,
    policy,
    *,
    drawdown=10.0,
    oos_return=0.05,
    shares=10.0,
    total_costs=5.0,
    trade_count=2,
):
    trades = [
        fake_trade(shares=shares, total_costs=total_costs)
        for _ in range(trade_count)
    ]
    return {
        "initial_capital": 5000.0,
        "final_capital": 5000.0 * (1.0 + oos_return),
        "trade_history": trades,
        "equity_curve": [
            {"index": pd.Timestamp("2024-01-01T00:00:00Z"), "equity": 5000.0},
            {"index": pd.Timestamp("2024-12-31T18:00:00Z"), "equity": 5250.0},
        ],
        "performance": {
            "max_drawdown": drawdown,
            "number_of_trades": trade_count,
            "profit_factor": 1.5,
        },
        "comparison": {
            "strategy_return": oos_return,
            "benchmark_return": 0.01,
            "excess_return": oos_return - 0.01,
        },
        "benchmark": {
            "entry_index": pd.Timestamp("2024-01-01T00:00:00Z")
        },
        "execution_timing": "next_bar_open",
        "protective_exit_policy": policy,
        "strategy": strategy,
    }


def fake_asset_result(
    strategy,
    policy,
    status,
    *,
    window_count=5,
    trades_per_window=4,
    drawdown=10.0,
    oos_return=0.05,
    shares=10.0,
    total_costs=5.0,
):
    windows = []
    for number in range(window_count):
        windows.append(
            {
                "window": number + 1,
                "train": fake_backtest(strategy, policy),
                "test": fake_backtest(
                    strategy,
                    policy,
                    trade_count=trades_per_window,
                    drawdown=drawdown,
                    oos_return=oos_return,
                ),
            }
        )
    partition = fake_backtest(
        strategy,
        policy,
        drawdown=drawdown,
        oos_return=oos_return,
        shares=shares,
        total_costs=total_costs,
    )
    return {
        "strategy": strategy,
        "classification": {
            "status": status,
            "gates": {
                "positive_oos_return": oos_return > 0.0,
                "positive_oos_excess_return": oos_return > 0.01,
                "passes_statistical_falsification": status == "VALIDATED",
                "walk_forward_persistence": status == "VALIDATED",
            },
        },
        "out_of_sample": {
            "split": {
                "split_position": 4,
                "in_sample_rows": 4,
                "out_of_sample_rows": 4,
                "out_of_sample_start": pd.Timestamp("2024-01-01T00:00:00Z"),
                "out_of_sample_end": pd.Timestamp("2024-12-31T18:00:00Z"),
            },
            "generalization": {"return_difference": 0.01},
            "in_sample": fake_backtest(strategy, policy),
            "out_of_sample": partition,
        },
        "walk_forward": {
            "configuration": {
                "train_size": 2880,
                "test_size": 720,
                "step_size": 720,
            },
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


def fake_evaluation(strategy, policy, status="REJECTED", **settings):
    assets = {
        asset: fake_asset_result(strategy, policy, status, **settings)
        for asset in ("BTC-USD", "ETH-USD")
    }
    return {
        "strategy": strategy,
        "asset_count": 2,
        "assets": assets,
        "summary": {
            "mean_oos_strategy_return": settings.get("oos_return", 0.05),
            "mean_oos_excess_return": 0.04,
            "positive_oos_excess_asset_rate": 1.0,
            "mean_walk_forward_positive_excess_rate": 0.8,
        },
        "classification": {
            "status": status,
            "counts": {status: 2},
        },
    }


class FakePreregistration:
    def __init__(
        self,
        manifest_sha256=DEVELOPMENT_MANIFEST_SHA256,
        attribution_sha256=RECORDED_ATTRIBUTION_REPORT_SHA256,
    ):
        self.calls = []
        self.locked = SimpleNamespace(
            manifest_sha256=manifest_sha256,
            attribution_report_sha256=attribution_sha256,
            contract=SimpleNamespace(
                dataset_id=(
                    "coinbase-exchange-btc-eth-native-6h-20190101-20260801-v1"
                ),
                timeframe="6h",
                products=("BTC-USD", "ETH-USD"),
                as_dict=lambda: {
                    "dataset_id": (
                        "coinbase-exchange-btc-eth-native-6h-20190101-20260801-v1"
                    ),
                    "timeframe": "6h",
                    "products": ["BTC-USD", "ETH-USD"],
                },
            ),
            configuration=alpha_development_configuration(),
            strategy_engines=alpha_development_strategy_engines(),
            assets={"BTC-USD": market_frame(), "ETH-USD": market_frame()},
        )

    def lock(self, manifest_path, attribution_report_path):
        self.calls.append((str(manifest_path), str(attribution_report_path)))
        return self.locked


class FakeValidator:
    calls: ClassVar[list] = []
    results: ClassVar[dict] = {}

    def __init__(self, strategy_engine, **kwargs):
        self.strategy_engine = strategy_engine
        self.kwargs = kwargs
        type(self).calls.append(self)

    @staticmethod
    def _scenario(kwargs):
        for scenario in VENUE_EXECUTION_SCENARIOS:
            if (
                scenario.executable_in_v2_runner
                and kwargs["commission_rate"] == scenario.commission_rate
                and kwargs["slippage_rate"] == scenario.slippage_rate
                and kwargs["spread_rate"] == scenario.spread_rate
            ):
                return scenario.label
        raise AssertionError("Unknown fake scenario.")

    def run(self, assets):
        assert tuple(sorted(assets)) == ("BTC-USD", "ETH-USD")
        strategy = self.strategy_engine.strategy_name
        scenario = self._scenario(self.kwargs)
        settings = dict(type(self).results.get((strategy, scenario), {}))
        policy = self.kwargs["protective_exit_policy"].as_dict()
        return fake_evaluation(strategy, policy, **settings)


@pytest.fixture(autouse=True)
def reset_fake_validator():
    FakeValidator.calls = []
    FakeValidator.results = {}


def runner(tmp_path, preregistration=None, validator_factory=FakeValidator):
    return AlphaDevelopmentRunner(
        output_root=tmp_path / "alpha_development_v2",
        preregistration=preregistration or FakePreregistration(),
        validator_factory=validator_factory,
    )


def set_profile(variant_id, scenario, **settings):
    strategy = f"alpha_v2_{variant_id}"
    FakeValidator.results[(strategy, scenario)] = settings


def validate_variant(variant_id, kraken_status="REJECTED", **settings):
    set_profile(variant_id, BASELINE_COSTS.label, status="VALIDATED", **settings)
    set_profile(variant_id, STRESSED_COSTS.label, status="VALIDATED", **settings)
    set_profile(variant_id, SCENARIO_ORDER[2], status=kraken_status, **settings)


def test_runner_executes_exact_three_by_three_matrix_with_active_risk_and_protection(
    tmp_path,
):
    recorded = runner(tmp_path).run("manifest.json", "attribution.json")
    assert recorded.joint_multi_asset_evaluations == 9
    assert len(FakeValidator.calls) == 9
    assert [call.strategy_engine.strategy.variant.variant_id for call in FakeValidator.calls] == [
        variant for variant in VARIANT_ORDER for _scenario in SCENARIO_ORDER
    ]
    assert [FakeValidator._scenario(call.kwargs) for call in FakeValidator.calls] == [
        scenario for _variant in VARIANT_ORDER for scenario in SCENARIO_ORDER
    ]
    assert all(call.kwargs["train_size"] == 2880 for call in FakeValidator.calls)
    assert all(call.kwargs["test_size"] == 720 for call in FakeValidator.calls)
    assert all(call.kwargs["execution_timing"] == "next_bar_open" for call in FakeValidator.calls)
    assert all(call.kwargs["risk_engine"].risk_per_trade == pytest.approx(0.005) for call in FakeValidator.calls)
    assert all(call.kwargs["protective_exit_policy"].entry_bar_protection is True for call in FakeValidator.calls)


def test_report_is_canonical_atomic_compact_and_non_promotional(tmp_path):
    recorded = runner(tmp_path).run("manifest.json", "attribution.json")
    report_bytes = recorded.report_path.read_bytes()
    payload = json.loads(report_bytes)
    assert canonical_json_bytes(payload) == report_bytes
    assert payload["schema_version"] == ALPHA_DEVELOPMENT_REPORT_SCHEMA_VERSION
    assert payload["status"] == "ALPHA_DEVELOPMENT_COMPLETED"
    assert payload["alpha_development_id"] == ALPHA_DEVELOPMENT_ID
    assert payload["manifest_sha256"] == DEVELOPMENT_MANIFEST_SHA256
    assert payload["attribution_report_sha256"] == RECORDED_ATTRIBUTION_REPORT_SHA256
    assert payload["variant_order"] == list(VARIANT_ORDER)
    assert payload["scenario_order"] == list(SCENARIO_ORDER)
    assert payload["joint_multi_asset_evaluations"] == 9
    assert payload["joint_development_evaluation_executed"] is True
    assert payload["protective_exit_engine_active"] is True
    assert payload["automatic_ranking_generated"] is False
    assert payload["automatic_strategy_selection"] is False
    assert payload["parameter_calibration_executed"] is False
    assert payload["selected_variant"] is None
    assert payload["formal_candidate_evaluation"] is False
    assert payload["candidate_v2_authorized"] is False
    assert payload["bounded_forward_paper_authorized"] is False
    assert payload["live_execution_authorized"] is False
    assert b'"trade_history"' not in report_bytes
    assert b'"equity_curve"' not in report_bytes
    expected_hash = hashlib.sha256(report_bytes).hexdigest()
    assert recorded.report_sha256 == expected_hash
    assert recorded.checksum_path.read_bytes() == (
        f"{expected_hash}  {REPORT_FILENAME}\n".encode("ascii")
    )


def test_fixed_ablation_outcomes_are_gate_based_and_kraken_is_sensitivity_only(
    tmp_path,
):
    validate_variant(VARIANT_ORDER[0], kraken_status="REJECTED")
    set_profile(VARIANT_ORDER[1], BASELINE_COSTS.label, status="VALIDATED")
    set_profile(VARIANT_ORDER[1], STRESSED_COSTS.label, status="CONDITIONAL")
    set_profile(VARIANT_ORDER[1], SCENARIO_ORDER[2], status="VALIDATED")

    payload = json.loads(
        runner(tmp_path).run("manifest.json", "attribution.json").report_path.read_bytes()
    )
    comparison = payload["comparison"]
    assert comparison["comparison_mode"] == "FIXED_CAUSAL_ABLATION_NOT_RANKING"
    assert comparison["automatic_ranking_generated"] is False
    assert comparison["selected_variant"] is None
    assert comparison["variants"][VARIANT_ORDER[0]]["outcome"] == (
        "MECHANISM_RETAINS_DEVELOPMENT_INTEREST"
    )
    assert comparison["variants"][VARIANT_ORDER[1]]["outcome"] == "INCONCLUSIVE"
    assert comparison["variants"][VARIANT_ORDER[2]]["outcome"] == "SCREEN_OUT"
    assert comparison["mechanisms_retaining_interest"] == [VARIANT_ORDER[0]]
    assert comparison["outcome_counts"] == {
        "INCONCLUSIVE": 1,
        "MECHANISM_RETAINS_DEVELOPMENT_INTEREST": 1,
        "SCREEN_OUT": 1,
    }


@pytest.mark.parametrize(
    ("settings", "failed_gate"),
    [
        ({"drawdown": 20.01}, "oos_drawdown_within_limit"),
        ({"shares": 400.0}, "annual_turnover_within_budget"),
        ({"total_costs": 700.0}, "annual_baseline_cost_within_budget"),
    ],
)
def test_risk_turnover_or_cost_budget_breach_screens_out(
    tmp_path, settings, failed_gate
):
    validate_variant(VARIANT_ORDER[0], **settings)
    payload = json.loads(
        runner(tmp_path).run("manifest.json", "attribution.json").report_path.read_bytes()
    )
    review = payload["variant_evidence"][VARIANT_ORDER[0]]["development_review"]
    assert review["outcome"] == "SCREEN_OUT"
    assert review["gates"][failed_gate] is False
    assert failed_gate in review["failed_gates"]


@pytest.mark.parametrize(
    ("settings", "failed_gate"),
    [
        ({"window_count": 4}, "minimum_walk_forward_windows"),
        ({"trades_per_window": 3}, "minimum_development_trades_per_asset"),
    ],
)
def test_incomplete_evidence_is_inconclusive_not_promoted(
    tmp_path, settings, failed_gate
):
    validate_variant(VARIANT_ORDER[0], **settings)
    payload = json.loads(
        runner(tmp_path).run("manifest.json", "attribution.json").report_path.read_bytes()
    )
    review = payload["variant_evidence"][VARIANT_ORDER[0]]["development_review"]
    assert review["outcome"] == "INCONCLUSIVE"
    assert review["gates"][failed_gate] is False


def test_operational_summary_uses_execution_notional_and_records_exit_evidence(tmp_path):
    validate_variant(VARIANT_ORDER[0])
    payload = json.loads(
        runner(tmp_path).run("manifest.json", "attribution.json").report_path.read_bytes()
    )
    operational = payload["variant_evidence"][VARIANT_ORDER[0]]["profiles"][
        BASELINE_COSTS.label
    ]["operational_assets"]["BTC-USD"]
    assert operational["round_trip_executed_notional"] == pytest.approx(
        2 * 10.0 * (100.5 + 105.5)
    )
    assert operational["total_costs"] == pytest.approx(10.0)
    assert operational["exit_reason_counts"]["PROTECTIVE_TARGET"] == 2
    assert operational["protective_exit_count"] == 2
    assert operational["protective_policy_active"] is True


def test_existing_final_or_staging_blocks_before_evidence_lock(tmp_path):
    preregistration = FakePreregistration()
    output_root = tmp_path / "alpha_development_v2"
    (output_root / DEVELOPMENT_DIRECTORY_NAME).mkdir(parents=True)
    development_runner = AlphaDevelopmentRunner(
        output_root=output_root,
        preregistration=preregistration,
        validator_factory=FakeValidator,
    )
    with pytest.raises(FileExistsError, match="already exists"):
        development_runner.run("manifest.json", "attribution.json")
    assert preregistration.calls == []
    assert FakeValidator.calls == []

    (output_root / DEVELOPMENT_DIRECTORY_NAME).rmdir()
    (output_root / STAGING_DIRECTORY_NAME).mkdir()
    with pytest.raises(FileExistsError, match="incomplete"):
        development_runner.run("manifest.json", "attribution.json")
    assert preregistration.calls == []
    assert FakeValidator.calls == []


@pytest.mark.parametrize(
    ("preregistration", "message"),
    [
        (FakePreregistration(manifest_sha256="0" * 64), "manifest"),
        (FakePreregistration(attribution_sha256="0" * 64), "attribution"),
    ],
)
def test_runner_rejects_wrong_frozen_evidence_before_evaluation(
    tmp_path, preregistration, message
):
    with pytest.raises(ValueError, match=message):
        runner(tmp_path, preregistration=preregistration).run(
            "manifest.json", "attribution.json"
        )
    assert FakeValidator.calls == []


def test_runner_rejects_strategy_or_configuration_drift_before_evaluation(tmp_path):
    preregistration = FakePreregistration()
    preregistration.locked.strategy_engines[VARIANT_ORDER[0]].strategy.entry_threshold = 26.0
    with pytest.raises(ValueError, match="strategy identity"):
        runner(tmp_path, preregistration=preregistration).run(
            "manifest.json", "attribution.json"
        )
    assert FakeValidator.calls == []

    preregistration = FakePreregistration()
    preregistration.locked.configuration["risk"]["risk_per_trade_fraction"] = 0.01
    with pytest.raises(ValueError, match="configuration"):
        runner(tmp_path, preregistration=preregistration).run(
            "manifest.json", "attribution.json"
        )
    assert FakeValidator.calls == []


@pytest.mark.parametrize(
    ("mutation", "message"),
    [
        (lambda result: result.__setitem__("strategy", "wrong"), "identity"),
        (lambda result: result.__setitem__("asset_count", 1), "asset count"),
        (lambda result: result["assets"].pop("ETH-USD"), "asset scope"),
        (
            lambda result: result["classification"].__setitem__(
                "status", "PAPER_CANDIDATE"
            ),
            "classification",
        ),
        (
            lambda result: result["assets"]["BTC-USD"]["out_of_sample"][
                "out_of_sample"
            ].__setitem__("protective_exit_policy", None),
            "protective policy",
        ),
    ],
)
def test_invalid_validator_evidence_fails_before_staging(
    tmp_path, mutation, message
):
    class InvalidValidator(FakeValidator):
        def run(self, assets):
            result = super().run(assets)
            mutation(result)
            return result

    with pytest.raises(ValueError, match=message):
        runner(tmp_path, validator_factory=InvalidValidator).run(
            "manifest.json", "attribution.json"
        )
    assert not (tmp_path / "alpha_development_v2" / DEVELOPMENT_DIRECTORY_NAME).exists()
    assert not (tmp_path / "alpha_development_v2" / STAGING_DIRECTORY_NAME).exists()


def test_non_finite_trade_evidence_fails_before_staging(tmp_path):
    class NonFiniteValidator(FakeValidator):
        def run(self, assets):
            result = super().run(assets)
            result["assets"]["BTC-USD"]["out_of_sample"]["out_of_sample"][
                "trade_history"
            ][0]["total_costs"] = float("nan")
            return result

    with pytest.raises(ValueError, match="finite|Out of range"):
        runner(tmp_path, validator_factory=NonFiniteValidator).run(
            "manifest.json", "attribution.json"
        )
    assert not (tmp_path / "alpha_development_v2" / DEVELOPMENT_DIRECTORY_NAME).exists()


def test_maker_scenario_is_structurally_excluded():
    assert len(SCENARIO_ORDER) == 3
    assert all(
        scenario.order_role == "TAKER"
        for scenario in VENUE_EXECUTION_SCENARIOS
        if scenario.label in SCENARIO_ORDER
    )
    assert all("maker" not in label for label in SCENARIO_ORDER)


def test_cli_prints_bounded_non_promotional_summary(monkeypatch, tmp_path, capsys):
    class FakeRecorded:
        def as_dict(self):
            return {
                "status": "ALPHA_DEVELOPMENT_RECORDED",
                "report_sha256": "a" * 64,
                "joint_development_evaluation_executed": True,
                "automatic_strategy_selection": False,
                "candidate_v2_authorized": False,
                "bounded_forward_paper_authorized": False,
                "live_execution_authorized": False,
            }

    class FakeRunner:
        def run(self, manifest_path, attribution_path):
            assert manifest_path == str(tmp_path / "manifest.json")
            assert attribution_path == str(tmp_path / "attribution.json")
            return FakeRecorded()

    monkeypatch.setattr(runner_module, "AlphaDevelopmentRunner", FakeRunner)
    assert main(
        [
            "--manifest",
            str(tmp_path / "manifest.json"),
            "--attribution-report",
            str(tmp_path / "attribution.json"),
        ]
    ) == 0
    output = json.loads(capsys.readouterr().out)
    assert output["status"] == "ALPHA_DEVELOPMENT_RECORDED"
    assert output["candidate_v2_authorized"] is False
    assert output["live_execution_authorized"] is False


def test_runner_constants_remain_bound_to_protocol():
    assert ALPHA_DEVELOPMENT_REPORT_SCHEMA_VERSION == 1
    assert REPORT_FILENAME == "alpha_development_report.json"
    assert CHECKSUM_FILENAME == "alpha_development_report.sha256"
    assert tuple(sorted(DEVELOPMENT_OUTCOMES)) == tuple(
        sorted(alpha_development_interpretation_policy()["allowed_outcomes"])
    )
    assert alpha_development_protective_exit_policy().reward_risk_ratio == 3.0
