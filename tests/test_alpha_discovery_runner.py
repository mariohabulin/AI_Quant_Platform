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

from alpha_discovery_protocol import (
    ALPHA_DISCOVERY_ID,
    ASSET_SCOPE,
    CALIBRATION_PARAMETER_CATALOG,
    PARAMETER_SET_ORDER,
    RECORDED_ALPHA_DEVELOPMENT_REPORT_SHA256,
    alpha_discovery_configuration,
)
from alpha_discovery_runner import (
    AlphaDiscoveryCalibrationRunner,
    AlphaDiscoveryWindowEvaluator,
)
from first_strategy_candidate import BASELINE_COSTS
from research_evidence import canonical_json_bytes
from strategy_family_screening import DEVELOPMENT_MANIFEST_SHA256
import alpha_discovery_runner as runner_module


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


def locked_discovery(rows=11076):
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
        alpha_development_report={"status": "ALPHA_DEVELOPMENT_COMPLETED"},
        alpha_development_report_sha256=(
            RECORDED_ALPHA_DEVELOPMENT_REPORT_SHA256
        ),
        configuration=alpha_discovery_configuration(),
    )


class FakePreregistration:
    def __init__(self, locked=None):
        self.locked = locked or locked_discovery()
        self.calls = []

    def lock(self, manifest_path, alpha_report_path):
        self.calls.append((str(manifest_path), str(alpha_report_path)))
        return self.locked


class FakeDiagnosticEvaluator:
    def __init__(self, valid=True):
        self.valid = valid
        self.calls = 0

    def run(self, locked):
        self.calls += 1
        if not self.valid:
            return {"status": "BAD"}
        return {
            "status": "ZERO_COST_TRADE_PATH_DIAGNOSTIC_COMPLETED",
            "variant_order": [
                "adx_high_relative_volume",
                "adx_bullish_normal_high_relative_volume",
                "adx_bullish_normal_high_relative_volume_obv_rising",
            ],
            "multi_asset_replays": 3,
            "zero_cost_may_select_parameters": False,
            "raw_trade_paths_persisted": False,
            "variants": {},
        }


