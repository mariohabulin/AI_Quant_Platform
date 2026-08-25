import hashlib
import json
import os
from pathlib import Path
from types import SimpleNamespace
import sys

import numpy as np
import pandas as pd
import pytest

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src")))

from alpha_discovery_protocol import ASSET_SCOPE
from first_strategy_candidate import BASELINE_COSTS, STRESSED_COSTS
from research_evidence import canonical_json_bytes
from strategy_family_screening import DEVELOPMENT_MANIFEST_SHA256
from trend_pullback_volume_protocol import (
    RECORDED_ALPHA_DISCOVERY_REPORT_SHA256,
    TREND_PULLBACK_DEVELOPMENT_ID,
    TREND_PULLBACK_PARAMETER_CATALOG,
    TREND_PULLBACK_PARAMETER_CATALOG_SHA256,
    TREND_PULLBACK_PARAMETER_ORDER,
    trend_pullback_configuration,
)
from trend_pullback_volume_runner import (
    TrendPullbackSelectionPolicy,
    TrendPullbackWindowEvaluator,
    TrendPullbackVolumeDevelopmentRunner,
    main,
    trend_pullback_protective_exit_policy,
    trend_pullback_risk_engine,
)
import trend_pullback_volume_runner as runner_module


def market(rows=11076):
    index = pd.date_range("2019-01-01T00:00:00Z", periods=rows, freq="6h")
    close = 100.0 + np.arange(rows, dtype=float) * 0.01
    return pd.DataFrame(
        {
            "Open": close,
            "High": close + 1.0,
            "Low": close - 1.0,
            "Close": close,
            "Volume": 1000.0,
        },
        index=index,
    )


def locked_development(rows=11076):
    return SimpleNamespace(
        contract=SimpleNamespace(
            dataset_id="coinbase-exchange-btc-eth-native-6h-20190101-20260801-v1",
            timeframe="6h",
            products=ASSET_SCOPE,
            as_dict=lambda: {
                "dataset_id": "coinbase-exchange-btc-eth-native-6h-20190101-20260801-v1",
                "timeframe": "6h",
                "products": list(ASSET_SCOPE),
            },
        ),
        assets={asset: market(rows) for asset in ASSET_SCOPE},
        manifest_sha256=DEVELOPMENT_MANIFEST_SHA256,
        alpha_discovery_report={"status": "ALPHA_DISCOVERY_COMPLETED"},
        alpha_discovery_report_sha256=(
            RECORDED_ALPHA_DISCOVERY_REPORT_SHA256
        ),
        configuration=trend_pullback_configuration(),
    )


class FakePreregistration:
    def __init__(self, locked=None, error=None):
        self.locked = locked or locked_development()
        self.error = error
        self.calls = []

    def lock(self, manifest_path, discovery_report_path):
        self.calls.append((str(manifest_path), str(discovery_report_path)))
        if self.error is not None:
            raise self.error
        return self.locked


class FakeWindowEvaluator:
    def __init__(self, eligible_parameter=None, invalid=False):
        self.eligible_parameter = eligible_parameter
        self.invalid = invalid
        self.calls = []

    def evaluate(
        self,
        parameter_set,
        assets,
        start_position,
        end_position,
        cost_profile,
        phase,
        window_id,
    ):
        self.calls.append(
            {
                "parameter_set_id": parameter_set.parameter_set_id,
                "start": start_position,
                "end": end_position,
                "profile": cost_profile.label,
                "phase": phase,
                "window_id": window_id,
            }
        )
        positive = parameter_set.parameter_set_id == self.eligible_parameter
        stressed = cost_profile.label == STRESSED_COSTS.label
        strategy_return = (0.01 if stressed else 0.02) if positive else -0.01
        result = {
            asset: {
                "asset": asset,
                "phase": phase,
                "window_id": window_id,
                "window_start_position": start_position,
                "window_end_position": end_position,
                "window_rows": end_position - start_position,
                "parameter_set_id": parameter_set.parameter_set_id,
                "cost_profile": cost_profile.as_dict(),
                "strategy_return": strategy_return,
                "maximum_drawdown_percent": 5.0,
                "completed_trades": 4,
                "annualized_turnover_multiple": 2.0,
                "annualized_cost_fraction": 0.02 if not stressed else 0.03,
                "protective_policy_active": True,
                "raw_partition_sha256": "a" * 64,
                "raw_partition_canonical_bytes": 100,
                "raw_trade_level_evidence_persisted": False,
            }
            for asset in ASSET_SCOPE
        }
        if self.invalid:
            result["BTC-USD"]["protective_policy_active"] = False
        return result


