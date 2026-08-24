import hashlib
import json
import os
from pathlib import Path
from types import SimpleNamespace
import sys

import pandas as pd
import pytest

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src")))

import strategy_failure_attribution as attribution_module
from first_strategy_candidate import BASELINE_COSTS, STRESSED_COSTS
from research_evidence import canonical_json_bytes
from strategy_failure_attribution import (
    ATTRIBUTION_ID,
    ATTRIBUTION_SCHEMA_VERSION,
    DIAGNOSTIC_PROFILES,
    RECORDED_SCREENING_REPORT_SHA256,
    FailureAttributionPreregistration,
    failure_attribution_configuration,
    load_recorded_screening_report,
    main,
)
from strategy_family_screening import (
    DEVELOPMENT_MANIFEST_SHA256,
    SCREENING_ID,
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


def screening_payload():
    strategies = {
        name: {
            "outcome": "SCREEN_OUT",
            "baseline_aggregate_classification": "REJECTED",
            "cost_stress_aggregate_classification": "REJECTED",
        }
        for name in EXPECTED_STRATEGIES
    }
    return {
        "schema_version": 1,
        "status": "STRATEGY_FAMILY_SCREENING_COMPLETED",
        "screening_id": SCREENING_ID,
        "manifest_sha256": DEVELOPMENT_MANIFEST_SHA256,
        "dataset_role": "INSPECTED_DEVELOPMENT_ONLY",
        "development_data_only": True,
        "strategy_order": list(EXPECTED_STRATEGIES),
        "strategy_count": 8,
        "strategy_evidence": {
            name: {"screening_review": {"outcome": "SCREEN_OUT"}}
            for name in EXPECTED_STRATEGIES
        },
        "comparison": {
            "strategy_order": list(EXPECTED_STRATEGIES),
            "selection_policy": "DESCRIPTIVE_MULTIPLE_COMPARISON_GUARD",
            "automatic_ranking_generated": False,
            "automatic_strategy_selection": False,
            "outcome_counts": {
                "INCONCLUSIVE": 0,
                "MECHANISM_RETAINS_INTEREST": 0,
                "SCREEN_OUT": 8,
            },
            "mechanisms_retaining_interest": [],
            "strategies": strategies,
        },
        "screening_executed": True,
        "performance_evaluation_executed": True,
        "development_screening_executed": True,
        "automatic_ranking_generated": False,
        "automatic_strategy_selection": False,
        "parameter_sweep_executed": False,
        "strategy_combination_executed": False,
        "formal_candidate_evaluation": False,
        "selected_strategy": None,
        "candidate_v2_authorized": False,
        "optimization_authorized": False,
        "bounded_forward_paper_review_eligible": False,
        "bounded_forward_paper_authorized": False,
        "live_execution_authorized": False,
    }


def write_screening_report(directory, transform=None):
    directory.mkdir(parents=True)
    payload = screening_payload()
    if transform:
        transform(payload)
    report_path = directory / "strategy_family_screening_report.json"
    report_bytes = canonical_json_bytes(payload)
    digest = hashlib.sha256(report_bytes).hexdigest()
    report_path.write_bytes(report_bytes)
    report_path.with_name("strategy_family_screening_report.sha256").write_bytes(
        f"{digest}  {report_path.name}\n".encode("ascii")
    )
    return report_path, digest


class FakeScreeningPreregistration:
    def __init__(self):
        index = pd.date_range("2024-01-01", periods=4, freq="6h", tz="UTC")
        frame = pd.DataFrame(
            {
                "Open": [100.0, 101.0, 102.0, 103.0],
                "High": [101.0, 102.0, 103.0, 104.0],
                "Low": [99.0, 100.0, 101.0, 102.0],
                "Close": [100.5, 101.5, 102.5, 103.5],
                "Volume": [10.0, 20.0, 15.0, 30.0],
            },
            index=index,
        )
        self.calls = []
        self.locked = SimpleNamespace(
            manifest_sha256=DEVELOPMENT_MANIFEST_SHA256,
            contract=SimpleNamespace(
                dataset_id="coinbase-exchange-btc-eth-native-6h-20190101-20260801-v1",
                timeframe="6h",
                products=("BTC-USD", "ETH-USD"),
            ),
            configuration=SimpleNamespace(),
            strategy_engines={name: SimpleNamespace(strategy_name=name) for name in EXPECTED_STRATEGIES},
            assets={"BTC-USD": frame, "ETH-USD": frame.copy()},
        )

    def lock(self, manifest_path):
        self.calls.append(str(manifest_path))
        return self.locked


def test_declaration_freezes_failure_attribution_and_volume_boundary():
    declaration = FailureAttributionPreregistration().declaration()

    assert declaration["schema_version"] == ATTRIBUTION_SCHEMA_VERSION
    assert declaration["status"] == "FAILURE_ATTRIBUTION_EVIDENCE_LOCK_PENDING"
    assert declaration["attribution_id"] == ATTRIBUTION_ID
    assert declaration["strategy_order"] == list(EXPECTED_STRATEGIES)
    assert declaration["required_manifest_sha256"] == DEVELOPMENT_MANIFEST_SHA256
    assert declaration["required_screening_report_sha256"] == (
        RECORDED_SCREENING_REPORT_SHA256
    )
    assert declaration["dataset_role"] == "INSPECTED_DEVELOPMENT_ONLY"
    assert declaration["failure_attribution_executed"] is False
    assert declaration["performance_replay_executed"] is False
    assert declaration["volume_analysis_mandatory"] is True
    assert declaration["parameter_sweep_authorized"] is False
    assert declaration["strategy_combination_authorized"] is False
    assert declaration["candidate_v2_authorized"] is False
    assert declaration["bounded_forward_paper_authorized"] is False
    assert declaration["live_execution_authorized"] is False


def test_configuration_freezes_zero_baseline_stress_and_causal_axes():
    configuration = failure_attribution_configuration()

    assert tuple(item["label"] for item in configuration["diagnostic_profiles"]) == (
        DIAGNOSTIC_PROFILES
    )
    assert configuration["diagnostic_profiles"][0]["total_rate"] == 0.0
    assert configuration["diagnostic_profiles"][1] == BASELINE_COSTS.as_dict()
    assert configuration["diagnostic_profiles"][2] == STRESSED_COSTS.as_dict()
    assert configuration["execution_timing"] == "next_bar_open"
    assert configuration["attribution_timestamp"] == "entry_signal_index"
    assert configuration["market_regime"]["signal_observation"] == (
        "COMPLETED_BAR_ONLY"
    )
    assert configuration["volume"]["baseline_lag"] == 1
    assert configuration["volume"]["cross_asset_normalization"] == (
        "PER_ASSET_RELATIVE_NOT_RAW_VOLUME"
    )
    assert configuration["volume"]["signal_observation"] == "COMPLETED_BAR_ONLY"
    assert "VOLUME_REGIME_AT_SIGNAL_BAR" in configuration["diagnostic_axes"]
    assert "GROSS_SIGNAL_BEFORE_COSTS" in configuration["diagnostic_axes"]


def test_volume_is_a_required_filter_feature_not_a_standalone_edge_claim():
    volume = FailureAttributionPreregistration().declaration()["volume_policy"]

    assert volume["mandatory_for_future_alpha_hypothesis"] is True
    assert volume["raw_cross_asset_volume_comparison"] == "PROHIBITED"
    assert volume["future_data_access"] == "PROHIBITED"
    assert volume["standalone_edge_claim"] is False
    assert volume["live_liquidity_substitute"] is False


def test_declaration_prohibits_ranking_selection_and_result_driven_tuning():
    policy = FailureAttributionPreregistration().declaration()[
        "interpretation_policy"
    ]

    assert policy["purpose"] == "EXPLAIN_RECORDED_FAILURE_NOT_SELECT_WINNER"
    assert policy["ranking"] == "PROHIBITED"
    assert policy["winner_selection"] == "PROHIBITED"
    assert policy["result_driven_parameter_changes"] == "PROHIBITED"
    assert policy["future_hypothesis_may_use_inspected_evidence"] is True
    assert policy["formal_validation_claim"] == "PROHIBITED"


def test_recorded_screening_hash_is_exactly_frozen():
    assert RECORDED_SCREENING_REPORT_SHA256 == (
        "9cf74deebe6a7efe9928d89b93b8ad4f7504ef70dfcf07ab0c00091a2cb9ec7f"
    )


def test_loader_accepts_only_canonical_sidecar_bound_screening(tmp_path):
    report_path, digest = write_screening_report(tmp_path / "screening_v1")

    payload, observed = load_recorded_screening_report(
        report_path,
        expected_sha256=digest,
    )

    assert observed == digest
    assert payload["status"] == "STRATEGY_FAMILY_SCREENING_COMPLETED"
    assert payload["comparison"]["outcome_counts"]["SCREEN_OUT"] == 8


@pytest.mark.parametrize("problem", ["hash", "sidecar", "canonical"])
def test_loader_rejects_hash_sidecar_or_canonical_drift(tmp_path, problem):
    report_path, digest = write_screening_report(tmp_path / "screening_v1")
    if problem == "hash":
        expected = "0" * 64
    else:
        expected = digest
    if problem == "sidecar":
        report_path.with_name("strategy_family_screening_report.sha256").write_text(
            "0" * 64 + "  strategy_family_screening_report.json\n",
            encoding="ascii",
        )
    elif problem == "canonical":
        payload = json.loads(report_path.read_bytes())
        noncanonical = json.dumps(payload, indent=2, sort_keys=True).encode("utf-8")
        report_path.write_bytes(noncanonical)
        expected = hashlib.sha256(noncanonical).hexdigest()
        report_path.with_name("strategy_family_screening_report.sha256").write_bytes(
            f"{expected}  {report_path.name}\n".encode("ascii")
        )

    with pytest.raises(ValueError):
        load_recorded_screening_report(report_path, expected_sha256=expected)


@pytest.mark.parametrize(
    "transform",
    [
        lambda payload: payload.__setitem__("selected_strategy", "adx"),
        lambda payload: payload.__setitem__("candidate_v2_authorized", True),
        lambda payload: payload["comparison"]["outcome_counts"].__setitem__(
            "SCREEN_OUT", 7
        ),
        lambda payload: payload["comparison"]["strategies"]["adx"].__setitem__(
            "outcome", "MECHANISM_RETAINS_INTEREST"
        ),
    ],
)
def test_loader_rejects_identity_authorization_or_closed_outcome_drift(
    tmp_path, transform
):
    report_path, digest = write_screening_report(
        tmp_path / "screening_v1", transform=transform
    )

    with pytest.raises(ValueError):
        load_recorded_screening_report(report_path, expected_sha256=digest)


def test_lock_binds_dataset_and_recorded_screening_without_replay(tmp_path):
    report_path, digest = write_screening_report(tmp_path / "screening_v1")
    screening = FakeScreeningPreregistration()
    preregistration = FailureAttributionPreregistration(
        screening_preregistration=screening,
        required_screening_report_sha256=digest,
    )

    locked = preregistration.lock("manifest.json", report_path)

    assert screening.calls == ["manifest.json"]
    assert locked.manifest_sha256 == DEVELOPMENT_MANIFEST_SHA256
    assert locked.screening_report_sha256 == digest
    assert tuple(locked.strategy_engines) == EXPECTED_STRATEGIES
    assert tuple(sorted(locked.assets)) == ("BTC-USD", "ETH-USD")
    assert locked.screening_report["selected_strategy"] is None


def test_lock_rejects_report_manifest_or_strategy_scope_mismatch(tmp_path):
    report_path, digest = write_screening_report(tmp_path / "screening_v1")
    payload = json.loads(report_path.read_bytes())
    payload["manifest_sha256"] = "0" * 64
    report_bytes = canonical_json_bytes(payload)
    digest = hashlib.sha256(report_bytes).hexdigest()
    report_path.write_bytes(report_bytes)
    report_path.with_name("strategy_family_screening_report.sha256").write_bytes(
        f"{digest}  {report_path.name}\n".encode("ascii")
    )
    preregistration = FailureAttributionPreregistration(
        screening_preregistration=FakeScreeningPreregistration(),
        required_screening_report_sha256=digest,
    )

    with pytest.raises(ValueError, match="manifest"):
        preregistration.lock("manifest.json", report_path)


def test_cli_declaration_does_not_execute_or_write(capsys):
    assert main([]) == 0
    output = json.loads(capsys.readouterr().out)

    assert output["status"] == "FAILURE_ATTRIBUTION_EVIDENCE_LOCK_PENDING"
    assert output["failure_attribution_executed"] is False
    assert output["performance_replay_executed"] is False


def test_cli_requires_manifest_and_report_together():
    with pytest.raises(SystemExit):
        main(["--manifest", "manifest.json"])
    with pytest.raises(SystemExit):
        main(["--screening-report", "report.json"])


def test_cli_lock_reports_safe_identity_without_execution(
    tmp_path, capsys, monkeypatch
):
    report_path, digest = write_screening_report(tmp_path / "screening_v1")
    preregistration = FailureAttributionPreregistration(
        screening_preregistration=FakeScreeningPreregistration(),
        required_screening_report_sha256=digest,
    )
    monkeypatch.setattr(
        attribution_module,
        "FailureAttributionPreregistration",
        lambda: preregistration,
    )

    assert main(
        [
            "--manifest",
            "manifest.json",
            "--screening-report",
            str(report_path),
        ]
    ) == 0
    output = json.loads(capsys.readouterr().out)

    assert output["status"] == "FAILURE_ATTRIBUTION_EVIDENCE_LOCKED"
    assert output["asset_rows"] == {"BTC-USD": 4, "ETH-USD": 4}
    assert output["strategy_order"] == list(EXPECTED_STRATEGIES)
    assert output["failure_attribution_executed"] is False
    assert output["performance_replay_executed"] is False
    assert output["candidate_v2_authorized"] is False
    assert output["live_execution_authorized"] is False