class FakeWindowEvaluator:
    def __init__(self, eligible_parameter=None):
        self.eligible_parameter = eligible_parameter
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
        stressed = "stress" in cost_profile.label
        strategy_return = (0.01 if stressed else 0.02) if positive else -0.01
        return {
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


def load_recorded(output_root):
    report = output_root / "discovery_v1" / "alpha_discovery_report.json"
    checksum = output_root / "discovery_v1" / "alpha_discovery_report.sha256"
    payload = json.loads(report.read_bytes())
    digest = hashlib.sha256(report.read_bytes()).hexdigest()
    assert report.read_bytes() == canonical_json_bytes(payload)
    assert checksum.read_bytes() == f"{digest}  {report.name}\n".encode("ascii")
    return payload, digest


def test_runner_selects_only_from_prior_inner_windows_and_records_atomically(tmp_path):
    selected = PARAMETER_SET_ORDER[0]
    preregistration = FakePreregistration()
    diagnostic = FakeDiagnosticEvaluator()
    evaluator = FakeWindowEvaluator(eligible_parameter=selected)
    runner = AlphaDiscoveryCalibrationRunner(
        output_root=tmp_path,
        preregistration=preregistration,
        diagnostic_evaluator=diagnostic,
        window_evaluator=evaluator,
    )

    recorded = runner.run("manifest.json", "alpha_report.json")
    payload, digest = load_recorded(tmp_path)
    report_bytes = recorded.report_path.read_bytes()

    assert recorded.report_sha256 == digest
    assert recorded.outer_window_count == 7
    assert recorded.selected_outer_windows == 7
    assert recorded.hold_cash_outer_windows == 0
    assert diagnostic.calls == 1
    assert payload["status"] == "ALPHA_DISCOVERY_COMPLETED"
    assert payload["alpha_discovery_id"] == ALPHA_DISCOVERY_ID
    assert payload["parameter_set_order"] == list(PARAMETER_SET_ORDER)
    assert payload["nested_calibration_executed"] is True
    assert payload["parameter_selection_executed"] is True
    assert payload["outer_development_test_executed"] is True
    assert payload["global_hindsight_leaderboard_generated"] is False
    assert payload["candidate_v2_authorized"] is False
    assert payload["bounded_forward_paper_authorized"] is False
    assert payload["live_execution_authorized"] is False
    assert b'"trade_history"' not in report_bytes
    assert b'"equity_curve"' not in report_bytes
    assert not (tmp_path / ".discovery_v1.staging").exists()

    outer_windows = payload["nested_calibration"]["outer_windows"]
    assert len(outer_windows) == 7
    for window in outer_windows:
        assert window["selection"]["selected_parameter_set_id"] == selected
        assert window["selection_cutoff"] == window["outer_test_start"]
        assert window["outer_test_available_to_selection"] is False
        assert all(
            item["inner_validation_end"] <= window["selection_cutoff"]
            for item in window["inner_windows"]
        )
        assert window["outer_evaluation"]["action"] == "EXECUTE_SELECTED"

    inner_calls = [call for call in evaluator.calls if call["phase"] == "INNER"]
    outer_calls = [call for call in evaluator.calls if call["phase"] == "OUTER"]
    assert len(inner_calls) == 10 * 8 * 2
    assert len(outer_calls) == 7 * 2
    assert {call["parameter_set_id"] for call in outer_calls} == {selected}


def test_runner_holds_cash_when_complete_catalog_has_no_eligible_member(tmp_path):
    evaluator = FakeWindowEvaluator(eligible_parameter=None)
    runner = AlphaDiscoveryCalibrationRunner(
        output_root=tmp_path,
        preregistration=FakePreregistration(),
        diagnostic_evaluator=FakeDiagnosticEvaluator(),
        window_evaluator=evaluator,
    )

    recorded = runner.run("manifest.json", "alpha_report.json")
    payload, _ = load_recorded(tmp_path)

    assert recorded.selected_outer_windows == 0
    assert recorded.hold_cash_outer_windows == 7
    assert not any(call["phase"] == "OUTER" for call in evaluator.calls)
    for window in payload["nested_calibration"]["outer_windows"]:
        assert window["selection"]["hold_cash"] is True
        assert window["outer_evaluation"] == {
            "action": "HOLD_CASH",
            "parameter_set_id": None,
            "profiles": {},
        }


def test_runner_refuses_repeat_staging_and_invalid_diagnostic(tmp_path):
    common = {
        "output_root": tmp_path,
        "preregistration": FakePreregistration(),
        "diagnostic_evaluator": FakeDiagnosticEvaluator(),
        "window_evaluator": FakeWindowEvaluator(PARAMETER_SET_ORDER[0]),
    }
    runner = AlphaDiscoveryCalibrationRunner(**common)
    runner.run("manifest.json", "alpha_report.json")
    with pytest.raises(FileExistsError, match="already exists"):
        runner.run("manifest.json", "alpha_report.json")

    other = tmp_path / "other"
    (other / ".discovery_v1.staging").mkdir(parents=True)
    with pytest.raises(FileExistsError, match="staging"):
        AlphaDiscoveryCalibrationRunner(
            output_root=other,
            preregistration=FakePreregistration(),
            diagnostic_evaluator=FakeDiagnosticEvaluator(),
            window_evaluator=FakeWindowEvaluator(PARAMETER_SET_ORDER[0]),
        ).run("manifest.json", "alpha_report.json")

    invalid = tmp_path / "invalid"
    with pytest.raises(ValueError, match="diagnostic"):
        AlphaDiscoveryCalibrationRunner(
            output_root=invalid,
            preregistration=FakePreregistration(),
            diagnostic_evaluator=FakeDiagnosticEvaluator(valid=False),
            window_evaluator=FakeWindowEvaluator(PARAMETER_SET_ORDER[0]),
        ).run("manifest.json", "alpha_report.json")
    assert not (invalid / "discovery_v1").exists()
    assert not (invalid / ".discovery_v1.staging").exists()


class OneTradeStrategy:
    def __init__(self, parameter_set):
        self.parameter_set = parameter_set
        self.name = f"prepared_{parameter_set.parameter_set_id}"
        self.required_features = []

    def configuration(self):
        return {"parameter_set_id": self.parameter_set.parameter_set_id}

    def generate_signals(self, data, evaluation_start_position=0):
        result = data.copy()
        result["Signal"] = 0
        result.iloc[evaluation_start_position, result.columns.get_loc("Signal")] = 1
        result["ALPHA_V2_ATR_RISK_DISTANCE"] = 2.0
        result["ALPHA_V2_REWARD_RISK_RATIO"] = 3.0
        return result


def identity_features(data, required_features=None):
    return data.copy(deep=True)


def test_real_window_evaluator_uses_history_for_features_but_trades_only_window():
    rows = 12
    assets = {asset: market(rows) for asset in ASSET_SCOPE}
    evaluator = AlphaDiscoveryWindowEvaluator(
        strategy_factory=OneTradeStrategy,
        feature_generator=identity_features,
    )

    result = evaluator.evaluate(
        CALIBRATION_PARAMETER_CATALOG[0],
        assets,
        start_position=5,
        end_position=10,
        cost_profile=BASELINE_COSTS,
        phase="INNER",
        window_id="inner-5-10",
    )

    assert tuple(result) == ASSET_SCOPE
    for evidence in result.values():
        assert evidence["window_start_position"] == 5
        assert evidence["window_end_position"] == 10
        assert evidence["window_rows"] == 5
        assert evidence["completed_trades"] == 1
        assert evidence["protective_policy_active"] is True
        assert evidence["raw_trade_level_evidence_persisted"] is False
        assert len(evidence["raw_partition_sha256"]) == 64


def test_trade_path_diagnostic_summary_is_bounded_and_validated():
    summary = runner_module.AlphaDiscoveryDiagnosticEvaluator._trade_path_summary(
        [
            {
                "maximum_favorable_excursion_r": 2.0,
                "maximum_adverse_excursion_r": 0.5,
                "realized_r": 1.0,
                "holding_bars": 4,
                "bars_to_maximum_favorable_excursion": 2,
                "exit_reason": "SIGNAL",
            },
            {
                "maximum_favorable_excursion_r": 1.0,
                "maximum_adverse_excursion_r": 1.0,
                "realized_r": -1.0,
                "holding_bars": 2,
                "bars_to_maximum_favorable_excursion": 1,
                "exit_reason": "PROTECTIVE_STOP",
            },
        ]
    )

    assert summary["trade_count"] == 2
    assert summary["median_maximum_favorable_excursion_r"] == pytest.approx(1.5)
    assert summary["median_realized_r"] == pytest.approx(0.0)
    assert summary["exit_reason_counts"]["SIGNAL"] == 1
    assert summary["exit_reason_counts"]["PROTECTIVE_STOP"] == 1
    assert summary["raw_trade_paths_persisted"] is False

    with pytest.raises(ValueError, match="exit reason"):
        runner_module.AlphaDiscoveryDiagnosticEvaluator._trade_path_summary(
            [
                {
                    "maximum_favorable_excursion_r": 1.0,
                    "maximum_adverse_excursion_r": 0.5,
                    "realized_r": 0.0,
                    "holding_bars": 1,
                    "bars_to_maximum_favorable_excursion": 1,
                    "exit_reason": "UNKNOWN",
                }
            ]
        )


def test_cli_runs_once_and_prints_recorded_state(monkeypatch, capsys, tmp_path):
    recorded = runner_module.RecordedAlphaDiscovery(
        report_path=tmp_path / "alpha_discovery_report.json",
        checksum_path=tmp_path / "alpha_discovery_report.sha256",
        report_sha256="f" * 64,
        outer_window_count=7,
        selected_outer_windows=2,
        hold_cash_outer_windows=5,
    )
    calls = []

    class FakeRunner:
        def run(self, manifest_path, alpha_report_path):
            calls.append((manifest_path, alpha_report_path))
            return recorded

    monkeypatch.setattr(
        runner_module, "AlphaDiscoveryCalibrationRunner", FakeRunner
    )
    assert runner_module.main(
        ["--manifest", "manifest.json", "--alpha-report", "alpha.json"]
    ) == 0
    output = json.loads(capsys.readouterr().out)

    assert calls == [("manifest.json", "alpha.json")]
    assert output["status"] == "ALPHA_DISCOVERY_RECORDED"
    assert output["outer_window_count"] == 7
    assert output["candidate_v2_authorized"] is False
    assert output["bounded_forward_paper_authorized"] is False
    assert output["live_execution_authorized"] is False