def eligible_metrics(return_value=0.02):
    return {
        "baseline_median_net_return": return_value,
        "stress_median_net_return": return_value / 2.0,
        "baseline_positive_window_rate": 0.75,
        "stress_positive_window_rate": 0.75,
        "maximum_drawdown_percent": 5.0,
        "completed_trades": 16,
        "annualized_turnover_multiple": 2.0,
        "annualized_baseline_cost_fraction": 0.02,
        "protective_policy_active": True,
    }


def selection_evidence(eligible_id=None):
    result = {}
    for parameter_id in TREND_PULLBACK_PARAMETER_ORDER:
        value = 0.02 if parameter_id == eligible_id else -0.01
        result[parameter_id] = {
            asset: eligible_metrics(value) for asset in ASSET_SCOPE
        }
    return result


def load_recorded(output_root):
    report = output_root / "development_v1" / "trend_pullback_volume_report.json"
    checksum = output_root / "development_v1" / "trend_pullback_volume_report.sha256"
    payload = json.loads(report.read_bytes())
    digest = hashlib.sha256(report.read_bytes()).hexdigest()
    assert report.read_bytes() == canonical_json_bytes(payload)
    assert checksum.read_bytes() == f"{digest}  {report.name}\n".encode("ascii")
    return payload, digest


def test_risk_and_protective_policy_preserve_frozen_static_boundary():
    risk = trend_pullback_risk_engine()
    policy = trend_pullback_protective_exit_policy(
        TREND_PULLBACK_PARAMETER_CATALOG[0]
    )
    assert risk.risk_per_trade == pytest.approx(0.005)
    assert risk.max_position_fraction == pytest.approx(0.50)
    assert risk.max_drawdown_fraction == pytest.approx(0.20)
    assert risk.min_reward_risk == pytest.approx(3.0)
    assert policy.reward_risk_ratio == pytest.approx(3.0)
    assert policy.breakeven_trigger_r is None
    assert policy.stop_and_target_same_bar == "STOP_FIRST"
    assert policy.entry_bar_protection is True


def test_real_window_evaluator_wires_strategy_risk_and_protection_end_to_end():
    assets = {asset: market(400) for asset in ASSET_SCOPE}
    evidence = TrendPullbackWindowEvaluator().evaluate(
        TREND_PULLBACK_PARAMETER_CATALOG[0],
        assets,
        250,
        400,
        BASELINE_COSTS,
        "INNER",
        "integration-smoke",
    )

    assert tuple(sorted(evidence)) == ASSET_SCOPE
    for asset, item in evidence.items():
        assert item["asset"] == asset
        assert item["phase"] == "INNER"
        assert item["window_rows"] == 150
        assert item["protective_policy_active"] is True
        assert item["raw_trade_level_evidence_persisted"] is False
        assert len(item["raw_partition_sha256"]) == 64


