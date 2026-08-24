import hashlib
import json
import os
from pathlib import Path
from types import SimpleNamespace
import sys

import pandas as pd
import pytest

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src")))

import alpha_discovery_protocol as discovery_module
from alpha_development_protocol import ALPHA_DEVELOPMENT_ID, VARIANT_ORDER
from alpha_discovery_protocol import (
    ALPHA_DISCOVERY_ID,
    ALPHA_DISCOVERY_SCHEMA_VERSION,
    ASSET_SCOPE,
    CALIBRATION_PARAMETER_CATALOG,
    PARAMETER_CATALOG_VERSION,
    PARAMETER_SET_ORDER,
    RECORDED_ALPHA_DEVELOPMENT_REPORT_SHA256,
    AlphaCalibrationParameterSet,
    AlphaCalibrationSelectionPolicy,
    AlphaDiscoveryPreregistration,
    NestedCalibrationConfig,
    NestedCalibrationPlanner,
    alpha_calibration_parameter_catalog,
    alpha_discovery_configuration,
    load_recorded_alpha_development_report,
    main,
    parameter_catalog_fingerprint,
)
from research_evidence import canonical_json_bytes
from strategy_family_screening import DEVELOPMENT_MANIFEST_SHA256


PASSED_DEVELOPMENT_GATES = {
    "minimum_walk_forward_windows": True,
    "minimum_development_trades_per_asset": True,
    "oos_drawdown_within_limit": True,
    "annual_turnover_within_budget": True,
    "annual_baseline_cost_within_budget": True,
    "protective_exit_policy_active_all_scenarios": True,
}
FAILED_DEVELOPMENT_GATES = {
    "baseline_multi_asset_validated": False,
    "cost_stress_multi_asset_validated": False,
    "baseline_positive_oos_return_both_assets": False,
}


