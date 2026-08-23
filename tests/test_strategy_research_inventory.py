import hashlib
import json
import os
from pathlib import Path
import sys

import numpy as np
import pandas as pd
import pytest

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src")))

import strategy_research_inventory as inventory_module
from research_evidence import canonical_json_bytes
from strategy_research_inventory import (
    RECORDED_TIMEFRAME_STUDY_SHA256,
    STRATEGY_RESEARCH_INVENTORY_ID,
    STRATEGY_SPECS,
    analyze_recorded_study,
    audit_strategy_integrations,
    inventory_declaration,
    load_recorded_study_report,
    main,
)


def recorded_profile(
    classification="REJECTED",
    oos_return=-0.10,
    benchmark_return=-0.05,
    excess_return=-0.05,
    drawdown=25.0,
    oos_trades=12,
    walk_forward_trades=40,
    positive_rate=0.20,
    falsification=False,
):
    return {
        "validation_classification": classification,
        "oos_strategy_return": oos_return,
        "oos_benchmark_return": benchmark_return,
        "oos_excess_return": excess_return,
        "oos_max_drawdown_percent": drawdown,
        "oos_trade_count": oos_trades,
        "walk_forward_window_count": 11,
        "unseen_walk_forward_trade_count": walk_forward_trades,
        "positive_walk_forward_excess_rate": positive_rate,
        "passes_statistical_falsification": falsification,
        "bootstrap_ci_lower": -2.0,
        "bootstrap_ci_upper": 3.0,
        "permutation_p_value": 0.50,
    }


def recorded_study_payload():
    timeframes = {}
    for timeframe in ("1h", "6h", "1d"):
        assets = {}
        for asset in ("BTC-USD", "ETH-USD"):
            assets[asset] = {
                "baseline": recorded_profile(),
                "stress": recorded_profile(oos_return=-0.15, drawdown=30.0),
            }
        timeframes[timeframe] = {
            "baseline_aggregate_classification": "REJECTED",
            "cost_stress_aggregate_classification": "REJECTED",
            "assets": assets,
        }
    return {
        "schema_version": 3,
        "status": "TIMEFRAME_SENSITIVITY_COMPLETED",
        "study_id": "ema-20-50-btc-eth-timeframe-sensitivity-v1",
        "comparison": {
            "timeframe_order": ["1h", "6h", "1d"],
            "selection_policy": "NONE_EXPLORATORY_ONLY",
            "automatic_ranking_generated": False,
            "timeframes": timeframes,
        },
        "candidate_v1_reopened": False,
        "automatic_timeframe_selection": False,
        "formal_candidate_evaluation": False,
        "candidate_v2_authorized": False,
        "optimization_authorized": False,
        "bounded_forward_paper_review_eligible": False,
        "bounded_forward_paper_authorized": False,
        "live_execution_authorized": False,
    }


def write_recorded_study(tmp_path, payload=None):
    tmp_path.mkdir(parents=True, exist_ok=True)
    payload = recorded_study_payload() if payload is None else payload
    report_path = tmp_path / "timeframe_sensitivity_report.json"
    report_bytes = canonical_json_bytes(payload)
    report_path.write_bytes(report_bytes)
    digest = hashlib.sha256(report_bytes).hexdigest()
    report_path.with_name("timeframe_sensitivity_report.sha256").write_bytes(
        f"{digest}  timeframe_sensitivity_report.json\n".encode("ascii")
    )
    return report_path, digest


def test_inventory_freezes_exact_existing_strategy_scope_without_screening():
    declaration = inventory_declaration()

    assert declaration["status"] == "STRATEGY_RESEARCH_INVENTORY_DECLARED"
    assert declaration["inventory_id"] == STRATEGY_RESEARCH_INVENTORY_ID
    assert declaration["strategy_count"] == 9
    assert [item["strategy_name"] for item in declaration["strategies"]] == [
        "adx",
        "atr",
        "bollinger",
        "donchian",
        "ema_crossover",
        "macd",
        "rsi",
        "stochastic",
        "supertrend",
    ]
    assert declaration["remaining_unevaluated_strategy_count"] == 8
    assert declaration["strategy_screening_executed"] is False
    assert declaration["automatic_ranking_authorized"] is False
    assert declaration["parameter_sweep_authorized"] is False
    assert declaration["candidate_v2_authorized"] is False
    assert declaration["live_execution_authorized"] is False


def test_inventory_defaults_match_actual_strategy_implementations():
    for spec in STRATEGY_SPECS:
        strategy = spec.factory()
        assert strategy.name == spec.strategy_name
        assert {
            name: getattr(strategy, name)
            for name, _ in spec.default_parameters
        } == dict(spec.default_parameters)