def test_selection_policy_requires_complete_order_and_holds_cash():
    policy = TrendPullbackSelectionPolicy()
    result = policy.select(selection_evidence())
    assert result["status"] == "NO_ELIGIBLE_CONFIGURATION_HOLD_CASH"
    assert result["selected_parameter_set_id"] is None
    assert result["hold_cash"] is True
    assert result["outer_test_evidence_used"] is False
    assert result["global_hindsight_leaderboard_generated"] is False

    evidence = selection_evidence()
    evidence["unexpected"] = evidence.pop(TREND_PULLBACK_PARAMETER_ORDER[-1])
    with pytest.raises(ValueError, match="complete frozen catalog order"):
        policy.select(evidence)


def test_selection_policy_selects_only_member_passing_every_inner_gate():
    selected = TREND_PULLBACK_PARAMETER_ORDER[2]
    result = TrendPullbackSelectionPolicy().select(
        selection_evidence(selected)
    )
    assert result["status"] == "DEVELOPMENT_CONFIGURATION_SELECTED"
    assert result["selected_parameter_set_id"] == selected
    assert result["records"][selected]["eligible"] is True
    assert all(result["records"][selected]["gates"].values())


def test_runner_uses_only_prior_inner_windows_and_records_atomically(tmp_path):
    selected = TREND_PULLBACK_PARAMETER_ORDER[0]
    evaluator = FakeWindowEvaluator(eligible_parameter=selected)
    runner = TrendPullbackVolumeDevelopmentRunner(
        output_root=tmp_path,
        preregistration=FakePreregistration(),
        window_evaluator=evaluator,
    )

    recorded = runner.run("manifest.json", "discovery_report.json")
    payload, digest = load_recorded(tmp_path)
    report_bytes = recorded.report_path.read_bytes()

    assert recorded.report_sha256 == digest
    assert recorded.outer_window_count == 7
    assert recorded.selected_outer_windows == 7
    assert recorded.hold_cash_outer_windows == 0
    assert payload["status"] == "TREND_PULLBACK_VOLUME_DEVELOPMENT_COMPLETED"
    assert payload["development_id"] == TREND_PULLBACK_DEVELOPMENT_ID
    assert payload["parameter_set_order"] == list(
        TREND_PULLBACK_PARAMETER_ORDER
    )
    assert payload["parameter_catalog_sha256"] == (
        TREND_PULLBACK_PARAMETER_CATALOG_SHA256
    )
    assert payload["nested_development_evaluation_executed"] is True
    assert payload["parameter_selection_executed"] is True
    assert payload["global_hindsight_leaderboard_generated"] is False
    assert payload["candidate_v2_authorized"] is False
    assert payload["bounded_forward_paper_authorized"] is False
    assert payload["live_execution_authorized"] is False
    assert b'"trade_history"' not in report_bytes
    assert b'"equity_curve"' not in report_bytes
    assert not (tmp_path / ".development_v1.staging").exists()

    outer_windows = payload["nested_development"]["outer_windows"]
    assert len(outer_windows) == 7
    for window in outer_windows:
        assert window["selection"]["selected_parameter_set_id"] == selected
        assert window["selection_cutoff"] == window["outer_test_start"]
        assert window["outer_test_available_to_selection"] is False
        assert all(
            inner["inner_validation_end"] <= window["selection_cutoff"]
            for inner in window["inner_windows"]
        )
        assert window["outer_evaluation"]["action"] == "EXECUTE_SELECTED"

    inner_calls = [call for call in evaluator.calls if call["phase"] == "INNER"]
    outer_calls = [call for call in evaluator.calls if call["phase"] == "OUTER"]
    assert len(inner_calls) == 10 * 4 * 2
    assert len(outer_calls) == 7 * 2
    assert {call["parameter_set_id"] for call in outer_calls} == {selected}


