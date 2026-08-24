import hashlib
import json
import os
from pathlib import Path
from types import SimpleNamespace
import sys

import pandas as pd
import pytest

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src")))

import alpha_development_protocol as protocol_module
from alpha_development_protocol import (
    ALPHA_DEVELOPMENT_ID,
    ALPHA_DEVELOPMENT_SCHEMA_VERSION,
    RECORDED_ATTRIBUTION_REPORT_SHA256,
    VARIANT_ORDER,
    AlphaDevelopmentPreregistration,
    alpha_development_configuration,
    alpha_development_evaluation_configuration,
    alpha_development_protective_exit_policy,
    alpha_development_risk_engine,
    alpha_development_strategy_engines,
    load_recorded_attribution_report,
    main,
    protective_exit_boundary,
)
from research_evidence import canonical_json_bytes
from strategy_failure_attribution import (
    ATTRIBUTION_ID,
    RECORDED_SCREENING_REPORT_SHA256,
    RECORDED_STRATEGY_ORDER,
)
from strategy_family_screening import DEVELOPMENT_MANIFEST_SHA256


def conditioned_summary(trades, pnl):
    return {"trade_count": trades, "net_profit_loss": pnl}


def attribution_payload():
    assets = {}
    for asset, volume_trades, market_trades in (
        ("BTC-USD", 25, 14),
        ("ETH-USD", 21, 19),
    ):
        assets[asset] = {
            "volume": {
                "volume_regimes": {
                    "HIGH": conditioned_summary(volume_trades, 100.0)
                },
                "obv_directions": {
                    "FALLING": conditioned_summary(10, -100.0),
                    "RISING": conditioned_summary(
                        10, -50.0 if asset == "BTC-USD" else 50.0
                    ),
                },
            },
            "market_regime": {
                "regimes": {
                    "BULLISH_NORMAL": conditioned_summary(market_trades, 100.0)
                }
            },
        }
    return {
        "schema_version": 1,
        "status": "FAILURE_ATTRIBUTION_COMPLETED",
        "attribution_id": ATTRIBUTION_ID,
        "manifest_sha256": DEVELOPMENT_MANIFEST_SHA256,
        "screening_report_sha256": RECORDED_SCREENING_REPORT_SHA256,
        "dataset_role": "INSPECTED_DEVELOPMENT_ONLY",
        "strategy_order": list(RECORDED_STRATEGY_ORDER),
        "strategy_count": 8,
        "profile_order": ["zero_cost", "baseline", "stress"],
        "diagnostic_multi_asset_replays": 24,
        "strategy_evidence": {
            "adx": {
                "profiles": {
                    "baseline": {"attribution": {"assets": assets}}
                }
            }
        },
        "failure_attribution_executed": True,
        "performance_replay_executed": True,
        "volume_analysis_executed": True,
        "market_regime_analysis_executed": True,
        "automatic_ranking_generated": False,
        "automatic_strategy_selection": False,
        "parameter_sweep_executed": False,
        "strategy_combination_executed": False,
        "formal_candidate_evaluation": False,
        "selected_strategy": None,
        "new_alpha_hypothesis_generated": False,
        "candidate_v2_authorized": False,
        "optimization_authorized": False,
        "bounded_forward_paper_review_eligible": False,
        "bounded_forward_paper_authorized": False,
        "live_execution_authorized": False,
    }


def write_report(directory, mutate=None):
    directory.mkdir()
    payload = attribution_payload()
    if mutate is not None:
        mutate(payload)
    report = directory / "failure_attribution_report.json"
    report_bytes = canonical_json_bytes(payload)
    digest = hashlib.sha256(report_bytes).hexdigest()
    report.write_bytes(report_bytes)
    report.with_name("failure_attribution_report.sha256").write_bytes(
        f"{digest}  {report.name}\n".encode("ascii")
    )
    return report, digest


class FakeDatasetLock:
    def __init__(self, manifest_sha256=DEVELOPMENT_MANIFEST_SHA256):
        self.manifest_sha256 = manifest_sha256

    def lock(self, manifest_path):
        frame = pd.DataFrame({"Close": [1.0]})
        return SimpleNamespace(
            manifest_sha256=self.manifest_sha256,
            assets={"BTC-USD": frame, "ETH-USD": frame.copy()},
        )


def fake_loader(payload=None, digest=RECORDED_ATTRIBUTION_REPORT_SHA256):
    payload = payload or attribution_payload()

    def load(path, expected_sha256):
        assert expected_sha256 == RECORDED_ATTRIBUTION_REPORT_SHA256
        return payload, digest

    return load


