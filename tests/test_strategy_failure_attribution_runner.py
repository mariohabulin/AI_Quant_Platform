import hashlib
import json
import os
from types import SimpleNamespace
import sys

import numpy as np
import pandas as pd
import pytest

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src")))

import strategy_failure_attribution_runner as runner_module
from first_strategy_candidate import BASELINE_COSTS, STRESSED_COSTS
from research_evidence import canonical_json_bytes
from strategy_failure_attribution import (
    ATTRIBUTION_ID,
    RECORDED_SCREENING_REPORT_SHA256,
    ZERO_COSTS,
    failure_attribution_configuration,
)
from strategy_failure_attribution_runner import (
    ATTRIBUTION_REPORT_SCHEMA_VERSION,
    REPORT_FILENAME,
    FailureAttributionRunner,
    main,
)
from strategy_family_screening import (
    DEVELOPMENT_MANIFEST_SHA256,
    screening_configuration,
    screening_strategy_engines,
)


EXPECTED_STRATEGIES = (
    "adx", "atr", "bollinger", "donchian", "macd", "rsi", "stochastic", "supertrend",
)


def market_frame(rows=60):
    index = pd.date_range("2024-01-01T00:00:00Z", periods=rows, freq="6h")
    phase = np.linspace(0.0, 8.0 * np.pi, rows)
    close = 100.0 + np.arange(rows) * 0.15 + np.sin(phase) * 4.0
    volume = 100.0 + (np.arange(rows) % 9) * 15.0
    return pd.DataFrame(
        {"Open": close - 0.2, "High": close + 1.0, "Low": close - 1.0, "Close": close, "Volume": volume},
        index=index,
    )


