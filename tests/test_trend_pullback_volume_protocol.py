import hashlib
import json
import os
from pathlib import Path
from types import SimpleNamespace
import sys

import pandas as pd
import pytest

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src")))

import trend_pullback_volume_protocol as protocol_module
from alpha_discovery_protocol import (
    ALPHA_DISCOVERY_ID,
    PARAMETER_SET_ORDER as CLOSED_DISCOVERY_PARAMETER_ORDER,
    parameter_catalog_fingerprint as closed_discovery_catalog_fingerprint,
)
from research_evidence import canonical_json_bytes
from strategy_family_screening import DEVELOPMENT_MANIFEST_SHA256
from trend_pullback_volume_protocol import (
    EXPECTED_DISCOVERY_FAILED_GATES,
    RECORDED_ALPHA_DISCOVERY_REPORT_SHA256,
    TREND_PULLBACK_DEVELOPMENT_ID,
    TREND_PULLBACK_PARAMETER_CATALOG,
    TREND_PULLBACK_PARAMETER_CATALOG_SHA256,
    TREND_PULLBACK_PARAMETER_ORDER,
    TREND_PULLBACK_PROTOCOL_SCHEMA_VERSION,
    TrendPullbackVolumeParameterSet,
    TrendPullbackVolumePreregistration,
    load_recorded_alpha_discovery_report,
    main,
    trend_pullback_catalog_fingerprint,
    trend_pullback_configuration,
)


def gates(positive_baseline=False):
    return {
        "annual_baseline_cost_within_budget": True,
        "annual_turnover_within_budget": True,
        "baseline_inner_persistence": False,
        "drawdown_within_limit": True,
        "minimum_inner_trades": True,
        "nonnegative_stress_median_return_both_assets": False,
        "positive_baseline_median_return_both_assets": positive_baseline,
        "protective_policy_active": True,
        "stress_inner_persistence": False,
    }


def discovery_payload():
    pass_counter = 0
    windows = []
    for outer in range(7):
        records = {}
        for parameter_id in CLOSED_DISCOVERY_PARAMETER_ORDER:
            positive = pass_counter < 5
            pass_counter += 1
            record_gates = gates(positive)
            records[parameter_id] = {
                "eligible": False,
                "gates": record_gates,
                "failed_gates": [
                    name for name, passed in record_gates.items() if not passed
                ],
                "selection_metrics": {
                    "worst_asset_stress_median_net_return": -0.01,
                    "worst_asset_baseline_median_net_return": (
                        0.001 if positive else -0.005
                    ),
                    "mean_annualized_turnover_multiple": 3.0,
                },
            }
        windows.append(
            {
                "outer_window": outer,
                "selection": {
                    "status": "NO_ELIGIBLE_CONFIGURATION_HOLD_CASH",
                    "selected_parameter_set_id": None,
                    "hold_cash": True,
                    "selection_scope": "INNER_VALIDATION_ONLY",
                    "outer_test_evidence_used": False,
                    "global_hindsight_leaderboard_generated": False,
                    "records": records,
                },
                "outer_evaluation": {
                    "action": "HOLD_CASH",
                    "parameter_set_id": None,
                    "profiles": {},
                },
            }
        )
    return {
        "schema_version": 1,
        "status": "ALPHA_DISCOVERY_COMPLETED",
        "alpha_discovery_id": ALPHA_DISCOVERY_ID,
        "manifest_sha256": DEVELOPMENT_MANIFEST_SHA256,
        "parameter_catalog_sha256": closed_discovery_catalog_fingerprint(),
        "parameter_set_order": list(CLOSED_DISCOVERY_PARAMETER_ORDER),
        "dataset_role": "INSPECTED_DEVELOPMENT_ONLY",
        "development_data_only": True,
        "zero_cost_diagnostic_executed": True,
        "trade_path_analysis_executed": True,
        "nested_calibration_executed": True,
        "outer_development_test_executed": True,
        "parameter_selection_executed": True,
        "global_hindsight_leaderboard_generated": False,
        "formal_candidate_evaluation": False,
        "candidate_v2_authorized": False,
        "optimization_authorized": False,
        "bounded_forward_paper_review_eligible": False,
        "bounded_forward_paper_authorized": False,
        "live_execution_authorized": False,
        "adaptive_review": {
            "outcome": "SCREEN_OUT",
            "selected_outer_windows": 0,
            "hold_cash_outer_windows": 7,
            "failed_gates": sorted(EXPECTED_DISCOVERY_FAILED_GATES),
        },
        "diagnostic": {
            "status": "ZERO_COST_TRADE_PATH_DIAGNOSTIC_COMPLETED",
            "zero_cost_may_select_parameters": False,
            "raw_trade_paths_persisted": False,
        },
        "nested_calibration": {"outer_windows": windows},
    }