def test_configuration_freezes_three_ablation_variants_risk_turnover_and_no_calibration():
    configuration = alpha_development_configuration()
    assert configuration["variant_order"] == list(VARIANT_ORDER)
    assert len(configuration["variants"]) == 3
    assert configuration["comparison"]["parameter_sweep"] == "PROHIBITED"
    assert configuration["comparison"]["ranking"] == "PROHIBITED"
    assert configuration["risk"]["risk_per_trade_fraction"] == pytest.approx(0.005)
    assert configuration["risk"]["minimum_reward_risk_ratio"] == pytest.approx(3.0)
    assert configuration["turnover_cost_budget"][
        "annual_total_executed_notional_multiple_maximum"
    ] == pytest.approx(24.0)
    assert configuration["temporal_development"]["calibration_in_this_protocol"] is False
    assert configuration["evaluation"] == (
        alpha_development_evaluation_configuration().as_dict()
    )


def test_development_evaluation_configuration_freezes_deterministic_gates():
    configuration = alpha_development_evaluation_configuration()
    assert configuration.train_size == 2880
    assert configuration.test_size == 720
    assert configuration.step_size == 720
    assert configuration.initial_capital == pytest.approx(5000.0)
    assert configuration.simulations == 5000
    assert configuration.random_seed == 20260822
    assert configuration.min_walk_forward_windows == 5
    assert configuration.min_unseen_trades_per_asset == 20
    assert configuration.max_oos_drawdown_percent == pytest.approx(20.0)
    assert configuration.execution_timing == "next_bar_open"


def test_protective_exit_boundary_records_resolved_gap_and_runner_prerequisite():
    boundary = protective_exit_boundary()
    assert "DOES_NOT_EXECUTE_INTRABAR_PROTECTIVE_EXITS" in boundary[
        "resolved_backtester_limitation"
    ]
    assert boundary["stop_and_target_same_bar"] == "CONSERVATIVE_STOP_FIRST"
    assert boundary["implementation_verified"] is True
    assert boundary["performance_runner_prerequisite_satisfied"] is True


def test_protocol_constructs_exact_risk_engine_and_active_exit_policy():
    risk = alpha_development_risk_engine()
    policy = alpha_development_protective_exit_policy()
    assert risk.risk_per_trade == pytest.approx(0.005)
    assert risk.max_position_fraction == pytest.approx(0.50)
    assert risk.max_drawdown_fraction == pytest.approx(0.20)
    assert risk.daily_loss_limit == pytest.approx(0.02)
    assert risk.weekly_loss_limit == pytest.approx(0.05)
    assert risk.min_reward_risk == pytest.approx(3.0)
    assert policy.reward_risk_ratio == pytest.approx(risk.min_reward_risk)
    assert policy.stop_and_target_same_bar == "STOP_FIRST"


def test_declaration_is_non_evaluating_non_promotional_and_requires_separate_reviews():
    declaration = AlphaDevelopmentPreregistration().declaration()
    assert declaration["schema_version"] == ALPHA_DEVELOPMENT_SCHEMA_VERSION
    assert declaration["status"] == "ALPHA_DEVELOPMENT_EVIDENCE_LOCK_PENDING"
    assert declaration["alpha_development_id"] == ALPHA_DEVELOPMENT_ID
    assert declaration["dataset_role"] == "INSPECTED_DEVELOPMENT_ONLY"
    assert declaration["variant_order"] == list(VARIANT_ORDER)
    assert declaration["joint_performance_evaluation_executed"] is False
    assert declaration["protective_exit_engine_implemented"] is True
    assert declaration["automatic_strategy_selection"] is False
    assert declaration["candidate_v2_authorized"] is False
    assert declaration["bounded_forward_paper_authorized"] is False
    assert declaration["live_execution_authorized"] is False
    assert declaration["separate_protective_exit_review_required"] is False
    assert declaration["protective_exit_review_completed"] is True
    assert declaration["separate_performance_runner_review_required"] is False
    assert declaration["performance_runner_review_completed"] is True
    assert declaration["runner_execution_authorized_before_evidence_lock"] is False


def test_attribution_loader_rechecks_canonical_bytes_sidecar_scope_and_basis(tmp_path):
    report, digest = write_report(tmp_path / "evidence")
    payload, observed = load_recorded_attribution_report(
        report, expected_sha256=digest
    )
    assert observed == digest
    assert payload["status"] == "FAILURE_ATTRIBUTION_COMPLETED"