def backtest_run(data, strategy_return, costs, include_trade=True):
    initial = 5000.0
    trade_history = []
    if include_trade:
        entry_position = 22 if len(data) > 24 else 2
        exit_position = min(entry_position + 3, len(data) - 1)
        gross = 100.0 if strategy_return > 0 else -100.0
        total_costs = float(costs)
        trade_history = [{
            "entry_signal_index": data.index[entry_position - 1],
            "entry_index": data.index[entry_position],
            "exit_signal_index": data.index[exit_position - 1],
            "exit_index": data.index[exit_position],
            "execution_timing": "next_bar_open",
            "entry_market_price": float(data.iloc[entry_position]["Open"]),
            "exit_market_price": float(data.iloc[exit_position]["Open"]),
            "entry_price": float(data.iloc[entry_position]["Open"]),
            "exit_price": float(data.iloc[exit_position]["Open"]),
            "shares": 2.0,
            "gross_profit_loss": gross,
            "entry_commission": total_costs * 0.2,
            "exit_commission": total_costs * 0.3,
            "total_commission": total_costs * 0.5,
            "execution_cost": total_costs * 0.5,
            "total_costs": total_costs,
            "profit_loss": gross - total_costs,
            "risk_status": None,
            "planned_monetary_risk": None,
            "planned_stop_price": None,
            "planned_target_price": None,
            "planned_reward_risk_ratio": None,
        }]
    equity = np.linspace(initial, initial * (1.0 + strategy_return), len(data))
    if len(equity) >= 4:
        equity[len(equity) // 2] *= 0.85
    curve = [{"index": index, "equity": float(value)} for index, value in zip(data.index, equity)]
    final = float(equity[-1])
    return {
        "initial_capital": initial,
        "execution_timing": "next_bar_open",
        "final_capital": final,
        "trade_history": trade_history,
        "equity_curve": curve,
        "performance": {
            "total_return": strategy_return * 100.0,
            "number_of_trades": len(trade_history),
            "winning_trades": int(strategy_return > 0 and bool(trade_history)),
            "losing_trades": int(strategy_return <= 0 and bool(trade_history)),
            "win_rate": 100.0 if strategy_return > 0 else 0.0,
            "average_win": 100.0 if strategy_return > 0 else 0.0,
            "average_loss": -100.0 if strategy_return <= 0 else 0.0,
            "profit_factor": 2.0,
            "max_drawdown": 15.0,
            "expectancy": strategy_return * 100.0,
            "sharpe_ratio": strategy_return,
        },
        "benchmark": {"benchmark": "buy_and_hold", "initial_capital": initial, "final_capital": initial * 0.98, "total_return": -0.02},
        "comparison": {"strategy_return": strategy_return, "benchmark_return": -0.02, "excess_return": strategy_return + 0.02},
    }


def asset_evaluation(data, strategy, strategy_return, costs):
    split_position = 20
    in_sample_data = data.iloc[:split_position]
    oos_data = data.iloc[split_position:]
    in_sample = backtest_run(in_sample_data, 0.02, costs, include_trade=False)
    out_of_sample = backtest_run(oos_data, strategy_return, costs)
    window_test = backtest_run(oos_data.iloc[:20], strategy_return, costs)
    window_train = backtest_run(data.iloc[:20], 0.01, costs, include_trade=False)
    statistical_pass = strategy_return > 0.0
    status = "VALIDATED" if statistical_pass else "REJECTED"
    return {
        "strategy": strategy,
        "out_of_sample": {
            "split": {
                "split_position": split_position, "in_sample_rows": split_position, "out_of_sample_rows": len(oos_data),
                "in_sample_start": in_sample_data.index[0], "in_sample_end": in_sample_data.index[-1],
                "out_of_sample_start": oos_data.index[0], "out_of_sample_end": oos_data.index[-1],
            },
            "in_sample": in_sample,
            "out_of_sample": out_of_sample,
            "generalization": {
                "in_sample_strategy_return": 0.02, "out_of_sample_strategy_return": strategy_return,
                "in_sample_excess_return": 0.04, "out_of_sample_excess_return": strategy_return + 0.02,
            },
        },
        "walk_forward": {
            "configuration": {"train_size": 20, "test_size": 20, "step_size": 20, "expanding": True},
            "windows": [{
                "window": 1, "train_start": data.index[0], "train_end": data.index[19],
                "test_start": oos_data.index[0], "test_end": oos_data.index[19], "train_rows": 20, "test_rows": 20,
                "train": window_train, "test": window_test,
            }],
            "summary": {
                "window_count": 1, "mean_test_strategy_return": strategy_return,
                "mean_test_excess_return": strategy_return + 0.02,
                "positive_test_return_windows": int(strategy_return > 0.0),
                "positive_test_excess_windows": int(strategy_return > -0.02),
                "positive_test_return_rate": float(strategy_return > 0.0),
                "positive_test_excess_rate": float(strategy_return > -0.02),
            },
        },
        "falsification": {
            "passes_statistical_falsification": statistical_pass,
            "bootstrap": {"ci_lower": -1.0, "ci_upper": 1.0},
            "permutation": {"p_value": 0.5}, "monte_carlo": {"drawdown": 10.0},
        },
        "classification": {"status": status, "gates": {}, "thresholds": {"min_positive_walk_forward_excess_rate": 0.6}},
    }


def multi_asset_evaluation(strategy, assets, strategy_return, costs):
    results = {name: asset_evaluation(data, strategy, strategy_return, costs) for name, data in sorted(assets.items())}
    status = "VALIDATED" if strategy_return > 0.0 else "REJECTED"
    return {
        "strategy": strategy, "asset_count": 2, "assets": results,
        "summary": {
            "mean_oos_strategy_return": strategy_return, "mean_oos_excess_return": strategy_return + 0.02,
            "positive_oos_excess_asset_rate": float(strategy_return > -0.02),
            "mean_walk_forward_positive_excess_rate": float(strategy_return > -0.02),
        },
        "classification": {
            "status": status,
            "counts": {"VALIDATED": 2 if status == "VALIDATED" else 0, "CONDITIONAL": 0, "REJECTED": 2 if status == "REJECTED" else 0},
            "rates": {"validated": float(status == "VALIDATED"), "conditional": 0.0, "rejected": float(status == "REJECTED")},
            "gates": {}, "thresholds": {"min_assets": 2},
        },
    }


class FakePreregistration:
    def __init__(self, manifest_sha256=DEVELOPMENT_MANIFEST_SHA256):
        self.calls = []
        assets = {"BTC-USD": market_frame(), "ETH-USD": market_frame() * 1.05}
        self.locked = SimpleNamespace(
            manifest_sha256=manifest_sha256,
            screening_report_sha256=RECORDED_SCREENING_REPORT_SHA256,
            contract=SimpleNamespace(
                dataset_id="coinbase-exchange-btc-eth-native-6h-20190101-20260801-v1", timeframe="6h",
                products=("BTC-USD", "ETH-USD"), granularity_seconds=21600,
                as_dict=lambda: {"dataset_id": "coinbase-exchange-btc-eth-native-6h-20190101-20260801-v1", "timeframe": "6h", "products": ["BTC-USD", "ETH-USD"], "granularity_seconds": 21600},
            ),
            screening_configuration=screening_configuration(),
            strategy_engines=screening_strategy_engines(), assets=assets,
            screening_report={"status": "STRATEGY_FAMILY_SCREENING_COMPLETED"},
            attribution_configuration=failure_attribution_configuration(),
        )

    def lock(self, manifest_path, report_path):
        self.calls.append((str(manifest_path), str(report_path)))
        return self.locked

    def declaration(self):
        return {
            "attribution_id": ATTRIBUTION_ID, "required_manifest_sha256": DEVELOPMENT_MANIFEST_SHA256,
            "required_screening_report_sha256": RECORDED_SCREENING_REPORT_SHA256,
            "strategy_order": list(EXPECTED_STRATEGIES), "configuration": failure_attribution_configuration(),
            "failure_attribution_executed": False, "performance_replay_executed": False,
            "automatic_ranking_generated": False, "automatic_strategy_selection": False,
            "parameter_sweep_authorized": False, "strategy_combination_authorized": False,
            "candidate_v2_authorized": False, "bounded_forward_paper_authorized": False,
            "live_execution_authorized": False,
        }


class FakeValidator:
    calls = []
    overrides = {}

    def __init__(self, strategy_engine, **kwargs):
        self.strategy_engine = strategy_engine
        self.kwargs = kwargs
        type(self).calls.append(self)

    def run(self, assets):
        if self.kwargs["commission_rate"] == 0.0:
            profile, default_return, costs = "zero_cost", 0.05, 0.0
        elif self.kwargs["slippage_rate"] == BASELINE_COSTS.slippage_rate:
            profile, default_return, costs = "baseline", -0.03, 20.0
        else:
            profile, default_return, costs = "stress", -0.08, 35.0
        strategy = self.strategy_engine.strategy_name
        strategy_return = type(self).overrides.get((strategy, profile), default_return)
        return multi_asset_evaluation(strategy, assets, strategy_return, costs)


@pytest.fixture(autouse=True)
def reset_fake_validator():
    FakeValidator.calls = []
    FakeValidator.overrides = {}


def runner(tmp_path, preregistration=None, validator_factory=FakeValidator):
    return FailureAttributionRunner(
        output_root=tmp_path / "strategy_failure_attribution_v1",
        preregistration=preregistration or FakePreregistration(),
        validator_factory=validator_factory,
    )


def test_runner_executes_exact_eight_by_three_profile_matrix(tmp_path):
    recorded = runner(tmp_path).run("manifest.json", "screening.json")
    assert recorded.status == "FAILURE_ATTRIBUTION_RECORDED"
    assert len(FakeValidator.calls) == 24
    assert [item.strategy_engine.strategy_name for item in FakeValidator.calls] == [name for name in EXPECTED_STRATEGIES for _profile in range(3)]
    assert [item.kwargs["commission_rate"] for item in FakeValidator.calls] == [rate for _name in EXPECTED_STRATEGIES for rate in (ZERO_COSTS.commission_rate, BASELINE_COSTS.commission_rate, STRESSED_COSTS.commission_rate)]
    assert all(item.kwargs["execution_timing"] == "next_bar_open" for item in FakeValidator.calls)


def test_report_is_canonical_atomic_bounded_and_safely_non_promotional(tmp_path):
    recorded = runner(tmp_path).run("manifest.json", "screening.json")
    report_bytes = recorded.report_path.read_bytes()
    payload = json.loads(report_bytes)
    assert canonical_json_bytes(payload) == report_bytes
    assert payload["schema_version"] == ATTRIBUTION_REPORT_SCHEMA_VERSION
    assert payload["status"] == "FAILURE_ATTRIBUTION_COMPLETED"
    assert payload["attribution_id"] == ATTRIBUTION_ID
    assert payload["manifest_sha256"] == DEVELOPMENT_MANIFEST_SHA256
    assert payload["screening_report_sha256"] == RECORDED_SCREENING_REPORT_SHA256
    assert payload["strategy_order"] == list(EXPECTED_STRATEGIES)
    assert payload["diagnostic_multi_asset_replays"] == 24
    assert payload["failure_attribution_executed"] is True
    assert payload["performance_replay_executed"] is True
    assert payload["volume_analysis_executed"] is True
    assert payload["market_regime_analysis_executed"] is True
    assert payload["automatic_ranking_generated"] is False
    assert payload["automatic_strategy_selection"] is False
    assert payload["selected_strategy"] is None
    assert payload["new_alpha_hypothesis_generated"] is False
    assert payload["candidate_v2_authorized"] is False
    assert payload["bounded_forward_paper_authorized"] is False
    assert payload["live_execution_authorized"] is False
    assert b'"trade_history"' not in report_bytes
    assert b'"equity_curve"' not in report_bytes
    digest = hashlib.sha256(report_bytes).hexdigest()
    assert recorded.report_sha256 == digest
    assert recorded.checksum_path.read_bytes() == f"{digest}  {REPORT_FILENAME}\n".encode("ascii")
    assert not (recorded.report_path.parent.parent / ".attribution_v1.staging").exists()


def test_report_contains_every_failure_axis_and_volume_context(tmp_path):
    payload = json.loads(runner(tmp_path).run("manifest.json", "screening.json").report_path.read_bytes())
    adx = payload["strategy_evidence"]["adx"]
    baseline = adx["profiles"]["baseline"]
    btc = baseline["attribution"]["assets"]["BTC-USD"]
    assert set(adx["profiles"]) == {"zero_cost", "baseline", "stress"}
    assert set(btc) == {"cost_turnover", "drawdown", "exposure_holding", "market_regime", "volume"}
    assert btc["market_regime"]["signal_bar_attribution"] is True
    assert btc["volume"]["signal_bar_attribution"] is True
    assert "entry_context" in btc["volume"]
    assert "obv_directions" in btc["volume"]
    assert baseline["evaluation"]["raw_trade_level_evidence_persisted"] is False
    assert baseline["evaluation"]["raw_evaluation_sha256"]


def test_cross_profile_attribution_identifies_cost_survival_without_ranking(tmp_path):
    payload = json.loads(runner(tmp_path).run("manifest.json", "screening.json").report_path.read_bytes())
    btc = payload["strategy_evidence"]["adx"]["cross_profile_attribution"]["assets"]["BTC-USD"]
    assert btc["oos_strategy_return"]["zero_cost"] == pytest.approx(0.05)
    assert btc["oos_strategy_return"]["baseline"] == pytest.approx(-0.03)
    assert btc["oos_strategy_return"]["stress"] == pytest.approx(-0.08)
    assert btc["zero_to_baseline_oos_return_change"] == pytest.approx(-0.08)
    assert btc["baseline_to_stress_oos_return_change"] == pytest.approx(-0.05)
    assert "ZERO_COST_OOS_RETURN_POSITIVE" in btc["diagnostic_flags"]
    assert "BASELINE_COST_SURVIVAL_FAILED" in btc["diagnostic_flags"]
    assert "BASELINE_WALK_FORWARD_PERSISTENCE_FAILED" in btc["diagnostic_flags"]
    assert payload["interpretation"]["ranking"] == "PROHIBITED"
    assert "ranking" not in payload["strategy_evidence"]["adx"]


def test_cross_profile_flags_absent_gross_signal_when_zero_cost_is_negative(tmp_path):
    FakeValidator.overrides[("adx", "zero_cost")] = -0.01
    payload = json.loads(runner(tmp_path).run("manifest.json", "screening.json").report_path.read_bytes())
    btc = payload["strategy_evidence"]["adx"]["cross_profile_attribution"]["assets"]["BTC-USD"]
    assert "NO_POSITIVE_ZERO_COST_OOS_RETURN" in btc["diagnostic_flags"]
    assert "ZERO_COST_OOS_RETURN_POSITIVE" not in btc["diagnostic_flags"]


def test_runner_refuses_existing_final_or_staging_evidence(tmp_path):
    first = runner(tmp_path)
    first.output_directory.mkdir(parents=True)
    with pytest.raises(FileExistsError, match="already exists"):
        first.run("manifest.json", "screening.json")
    second = FailureAttributionRunner(output_root=tmp_path / "other", preregistration=FakePreregistration(), validator_factory=FakeValidator)
    second.staging_directory.mkdir(parents=True)
    with pytest.raises(FileExistsError, match="staging"):
        second.run("manifest.json", "screening.json")


def test_runner_validates_locked_hash_scope_and_configuration(tmp_path):
    wrong_hash = FakePreregistration(manifest_sha256="0" * 64)
    with pytest.raises(ValueError, match="manifest"):
        runner(tmp_path, preregistration=wrong_hash).run("manifest.json", "screening.json")
    wrong_scope = FakePreregistration()
    wrong_scope.locked.strategy_engines = {"adx": SimpleNamespace(strategy_name="adx")}
    with pytest.raises(ValueError, match="strategy"):
        runner(tmp_path, preregistration=wrong_scope).run("manifest.json", "screening.json")
    wrong_config = FakePreregistration()
    wrong_config.locked.attribution_configuration = {"drift": True}
    with pytest.raises(ValueError, match="configuration"):
        runner(tmp_path, preregistration=wrong_config).run("manifest.json", "screening.json")


def test_failure_before_completion_leaves_no_final_or_staging_evidence(tmp_path):
    class FailingValidator(FakeValidator):
        def run(self, assets):
            raise RuntimeError("diagnostic failure")
    instance = runner(tmp_path, validator_factory=FailingValidator)
    with pytest.raises(RuntimeError, match="diagnostic failure"):
        instance.run("manifest.json", "screening.json")
    assert not instance.output_directory.exists()
    assert not instance.staging_directory.exists()


def test_runner_is_deterministic_across_independent_output_roots(tmp_path):
    first = runner(tmp_path / "first").run("manifest.json", "screening.json")
    FakeValidator.calls = []
    second = runner(tmp_path / "second").run("manifest.json", "screening.json")
    assert first.report_sha256 == second.report_sha256
    assert first.report_path.read_bytes() == second.report_path.read_bytes()


def test_cli_records_summary_without_authorization(tmp_path, capsys, monkeypatch):
    instance = runner(tmp_path)
    monkeypatch.setattr(runner_module, "FailureAttributionRunner", lambda: instance)
    assert main(["--manifest", "manifest.json", "--screening-report", "screening.json"]) == 0
    output = json.loads(capsys.readouterr().out)
    assert output["status"] == "FAILURE_ATTRIBUTION_RECORDED"
    assert output["diagnostic_multi_asset_replays"] == 24
    assert output["automatic_ranking_generated"] is False
    assert output["automatic_strategy_selection"] is False
    assert output["new_alpha_hypothesis_generated"] is False
    assert output["candidate_v2_authorized"] is False
    assert output["bounded_forward_paper_authorized"] is False
    assert output["live_execution_authorized"] is False


def test_cli_requires_both_frozen_inputs():
    with pytest.raises(SystemExit):
        main(["--manifest", "manifest.json"])