def write_discovery_report(directory, mutator=None):
    directory.mkdir(parents=True)
    payload = discovery_payload()
    if mutator:
        mutator(payload)
    report = directory / "alpha_discovery_report.json"
    report_bytes = canonical_json_bytes(payload)
    report.write_bytes(report_bytes)
    digest = hashlib.sha256(report_bytes).hexdigest()
    report.with_name("alpha_discovery_report.sha256").write_bytes(
        f"{digest}  {report.name}\n".encode("ascii")
    )
    return report, digest


class FakeDatasetLock:
    def __init__(self, manifest_sha256=DEVELOPMENT_MANIFEST_SHA256, assets=None):
        self.manifest_sha256 = manifest_sha256
        self.assets = assets or {
            "BTC-USD": pd.DataFrame({"Close": [1.0, 2.0]}),
            "ETH-USD": pd.DataFrame({"Close": [1.0, 2.0]}),
        }

    def lock(self, manifest_path):
        return SimpleNamespace(
            manifest_sha256=self.manifest_sha256,
            assets=self.assets,
        )


def fake_discovery_loader(payload=None):
    payload = payload or discovery_payload()

    def loader(path, expected_sha256=None):
        assert expected_sha256 == RECORDED_ALPHA_DISCOVERY_REPORT_SHA256
        return payload, RECORDED_ALPHA_DISCOVERY_REPORT_SHA256

    return loader


def test_catalog_is_exact_small_and_deterministic():
    assert TREND_PULLBACK_PARAMETER_ORDER == (
        "pb0p5-rv1p2-2atr-static3r",
        "pb0p5-rv1p5-2atr-static3r",
        "pb1p0-rv1p2-2atr-static3r",
        "pb1p0-rv1p5-2atr-static3r",
    )
    assert tuple(
        item.parameter_set_id for item in TREND_PULLBACK_PARAMETER_CATALOG
    ) == TREND_PULLBACK_PARAMETER_ORDER
    assert len(TREND_PULLBACK_PARAMETER_CATALOG) == 4
    assert TREND_PULLBACK_PARAMETER_CATALOG_SHA256 == (
        "952046ddb7a9f9a85a8976f3ccafe43a017a745c887e592a44c39c2146ba8e00"
    )
    assert trend_pullback_catalog_fingerprint() == (
        TREND_PULLBACK_PARAMETER_CATALOG_SHA256
    )
    assert trend_pullback_catalog_fingerprint(
        TREND_PULLBACK_PARAMETER_CATALOG
    ) == TREND_PULLBACK_PARAMETER_CATALOG_SHA256


def test_catalog_varies_only_pullback_distance_and_trigger_volume():
    dictionaries = [item.as_dict() for item in TREND_PULLBACK_PARAMETER_CATALOG]
    varying = {
        name
        for name in dictionaries[0]
        if len({json.dumps(item[name], sort_keys=True) for item in dictionaries}) > 1
    }
    assert varying == {
        "parameter_set_id",
        "pullback_distance_atr",
        "trigger_relative_volume",
    }
    assert {item["initial_stop_atr"] for item in dictionaries} == {2.0}
    assert {item["reward_risk_ratio"] for item in dictionaries} == {3.0}
    assert {item["volume_baseline_lag"] for item in dictionaries} == {1}


@pytest.mark.parametrize(
    "kwargs, message",
    [
        ({"pullback_distance_atr": 0.75}, "0.5 or 1.0"),
        ({"trigger_relative_volume": 2.0}, "1.2 or 1.5"),
        ({"volume_baseline_lag": 0}, "positive integer"),
        ({"initial_stop_atr": 1.5}, "2 ATR"),
        ({"reward_risk_ratio": 2.0}, "3R"),
    ],
)
def test_parameter_set_rejects_catalog_drift(kwargs, message):
    values = {
        "parameter_set_id": "pb0p5-rv1p2-2atr-static3r",
        "pullback_distance_atr": 0.5,
        "trigger_relative_volume": 1.2,
    }
    values.update(kwargs)
    with pytest.raises(ValueError, match=message):
        TrendPullbackVolumeParameterSet(**values)