def test_attribution_loader_rejects_tamper_bad_sidecar_and_wrong_basis(tmp_path):
    report, digest = write_report(tmp_path / "tamper")
    report.write_bytes(report.read_bytes() + b" ")
    with pytest.raises(ValueError, match="SHA-256"):
        load_recorded_attribution_report(report, expected_sha256=digest)

    report, digest = write_report(tmp_path / "sidecar")
    report.with_name("failure_attribution_report.sha256").write_text("bad\n")
    with pytest.raises(ValueError, match="sidecar"):
        load_recorded_attribution_report(report, expected_sha256=digest)

    report, digest = write_report(
        tmp_path / "basis",
        lambda payload: payload["strategy_evidence"]["adx"]["profiles"][
            "baseline"
        ]["attribution"]["assets"]["BTC-USD"]["volume"]["volume_regimes"][
            "HIGH"
        ].update({"net_profit_loss": -1.0}),
    )
    with pytest.raises(ValueError, match="high-volume basis"):
        load_recorded_attribution_report(report, expected_sha256=digest)


def test_lock_binds_dataset_attribution_and_exact_strategy_engine_order():
    preregistration = AlphaDevelopmentPreregistration(
        dataset_lock=FakeDatasetLock(),
        attribution_report_loader=fake_loader(),
    )
    locked = preregistration.lock("manifest.json", "attribution.json")
    assert locked.manifest_sha256 == DEVELOPMENT_MANIFEST_SHA256
    assert locked.attribution_report_sha256 == RECORDED_ATTRIBUTION_REPORT_SHA256
    assert tuple(locked.strategy_engines) == VARIANT_ORDER
    assert tuple(sorted(locked.assets)) == ("BTC-USD", "ETH-USD")


def test_lock_rejects_manifest_hash_and_evidence_dataset_mismatch():
    with pytest.raises(ValueError, match="manifest"):
        AlphaDevelopmentPreregistration(
            dataset_lock=FakeDatasetLock("0" * 64),
            attribution_report_loader=fake_loader(),
        ).lock("manifest.json", "attribution.json")

    payload = attribution_payload()
    payload["manifest_sha256"] = "0" * 64
    with pytest.raises(ValueError, match="do not match"):
        AlphaDevelopmentPreregistration(
            dataset_lock=FakeDatasetLock(),
            attribution_report_loader=fake_loader(payload=payload),
        ).lock("manifest.json", "attribution.json")


def test_strategy_engines_use_unique_names_and_exact_non_ranked_order():
    engines = alpha_development_strategy_engines()
    assert tuple(engines) == VARIANT_ORDER
    assert len({engine.strategy_name for engine in engines.values()}) == 3
    assert all(engine.strategy_name.startswith("alpha_v2_adx_") for engine in engines.values())


def test_cli_declaration_and_locked_output_do_not_execute_performance(capsys, monkeypatch):
    assert main([]) == 0
    declaration = json.loads(capsys.readouterr().out)
    assert declaration["status"] == "ALPHA_DEVELOPMENT_EVIDENCE_LOCK_PENDING"

    locked = SimpleNamespace(
        manifest_sha256=DEVELOPMENT_MANIFEST_SHA256,
        attribution_report_sha256=RECORDED_ATTRIBUTION_REPORT_SHA256,
        contract=SimpleNamespace(timeframe="6h", products=("BTC-USD", "ETH-USD")),
        assets={"BTC-USD": pd.DataFrame({"x": [1]}), "ETH-USD": pd.DataFrame({"x": [1]})},
        strategy_engines={name: object() for name in VARIANT_ORDER},
        configuration=alpha_development_configuration(),
    )
    monkeypatch.setattr(
        protocol_module.AlphaDevelopmentPreregistration,
        "lock",
        lambda self, manifest, report: locked,
    )
    assert main(["--manifest", "m.json", "--attribution-report", "a.json"]) == 0
    output = json.loads(capsys.readouterr().out)
    assert output["status"] == "ALPHA_DEVELOPMENT_EVIDENCE_LOCKED"
    assert output["asset_rows"] == {"BTC-USD": 1, "ETH-USD": 1}
    assert output["joint_performance_evaluation_executed"] is False
    assert output["performance_runner_review_completed"] is True
    assert output["runner_execution_requires_same_process_evidence_lock"] is True
    assert output["candidate_v2_authorized"] is False


def test_cli_requires_manifest_and_attribution_report_together():
    with pytest.raises(SystemExit):
        main(["--manifest", "manifest.json"])