def alpha_development_payload():
    variant_evidence = {}
    for variant_id in VARIANT_ORDER:
        variant_evidence[variant_id] = {
            "development_review": {
                "outcome": "SCREEN_OUT",
                "gates": {
                    **FAILED_DEVELOPMENT_GATES,
                    **PASSED_DEVELOPMENT_GATES,
                },
                "failed_gates": list(FAILED_DEVELOPMENT_GATES),
            }
        }
    return {
        "schema_version": 1,
        "status": "ALPHA_DEVELOPMENT_COMPLETED",
        "alpha_development_id": ALPHA_DEVELOPMENT_ID,
        "manifest_sha256": DEVELOPMENT_MANIFEST_SHA256,
        "dataset_role": "INSPECTED_DEVELOPMENT_ONLY",
        "variant_order": list(VARIANT_ORDER),
        "variant_count": 3,
        "scenario_count": 3,
        "joint_multi_asset_evaluations": 9,
        "variant_evidence": variant_evidence,
        "comparison": {
            "outcome_counts": {
                "INCONCLUSIVE": 0,
                "MECHANISM_RETAINS_DEVELOPMENT_INTEREST": 0,
                "SCREEN_OUT": 3,
            },
            "mechanisms_retaining_interest": [],
        },
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


def write_alpha_report(directory, mutate=None):
    directory.mkdir()
    payload = alpha_development_payload()
    if mutate is not None:
        mutate(payload)
    report = directory / "alpha_development_report.json"
    report_bytes = canonical_json_bytes(payload)
    digest = hashlib.sha256(report_bytes).hexdigest()
    report.write_bytes(report_bytes)
    report.with_name("alpha_development_report.sha256").write_bytes(
        f"{digest}  {report.name}\n".encode("ascii")
    )
    return report, digest


class FakeDatasetLock:
    def __init__(self, manifest_sha256=DEVELOPMENT_MANIFEST_SHA256):
        self.manifest_sha256 = manifest_sha256

    def lock(self, manifest_path):
        frame = pd.DataFrame({"Close": [1.0, 2.0]})
        return SimpleNamespace(
            manifest_sha256=self.manifest_sha256,
            assets={"BTC-USD": frame, "ETH-USD": frame.copy()},
        )


def fake_alpha_loader(payload=None, digest=RECORDED_ALPHA_DEVELOPMENT_REPORT_SHA256):
    payload = payload or alpha_development_payload()

    def load(path, expected_sha256):
        assert expected_sha256 == RECORDED_ALPHA_DEVELOPMENT_REPORT_SHA256
        return payload, digest

    return load


def asset_metrics(**overrides):
    values = {
        "baseline_median_net_return": 0.04,
        "stress_median_net_return": 0.02,
        "baseline_positive_window_rate": 0.75,
        "stress_positive_window_rate": 0.75,
        "maximum_drawdown_percent": 10.0,
        "completed_trades": 20,
        "annualized_turnover_multiple": 4.0,
        "annualized_baseline_cost_fraction": 0.03,
        "protective_policy_active": True,
    }
    values.update(overrides)
    return values


def complete_inner_evidence(**overrides):
    result = {}
    for parameter_id in PARAMETER_SET_ORDER:
        result[parameter_id] = {
            asset: asset_metrics() for asset in ASSET_SCOPE
        }
    for parameter_id, asset_changes in overrides.items():
        for asset, changes in asset_changes.items():
            result[parameter_id][asset].update(changes)
    return result


def test_parameter_catalog_is_exact_bounded_ordered_and_volume_mandatory():
    catalog = alpha_calibration_parameter_catalog()
    assert catalog == CALIBRATION_PARAMETER_CATALOG
    assert len(catalog) == 8
    assert len(set(PARAMETER_SET_ORDER)) == 8
    assert tuple(item.parameter_set_id for item in catalog) == PARAMETER_SET_ORDER
    assert {item.adx_entry_threshold for item in catalog} == {20.0, 25.0}
    assert {item.adx_exit_threshold for item in catalog} == {15.0, 20.0}
    assert {item.atr_risk_distance_multiple for item in catalog} == {1.5, 2.0}
    assert {item.breakeven_trigger_r for item in catalog} == {None, 1.0}
    assert {item.reward_risk_ratio for item in catalog} == {3.0}
    for item in catalog:
        payload = item.as_dict()
        assert payload["required_volume_regime"] == "HIGH"
        assert payload["volume_baseline_lag"] == 1
        assert payload["required_market_regime"] == "BULLISH_NORMAL"
        assert payload["obv_role"] == "DIAGNOSTIC_ONLY_NOT_ENTRY_GATE"
        assert "EMA_200" in payload["trend_structure"]


@pytest.mark.parametrize(
    "changes, message",
    [
        ({"parameter_set_id": "unknown"}, "catalog v1 syntax"),
        ({"adx_entry_threshold": 21.0}, "two frozen ADX bands"),
        ({"adx_exit_threshold": 25.0}, "below entry"),
        ({"atr_risk_distance_multiple": 2.5}, "1.5 or 2.0"),
        ({"breakeven_trigger_r": 2.0}, "1R break-even"),
        ({"reward_risk_ratio": 2.0}, "3:1 target"),
        ({"required_volume_regime": "NORMAL"}, "HIGH relative volume"),
        ({"volume_baseline_lag": 0}, "positive integer"),
        ({"ema_fast_period": 250}, "below slow"),
    ],
)
def test_parameter_set_fails_closed_on_catalog_drift(changes, message):
    values = {
        "parameter_set_id": "adx20-15-atr1p5-static3r",
        "adx_entry_threshold": 20.0,
        "adx_exit_threshold": 15.0,
        "atr_risk_distance_multiple": 1.5,
        "breakeven_trigger_r": None,
    }
    values.update(changes)
    with pytest.raises((TypeError, ValueError), match=message):
        AlphaCalibrationParameterSet(**values)


def test_parameter_catalog_fingerprint_is_canonical_and_order_sensitive():
    digest = parameter_catalog_fingerprint()
    assert len(digest) == 64
    assert digest == parameter_catalog_fingerprint()
    assert digest != parameter_catalog_fingerprint(
        tuple(reversed(CALIBRATION_PARAMETER_CATALOG))
    )


def test_nested_configuration_freezes_non_overlapping_bounded_windows():
    configuration = NestedCalibrationConfig()
    assert configuration.outer_train_size == 5760
    assert configuration.outer_test_size == 720
    assert configuration.outer_step_size == 720
    assert configuration.inner_train_size == 2880
    assert configuration.inner_validation_size == 720
    assert configuration.max_recent_inner_windows == 4
    assert configuration.minimum_outer_windows == 5
    assert configuration.minimum_positive_inner_window_rate == pytest.approx(0.60)
    assert configuration.maximum_annual_turnover_multiple == pytest.approx(12.0)
    assert configuration.maximum_annual_baseline_cost_fraction == pytest.approx(0.10)


@pytest.mark.parametrize(
    "changes, message",
    [
        ({"outer_step_size": 719}, "must not overlap"),
        ({"inner_step_size": 719}, "must not overlap"),
        ({"outer_train_size": 3000}, "cannot contain"),
        ({"minimum_positive_inner_window_rate": 1.1}, "at most"),
        ({"maximum_annual_baseline_cost_fraction": 1.1}, "at most"),
    ],
)
def test_nested_configuration_rejects_leakage_or_invalid_limits(changes, message):
    with pytest.raises(ValueError, match=message):
        NestedCalibrationConfig(**changes)


def test_nested_planner_builds_seven_outer_tests_and_only_prior_inner_windows():
    plan = NestedCalibrationPlanner().plan(11076)
    assert plan["outer_window_count"] == 7
    assert plan["unused_terminal_rows"] == 276
    assert plan["selection_scope"] == "INNER_VALIDATION_ONLY"
    assert plan["outer_test_used_for_selection"] is False

    first = plan["windows"][0]
    assert first["outer_train_start"] == 0
    assert first["outer_train_end"] == 5760
    assert first["outer_test_start"] == 5760
    assert first["outer_test_end"] == 6480
    assert len(first["inner_windows"]) == 4
    assert first["inner_windows"][-1]["inner_validation_end"] == 5760

    previous_test_end = None
    for window in plan["windows"]:
        assert window["selection_cutoff"] == window["outer_test_start"]
        assert window["outer_test_available_to_selection"] is False
        assert all(
            inner["inner_validation_end"] <= window["selection_cutoff"]
            for inner in window["inner_windows"]
        )
        if previous_test_end is not None:
            assert window["outer_test_start"] >= previous_test_end
        previous_test_end = window["outer_test_end"]


def test_nested_planner_requires_minimum_outer_coverage_and_integer_rows():
    planner = NestedCalibrationPlanner()
    with pytest.raises(ValueError, match="minimum outer coverage"):
        planner.plan(9000)
    with pytest.raises(ValueError, match="positive integer"):
        planner.plan(True)


def test_selection_policy_selects_best_eligible_robust_floor_from_inner_only():
    evidence = complete_inner_evidence(
        **{
            PARAMETER_SET_ORDER[1]: {
                "BTC-USD": {
                    "stress_median_net_return": 0.03,
                    "baseline_median_net_return": 0.05,
                },
                "ETH-USD": {
                    "stress_median_net_return": 0.03,
                    "baseline_median_net_return": 0.05,
                },
            }
        }
    )
    result = AlphaCalibrationSelectionPolicy().select(evidence)
    assert result["status"] == "CALIBRATION_CONFIGURATION_SELECTED"
    assert result["selected_parameter_set_id"] == PARAMETER_SET_ORDER[1]
    assert result["hold_cash"] is False
    assert result["selection_scope"] == "INNER_VALIDATION_ONLY"
    assert result["outer_test_evidence_used"] is False
    assert result["global_hindsight_leaderboard_generated"] is False


def test_selection_policy_uses_lower_turnover_then_catalog_order_for_ties():
    evidence = complete_inner_evidence()
    for asset in ASSET_SCOPE:
        evidence[PARAMETER_SET_ORDER[1]][asset][
            "annualized_turnover_multiple"
        ] = 3.0
    result = AlphaCalibrationSelectionPolicy().select(evidence)
    assert result["selected_parameter_set_id"] == PARAMETER_SET_ORDER[1]

    evidence = complete_inner_evidence()
    result = AlphaCalibrationSelectionPolicy().select(evidence)
    assert result["selected_parameter_set_id"] == PARAMETER_SET_ORDER[0]


@pytest.mark.parametrize(
    "metric, value, failed_gate",
    [
        (
            "baseline_median_net_return",
            -0.01,
            "positive_baseline_median_return_both_assets",
        ),
        (
            "stress_median_net_return",
            -0.01,
            "nonnegative_stress_median_return_both_assets",
        ),
        ("baseline_positive_window_rate", 0.50, "baseline_inner_persistence"),
        ("stress_positive_window_rate", 0.50, "stress_inner_persistence"),
        ("completed_trades", 11, "minimum_inner_trades"),
        ("maximum_drawdown_percent", 20.01, "drawdown_within_limit"),
        (
            "annualized_turnover_multiple",
            12.01,
            "annual_turnover_within_budget",
        ),
        (
            "annualized_baseline_cost_fraction",
            0.101,
            "annual_baseline_cost_within_budget",
        ),
        ("protective_policy_active", False, "protective_policy_active"),
    ],
)
def test_selection_policy_holds_cash_when_any_hard_gate_fails_everywhere(
    metric, value, failed_gate
):
    evidence = complete_inner_evidence()
    for parameter_id in PARAMETER_SET_ORDER:
        evidence[parameter_id]["BTC-USD"][metric] = value
    result = AlphaCalibrationSelectionPolicy().select(evidence)
    assert result["status"] == "NO_ELIGIBLE_CONFIGURATION_HOLD_CASH"
    assert result["selected_parameter_set_id"] is None
    assert result["hold_cash"] is True
    assert all(
        failed_gate in record["failed_gates"]
        for record in result["records"].values()
    )


def test_selection_policy_rejects_partial_catalog_asset_scope_and_bad_metrics():
    policy = AlphaCalibrationSelectionPolicy()
    evidence = complete_inner_evidence()
    evidence.pop(PARAMETER_SET_ORDER[-1])
    with pytest.raises(ValueError, match="complete frozen catalog order"):
        policy.select(evidence)

    evidence = complete_inner_evidence()
    evidence[PARAMETER_SET_ORDER[0]].pop("ETH-USD")
    with pytest.raises(ValueError, match="exact asset evidence"):
        policy.select(evidence)

    evidence = complete_inner_evidence()
    evidence[PARAMETER_SET_ORDER[0]]["BTC-USD"].pop("completed_trades")
    with pytest.raises(ValueError, match="fields are not exact"):
        policy.select(evidence)

    evidence = complete_inner_evidence()
    evidence[PARAMETER_SET_ORDER[0]]["BTC-USD"][
        "baseline_median_net_return"
    ] = float("nan")
    with pytest.raises(ValueError, match="must be finite"):
        policy.select(evidence)


def test_configuration_freezes_diagnostic_nested_and_future_validation_boundaries():
    configuration = alpha_discovery_configuration()
    assert configuration["parameter_catalog_version"] == PARAMETER_CATALOG_VERSION
    assert configuration["parameter_set_order"] == list(PARAMETER_SET_ORDER)
    assert len(configuration["parameter_sets"]) == 8
    assert configuration["diagnostic_phase"]["zero_cost_replay"] is True
    assert (
        configuration["diagnostic_phase"]["zero_cost_may_select_parameters"]
        is False
    )
    assert (
        configuration["calibration_phase"]["outer_test_available_to_selection"]
        is False
    )
    assert configuration["calibration_phase"]["no_eligible_configuration_action"] == (
        "HOLD_CASH"
    )
    assert configuration["common_execution"]["risk_per_trade_fraction"] == (
        pytest.approx(0.005)
    )
    assert configuration["future_validation"][
        "inspected_development_data_may_form_candidate_evidence"
    ] is False
    assert configuration["implementation_prerequisites"]["status"] == (
        "NOT_YET_IMPLEMENTED"
    )


def test_alpha_report_loader_rechecks_hash_sidecar_canonical_scope_and_failure_basis(
    tmp_path,
):
    report, digest = write_alpha_report(tmp_path / "alpha")
    payload, observed = load_recorded_alpha_development_report(
        report, expected_sha256=digest
    )
    assert observed == digest
    assert payload["status"] == "ALPHA_DEVELOPMENT_COMPLETED"

    report.write_bytes(report.read_bytes() + b" ")
    with pytest.raises(ValueError, match="SHA-256 changed"):
        load_recorded_alpha_development_report(report, expected_sha256=digest)


def test_alpha_report_loader_rejects_sidecar_noncanonical_and_identity_drift(tmp_path):
    report, digest = write_alpha_report(tmp_path / "sidecar")
    report.with_name("alpha_development_report.sha256").write_text(
        f"{digest} wrong.json\n", encoding="ascii"
    )
    with pytest.raises(ValueError, match="checksum is invalid"):
        load_recorded_alpha_development_report(report, expected_sha256=digest)

    report, digest = write_alpha_report(tmp_path / "noncanonical")
    payload = json.loads(report.read_bytes())
    noncanonical = json.dumps(payload).encode("utf-8")
    report.write_bytes(noncanonical)
    digest = hashlib.sha256(noncanonical).hexdigest()
    report.with_name("alpha_development_report.sha256").write_bytes(
        f"{digest}  {report.name}\n".encode("ascii")
    )
    with pytest.raises(ValueError, match="not canonical JSON"):
        load_recorded_alpha_development_report(report, expected_sha256=digest)

    report, digest = write_alpha_report(
        tmp_path / "identity",
        lambda payload: payload.__setitem__("candidate_v2_authorized", True),
    )
    with pytest.raises(ValueError, match="candidate_v2_authorized"):
        load_recorded_alpha_development_report(report, expected_sha256=digest)


def test_alpha_report_loader_rejects_changed_outcome_or_gate_basis(tmp_path):
    def mutate_outcome(payload):
        payload["comparison"]["outcome_counts"]["SCREEN_OUT"] = 2

    report, digest = write_alpha_report(tmp_path / "outcome", mutate_outcome)
    with pytest.raises(ValueError, match="outcome counts"):
        load_recorded_alpha_development_report(report, expected_sha256=digest)

    def mutate_gate(payload):
        variant = payload["variant_evidence"][VARIANT_ORDER[0]][
            "development_review"
        ]
        variant["failed_gates"].append("annual_turnover_within_budget")

    report, digest = write_alpha_report(tmp_path / "gate", mutate_gate)
    with pytest.raises(ValueError, match="failed-gate basis"):
        load_recorded_alpha_development_report(report, expected_sha256=digest)


def test_declaration_is_non_executing_and_non_promotional():
    declaration = AlphaDiscoveryPreregistration().declaration()
    assert declaration["schema_version"] == ALPHA_DISCOVERY_SCHEMA_VERSION
    assert declaration["status"] == "ALPHA_DISCOVERY_EVIDENCE_LOCK_PENDING"
    assert declaration["alpha_discovery_id"] == ALPHA_DISCOVERY_ID
    assert declaration["dataset_role"] == "INSPECTED_DEVELOPMENT_ONLY"
    assert declaration["configuration"]["parameter_set_order"] == list(
        PARAMETER_SET_ORDER
    )
    assert declaration["implementation_prerequisites_satisfied"] is False
    assert declaration["separate_runner_review_required"] is True
    assert declaration["runner_execution_authorized"] is False
    assert declaration["zero_cost_diagnostic_executed"] is False
    assert declaration["nested_calibration_executed"] is False
    assert declaration["parameter_selection_executed"] is False
    assert declaration["candidate_v2_authorized"] is False
    assert declaration["bounded_forward_paper_authorized"] is False
    assert declaration["live_execution_authorized"] is False


def test_evidence_lock_binds_exact_manifest_report_assets_and_configuration():
    preregistration = AlphaDiscoveryPreregistration(
        dataset_lock=FakeDatasetLock(),
        alpha_report_loader=fake_alpha_loader(),
    )
    locked = preregistration.lock("manifest.json", "alpha.json")
    assert locked.manifest_sha256 == DEVELOPMENT_MANIFEST_SHA256
    assert locked.alpha_development_report_sha256 == (
        RECORDED_ALPHA_DEVELOPMENT_REPORT_SHA256
    )
    assert tuple(sorted(locked.assets)) == ASSET_SCOPE
    assert locked.configuration == alpha_discovery_configuration()


def test_evidence_lock_rejects_manifest_report_or_scope_drift():
    with pytest.raises(ValueError, match="frozen discovery manifest"):
        AlphaDiscoveryPreregistration(
            dataset_lock=FakeDatasetLock("0" * 64),
            alpha_report_loader=fake_alpha_loader(),
        ).lock("manifest.json", "alpha.json")

    payload = alpha_development_payload()
    payload["manifest_sha256"] = "0" * 64
    with pytest.raises(ValueError, match="dataset manifest do not match"):
        AlphaDiscoveryPreregistration(
            dataset_lock=FakeDatasetLock(),
            alpha_report_loader=fake_alpha_loader(payload),
        ).lock("manifest.json", "alpha.json")

    class WrongScopeLock(FakeDatasetLock):
        def lock(self, manifest_path):
            locked = super().lock(manifest_path)
            locked.assets = {"BTC-USD": pd.DataFrame({"Close": [1.0]})}
            return locked

    with pytest.raises(ValueError, match="asset scope"):
        AlphaDiscoveryPreregistration(
            dataset_lock=WrongScopeLock(),
            alpha_report_loader=fake_alpha_loader(),
        ).lock("manifest.json", "alpha.json")


def test_cli_declaration_prints_pending_state_without_execution(capsys):
    assert main([]) == 0
    output = json.loads(capsys.readouterr().out)
    assert output["status"] == "ALPHA_DISCOVERY_EVIDENCE_LOCK_PENDING"
    assert output["zero_cost_diagnostic_executed"] is False
    assert output["nested_calibration_executed"] is False
    assert output["runner_execution_authorized"] is False


def test_cli_lock_prints_exact_evidence_without_execution(capsys, monkeypatch):
    preregistration = AlphaDiscoveryPreregistration(
        dataset_lock=FakeDatasetLock(),
        alpha_report_loader=fake_alpha_loader(),
    )
    monkeypatch.setattr(
        discovery_module,
        "AlphaDiscoveryPreregistration",
        lambda: preregistration,
    )
    assert main(["--manifest", "manifest.json", "--alpha-report", "alpha.json"]) == 0
    output = json.loads(capsys.readouterr().out)
    assert output["status"] == "ALPHA_DISCOVERY_EVIDENCE_LOCKED"
    assert output["asset_rows"] == {"BTC-USD": 2, "ETH-USD": 2}
    assert output["parameter_set_order"] == list(PARAMETER_SET_ORDER)
    assert output["alpha_development_report_sha256"] == (
        RECORDED_ALPHA_DEVELOPMENT_REPORT_SHA256
    )
    assert output["implementation_prerequisites_satisfied"] is False
    assert output["nested_calibration_executed"] is False
    assert output["candidate_v2_authorized"] is False
    assert output["live_execution_authorized"] is False


def test_cli_requires_manifest_and_report_together():
    with pytest.raises(SystemExit):
        main(["--manifest", "manifest.json"])