def test_parameter_set_id_must_match_values():
    with pytest.raises(ValueError, match="does not match"):
        TrendPullbackVolumeParameterSet(
            parameter_set_id="pb1p0-rv1p2-2atr-static3r",
            pullback_distance_atr=0.5,
            trigger_relative_volume=1.2,
        )


def test_configuration_freezes_causal_volume_and_nonexecuting_boundary():
    configuration = trend_pullback_configuration()
    assert configuration["parameter_set_order"] == list(
        TREND_PULLBACK_PARAMETER_ORDER
    )
    assert configuration["causal_setup_state"] == {
        "observation": "COMPLETED_BARS_ONLY",
        "setup_expiry_bars": 8,
        "pullback_volume_role": "CONTRACTION_OR_NORMAL",
        "trigger_volume_role": "REEXPANSION",
        "entry_execution": "FOLLOWING_BAR_OPEN",
        "future_bar_access": False,
    }
    assert configuration["risk_and_exit"]["initial_stop_atr"] == 2.0
    assert configuration["risk_and_exit"]["breakeven_enabled"] is False
    assert configuration["future_runner_boundary"][
        "outer_test_available_to_selection"
    ] is False
    assert configuration["future_runner_boundary"][
        "no_eligible_configuration_action"
    ] == "HOLD_CASH"
    assert configuration["implementation_prerequisites"]["status"] == (
        "PROTOCOL_ONLY_NOT_EXECUTABLE"
    )


def test_discovery_loader_rechecks_hash_sidecar_canonical_and_exact_basis(tmp_path):
    report, digest = write_discovery_report(tmp_path / "valid")
    payload, observed = load_recorded_alpha_discovery_report(
        report, expected_sha256=digest
    )
    assert observed == digest
    assert payload["adaptive_review"]["hold_cash_outer_windows"] == 7

    report.write_bytes(report.read_bytes() + b" ")
    with pytest.raises(ValueError, match="SHA-256 changed"):
        load_recorded_alpha_discovery_report(report, expected_sha256=digest)


def test_discovery_loader_rejects_bad_sidecar_or_noncanonical_json(tmp_path):
    report, digest = write_discovery_report(tmp_path / "sidecar")
    report.with_name("alpha_discovery_report.sha256").write_bytes(
        f"{digest}  wrong.json\n".encode("ascii")
    )
    with pytest.raises(ValueError, match="checksum is invalid"):
        load_recorded_alpha_discovery_report(report, expected_sha256=digest)

    report, _ = write_discovery_report(tmp_path / "noncanonical")
    payload = json.loads(report.read_bytes())
    noncanonical = json.dumps(payload).encode("utf-8")
    report.write_bytes(noncanonical)
    digest = hashlib.sha256(noncanonical).hexdigest()
    report.with_name("alpha_discovery_report.sha256").write_bytes(
        f"{digest}  {report.name}\n".encode("ascii")
    )
    with pytest.raises(ValueError, match="not canonical JSON"):
        load_recorded_alpha_discovery_report(report, expected_sha256=digest)


@pytest.mark.parametrize(
    "mutator, message",
    [
        (
            lambda payload: payload.__setitem__("candidate_v2_authorized", True),
            "candidate_v2_authorized",
        ),
        (
            lambda payload: payload["adaptive_review"].__setitem__(
                "hold_cash_outer_windows", 6
            ),
            "review basis",
        ),
        (
            lambda payload: payload["nested_calibration"]["outer_windows"][0][
                "selection"
            ].__setitem__("selected_parameter_set_id", "changed"),
            "selection basis",
        ),
        (
            lambda payload: payload["nested_calibration"]["outer_windows"][0][
                "selection"
            ]["records"][CLOSED_DISCOVERY_PARAMETER_ORDER[5]]["gates"].__setitem__(
                "positive_baseline_median_return_both_assets", True
            ),
            "inner-gate counts",
        ),
    ],
)
def test_discovery_loader_rejects_authorization_or_outcome_drift(
    tmp_path, mutator, message
):
    report, digest = write_discovery_report(tmp_path / message.replace(" ", "_"), mutator)
    with pytest.raises(ValueError, match=message):
        load_recorded_alpha_discovery_report(report, expected_sha256=digest)