def test_runner_holds_cash_without_executing_any_outer_strategy(tmp_path):
    evaluator = FakeWindowEvaluator()
    runner = TrendPullbackVolumeDevelopmentRunner(
        output_root=tmp_path,
        preregistration=FakePreregistration(),
        window_evaluator=evaluator,
    )
    recorded = runner.run("manifest.json", "discovery_report.json")
    payload, _ = load_recorded(tmp_path)

    assert recorded.selected_outer_windows == 0
    assert recorded.hold_cash_outer_windows == 7
    assert not any(call["phase"] == "OUTER" for call in evaluator.calls)
    for window in payload["nested_development"]["outer_windows"]:
        assert window["selection"]["hold_cash"] is True
        assert window["outer_evaluation"] == {
            "action": "HOLD_CASH",
            "parameter_set_id": None,
            "profiles": {},
        }


def test_runner_refuses_repeat_or_stale_staging_evidence(tmp_path):
    (tmp_path / "development_v1").mkdir()
    runner = TrendPullbackVolumeDevelopmentRunner(
        output_root=tmp_path,
        preregistration=FakePreregistration(),
        window_evaluator=FakeWindowEvaluator(),
    )
    with pytest.raises(FileExistsError, match="already exists"):
        runner.run("manifest.json", "discovery_report.json")

    (tmp_path / "development_v1").rmdir()
    (tmp_path / ".development_v1.staging").mkdir()
    with pytest.raises(FileExistsError, match="staging evidence"):
        runner.run("manifest.json", "discovery_report.json")


def test_runner_locks_evidence_before_any_market_evaluation(tmp_path):
    preregistration = FakePreregistration(error=ValueError("lock failed"))
    evaluator = FakeWindowEvaluator()
    runner = TrendPullbackVolumeDevelopmentRunner(
        output_root=tmp_path,
        preregistration=preregistration,
        window_evaluator=evaluator,
    )
    with pytest.raises(ValueError, match="lock failed"):
        runner.run("manifest.json", "discovery_report.json")
    assert evaluator.calls == []
    assert not (tmp_path / "development_v1").exists()
    assert not (tmp_path / ".development_v1.staging").exists()


def test_runner_rejects_locked_configuration_or_window_evidence_drift(tmp_path):
    locked = locked_development()
    locked.configuration = {"changed": True}
    runner = TrendPullbackVolumeDevelopmentRunner(
        output_root=tmp_path / "configuration",
        preregistration=FakePreregistration(locked=locked),
        window_evaluator=FakeWindowEvaluator(),
    )
    with pytest.raises(ValueError, match="configuration changed"):
        runner.run("manifest.json", "discovery_report.json")

    runner = TrendPullbackVolumeDevelopmentRunner(
        output_root=tmp_path / "window",
        preregistration=FakePreregistration(),
        window_evaluator=FakeWindowEvaluator(invalid=True),
    )
    with pytest.raises(ValueError, match="safety validation"):
        runner.run("manifest.json", "discovery_report.json")


def test_runner_constructor_requires_reviewed_collaborators(tmp_path):
    with pytest.raises(TypeError, match="Preregistration"):
        TrendPullbackVolumeDevelopmentRunner(
            output_root=tmp_path,
            preregistration=object(),
        )


def test_cli_records_runner_summary_without_authorizing_deployment(
    monkeypatch, capsys
):
    class FakeRunner:
        def run(self, manifest, discovery_report):
            assert manifest == "manifest.json"
            assert discovery_report == "discovery.json"
            return SimpleNamespace(
                as_dict=lambda: {
                    "status": "TREND_PULLBACK_VOLUME_DEVELOPMENT_RECORDED",
                    "candidate_v2_authorized": False,
                    "bounded_forward_paper_authorized": False,
                    "live_execution_authorized": False,
                }
            )

    monkeypatch.setattr(
        runner_module, "TrendPullbackVolumeDevelopmentRunner", FakeRunner
    )
    assert main(
        [
            "--manifest",
            "manifest.json",
            "--discovery-report",
            "discovery.json",
        ]
    ) == 0
    output = json.loads(capsys.readouterr().out)
    assert output["candidate_v2_authorized"] is False
    assert output["bounded_forward_paper_authorized"] is False
    assert output["live_execution_authorized"] is False