def test_inventory_separates_families_and_research_status():
    declaration = inventory_declaration()
    strategies = {
        item["strategy_name"]: item for item in declaration["strategies"]
    }

    assert strategies["ema_crossover"]["research_status"] == (
        "CLOSED_REJECTED_CANDIDATE_V1"
    )
    assert all(
        item["research_status"] == "UNEVALUATED_RESEARCH_COMPONENT"
        for name, item in strategies.items()
        if name != "ema_crossover"
    )
    assert strategies["rsi"]["family"] == "MEAN_REVERSION"
    assert strategies["donchian"]["family"] == "BREAKOUT"
    assert strategies["supertrend"]["family"] == "TREND"


def test_synthetic_integration_audit_passes_without_market_evaluation():
    audit = audit_strategy_integrations()

    assert audit["status"] == "STRATEGY_INTEGRATION_AUDIT_PASS"
    assert audit["strategy_count"] == 9
    assert audit["performance_evaluation_executed"] is False
    assert audit["market_dataset_used"] is False
    assert audit["automatic_ranking_generated"] is False
    assert audit["candidate_v2_authorized"] is False
    assert all(item["integration_ready"] for item in audit["strategies"])
    assert all(item["checks"]["prefix_causal"] for item in audit["strategies"])
    assert all(item["checks"]["buy_signal_observed"] for item in audit["strategies"])
    assert all(item["checks"]["sell_signal_observed"] for item in audit["strategies"])


def test_recorded_study_loader_requires_canonical_bytes_hash_and_sidecar(tmp_path):
    report_path, digest = write_recorded_study(tmp_path)

    payload, actual = load_recorded_study_report(
        report_path,
        expected_sha256=digest,
    )

    assert actual == digest
    assert payload["status"] == "TIMEFRAME_SENSITIVITY_COMPLETED"

    report_path.with_name("timeframe_sensitivity_report.sha256").write_text(
        "bad sidecar\n",
        encoding="ascii",
    )
    with pytest.raises(ValueError, match="sidecar"):
        load_recorded_study_report(report_path, expected_sha256=digest)


def test_recorded_study_loader_rejects_authorization_or_identity_drift(tmp_path):
    payload = recorded_study_payload()
    payload["candidate_v2_authorized"] = True
    report_path, digest = write_recorded_study(tmp_path, payload)

    with pytest.raises(ValueError, match="authorization boundary"):
        load_recorded_study_report(report_path, expected_sha256=digest)

    identity = recorded_study_payload()
    identity["study_id"] = "other-study"
    identity_path, identity_digest = write_recorded_study(
        tmp_path / "identity",
        identity,
    )
    with pytest.raises(ValueError, match="identity"):
        load_recorded_study_report(
            identity_path,
            expected_sha256=identity_digest,
        )


def test_failure_mode_analysis_reports_facts_without_ranking_or_selection():
    analysis = analyze_recorded_study(
        recorded_study_payload(),
        "a" * 64,
    )

    assert analysis["status"] == "RECORDED_FAILURE_MODES_ANALYZED"
    assert analysis["profile_count"] == 12
    assert analysis["all_aggregate_profiles_rejected"] is True
    assert analysis["all_asset_profiles_rejected"] is True
    assert analysis["all_statistical_falsification_failed"] is True
    assert analysis["automatic_ranking_generated"] is False
    assert analysis["selected_strategy"] is None
    assert analysis["selected_timeframe"] is None
    assert analysis["strategy_screening_executed"] is False
    assert analysis["candidate_v2_authorized"] is False
    assert analysis["observations"]["1h"]["BTC-USD"]["baseline"][
        "oos_trade_count"
    ] == 12
    assert "REDUCE_TURNOVER_OR_PROVE_COST_SURVIVAL" in analysis[
        "next_hypothesis_constraints"
    ]


def test_cli_declaration_and_audit_are_non_activating(capsys):
    assert main([]) == 0
    declaration = json.loads(capsys.readouterr().out)
    assert declaration["strategy_screening_executed"] is False

    assert main(["--audit-integrations"]) == 0
    audited = json.loads(capsys.readouterr().out)
    assert audited["integration_audit"]["status"] == (
        "STRATEGY_INTEGRATION_AUDIT_PASS"
    )
    assert audited["strategy_screening_executed"] is False


def test_cli_analyzes_only_exact_recorded_evidence(monkeypatch, tmp_path, capsys):
    report_path, digest = write_recorded_study(tmp_path)
    monkeypatch.setattr(
        inventory_module,
        "RECORDED_TIMEFRAME_STUDY_SHA256",
        digest,
    )

    assert main(["--study-report", str(report_path)]) == 0
    output = json.loads(capsys.readouterr().out)

    assert output["failure_mode_analysis"]["source_report_sha256"] == digest
    assert output["failure_mode_analysis"]["selected_strategy"] is None
    assert output["strategy_screening_executed"] is False
    assert output["live_execution_authorized"] is False


def test_production_report_hash_remains_exactly_frozen():
    assert RECORDED_TIMEFRAME_STUDY_SHA256 == (
        "505bd5b40a38d7e5b8b4538e1d7ac9cb459cd40f46108dc1a33a42c1647b64ab"
    )