def test_declaration_is_nonexecuting_nonpromotional_and_volume_explicit():
    declaration = TrendPullbackVolumePreregistration().declaration()
    assert declaration["schema_version"] == TREND_PULLBACK_PROTOCOL_SCHEMA_VERSION
    assert declaration["status"] == "TREND_PULLBACK_VOLUME_EVIDENCE_LOCK_PENDING"
    assert declaration["development_id"] == TREND_PULLBACK_DEVELOPMENT_ID
    assert declaration["dataset_role"] == "INSPECTED_DEVELOPMENT_ONLY"
    assert declaration["configuration"]["causal_setup_state"][
        "trigger_volume_role"
    ] == "REEXPANSION"
    assert declaration["implementation_prerequisites_satisfied"] is False
    assert declaration["runner_execution_authorized"] is False
    assert declaration["performance_evaluation_executed"] is False
    assert declaration["parameter_calibration_executed"] is False
    assert declaration["candidate_v2_authorized"] is False
    assert declaration["bounded_forward_paper_authorized"] is False
    assert declaration["live_execution_authorized"] is False


def test_evidence_lock_binds_exact_manifest_report_scope_and_configuration():
    preregistration = TrendPullbackVolumePreregistration(
        dataset_lock=FakeDatasetLock(),
        discovery_report_loader=fake_discovery_loader(),
    )
    locked = preregistration.lock("manifest.json", "discovery.json")
    assert locked.manifest_sha256 == DEVELOPMENT_MANIFEST_SHA256
    assert locked.alpha_discovery_report_sha256 == (
        RECORDED_ALPHA_DISCOVERY_REPORT_SHA256
    )
    assert tuple(sorted(locked.assets)) == ("BTC-USD", "ETH-USD")
    assert locked.configuration == trend_pullback_configuration()


def test_evidence_lock_rejects_manifest_report_or_scope_drift():
    with pytest.raises(ValueError, match="frozen manifest"):
        TrendPullbackVolumePreregistration(
            dataset_lock=FakeDatasetLock("0" * 64),
            discovery_report_loader=fake_discovery_loader(),
        ).lock("manifest.json", "discovery.json")

    payload = discovery_payload()
    payload["manifest_sha256"] = "0" * 64
    with pytest.raises(ValueError, match="dataset manifest do not match"):
        TrendPullbackVolumePreregistration(
            dataset_lock=FakeDatasetLock(),
            discovery_report_loader=fake_discovery_loader(payload),
        ).lock("manifest.json", "discovery.json")

    with pytest.raises(ValueError, match="asset scope"):
        TrendPullbackVolumePreregistration(
            dataset_lock=FakeDatasetLock(
                assets={"BTC-USD": pd.DataFrame({"Close": [1.0]})}
            ),
            discovery_report_loader=fake_discovery_loader(),
        ).lock("manifest.json", "discovery.json")


def test_cli_declaration_and_lock_remain_nonexecuting(capsys, monkeypatch):
    assert main([]) == 0
    declaration = json.loads(capsys.readouterr().out)
    assert declaration["status"] == "TREND_PULLBACK_VOLUME_EVIDENCE_LOCK_PENDING"
    assert declaration["performance_evaluation_executed"] is False

    preregistration = TrendPullbackVolumePreregistration(
        dataset_lock=FakeDatasetLock(),
        discovery_report_loader=fake_discovery_loader(),
    )
    monkeypatch.setattr(
        protocol_module,
        "TrendPullbackVolumePreregistration",
        lambda: preregistration,
    )
    assert main(
        ["--manifest", "manifest.json", "--discovery-report", "discovery.json"]
    ) == 0
    locked = json.loads(capsys.readouterr().out)
    assert locked["status"] == "TREND_PULLBACK_VOLUME_EVIDENCE_LOCKED"
    assert locked["asset_rows"] == {"BTC-USD": 2, "ETH-USD": 2}
    assert locked["parameter_set_order"] == list(TREND_PULLBACK_PARAMETER_ORDER)
    assert locked["runner_execution_authorized"] is False
    assert locked["candidate_v2_authorized"] is False
    assert locked["live_execution_authorized"] is False


def test_cli_requires_manifest_and_discovery_report_together():
    with pytest.raises(SystemExit):
        main(["--manifest", "manifest.json"])
