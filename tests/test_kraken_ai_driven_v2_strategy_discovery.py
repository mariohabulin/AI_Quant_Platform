import copy
import os
import sys

import pytest


sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src")))

from kraken_ai_driven_v2_strategy_discovery import (
    ASSET_ORDER,
    DISCOVERY_BUDGET,
    FAMILY_CATALOG,
    HYBRID_ARCHITECTURE_MODE,
    PROTOCOL_ID,
    REFERENCE_A_REPORT_SHA256,
    REGIME_CATALOG,
    SHARED_SAFETY_ENVELOPE,
    STATUS,
    discovery_protocol_declaration,
    validate_hypothesis_manifest,
)


def valid_manifest():
    return {
        "schema_version": 1,
        "protocol_id": PROTOCOL_ID,
        "round_id": "kraken-ai-v2-hybrid-discovery-round-1",
        "partition": "DEVELOPMENT",
        "hypotheses": [
            {
                "hypothesis_id": "trend-pullback-btc-eth-r1-v1",
                "family_id": "TREND_PULLBACK_CONTINUATION",
                "asset_scope": ["BTC-USD", "ETH-USD"],
                "regime_scope": ["UPTREND_PULLBACK"],
                "indicator_set": ["EMA", "ADX", "VOLUME_RATIO"],
                "economic_thesis": (
                    "A causal pullback inside an established trend may resume "
                    "after completed-bar volume re-expansion."
                ),
                "signal_contract_id": "trend-pullback-signal-r1-v1",
                "execution_contract_id": "trend-pullback-execution-r1-v1",
                "development_gate_id": "hybrid-development-gates-r1-v1",
                "parent_hypothesis_id": None,
                "source_feedback_sha256s": [],
            },
            {
                "hypothesis_id": "range-reversion-xrp-r1-v1",
                "family_id": "RANGE_MEAN_REVERSION",
                "asset_scope": ["XRP-USD"],
                "regime_scope": ["RANGE_BOUND"],
                "indicator_set": ["RSI", "BOLLINGER_BANDS", "ATR"],
                "economic_thesis": (
                    "A completed-bar range extreme may revert when volatility "
                    "remains bounded and a causal reversal is confirmed."
                ),
                "signal_contract_id": "range-reversion-signal-r1-v1",
                "execution_contract_id": "range-reversion-execution-r1-v1",
                "development_gate_id": "hybrid-development-gates-r1-v1",
                "parent_hypothesis_id": None,
                "source_feedback_sha256s": [REFERENCE_A_REPORT_SHA256],
            },
        ],
        "development_data_access_authorized": False,
        "calibration_authorized": False,
        "evaluation_authorized": False,
        "automatic_mutation_authorized": False,
        "automatic_ranking_authorized": False,
        "candidate_v2_authorized": False,
        "round_execution_authorized": False,
    }


def test_declaration_freezes_hybrid_catalog_routing_and_cash_fallback():
    declaration = discovery_protocol_declaration()

    assert declaration["status"] == STATUS
    assert declaration["protocol_id"] == PROTOCOL_ID
    assert declaration["architecture_mode"] == HYBRID_ARCHITECTURE_MODE
    assert declaration["asset_order"] == list(ASSET_ORDER)
    assert declaration["strategy_family_order"] == [
        "CAPITULATION_RECOVERY",
        "TREND_PULLBACK_CONTINUATION",
        "RANGE_MEAN_REVERSION",
        "VOLATILITY_BREAKOUT",
    ]
    assert declaration["regime_order"] == [
        "DOWNTREND_CAPITULATION",
        "UPTREND_PULLBACK",
        "RANGE_BOUND",
        "VOLATILITY_EXPANSION",
        "UNCLASSIFIED",
    ]
    assert declaration["hold_cash_is_valid_action"] is True
    assert declaration["forced_asset_participation"] is False
    assert declaration["shared_safety_envelope"] == SHARED_SAFETY_ENVELOPE
    assert declaration["reference_a_closed"] is True
    assert declaration["reference_a_report_sha256"] == REFERENCE_A_REPORT_SHA256
    assert declaration["reference_a_rerun_authorized"] is False
    assert declaration["reference_a_policy_reuse_authorized"] is False


def test_catalog_is_bounded_and_each_family_owns_regimes_and_indicators():
    family_ids = {family["family_id"] for family in FAMILY_CATALOG}
    regime_ids = {regime["regime_id"] for regime in REGIME_CATALOG}

    assert len(FAMILY_CATALOG) == 4
    assert len(REGIME_CATALOG) == 5
    assert DISCOVERY_BUDGET == {
        "max_hypotheses_per_round": 6,
        "max_variants_per_family_per_round": 2,
        "max_routes_per_asset_per_round": 4,
        "max_rounds_under_protocol": 2,
        "max_total_hypotheses_under_protocol": 12,
        "min_indicators_per_hypothesis": 2,
        "max_indicators_per_hypothesis": 5,
    }
    assert family_ids == {
        "CAPITULATION_RECOVERY",
        "TREND_PULLBACK_CONTINUATION",
        "RANGE_MEAN_REVERSION",
        "VOLATILITY_BREAKOUT",
    }
    for family in FAMILY_CATALOG:
        assert set(family["eligible_regimes"]) <= regime_ids
        assert 2 <= len(family["permitted_indicators"])
        assert family["family_specific_signal_contract_required"] is True
        assert family["family_specific_execution_contract_required"] is True


def test_valid_manifest_preserves_asset_specific_routes_and_has_stable_hash():
    manifest = valid_manifest()
    original = copy.deepcopy(manifest)

    first = validate_hypothesis_manifest(manifest)
    second = validate_hypothesis_manifest(copy.deepcopy(manifest))

    assert manifest == original
    assert first.payload == second.payload
    assert first.sha256 == second.sha256
    assert len(first.sha256) == 64
    assert first.payload["hypothesis_count"] == 2
    assert first.payload["asset_route_counts"] == {
        "BTC-USD": 1,
        "ETH-USD": 1,
        "XRP-USD": 1,
    }
    assert first.payload["hypotheses"][0]["asset_scope"] == [
        "BTC-USD",
        "ETH-USD",
    ]
    assert first.payload["hypotheses"][1]["asset_scope"] == ["XRP-USD"]
    assert first.payload["automatic_strategy_selection"] is False
    assert first.payload["runtime_learning_or_mutation"] is False


@pytest.mark.parametrize(
    "path,value,message",
    [
        (("protocol_id",), "wrong", "protocol ID"),
        (("partition",), "CALIBRATION", "DEVELOPMENT"),
        (
            ("hypotheses", 0, "family_id"),
            "UNKNOWN_FAMILY",
            "family",
        ),
        (
            ("hypotheses", 0, "asset_scope"),
            ["ETH-USD", "BTC-USD"],
            "canonical asset order",
        ),
        (
            ("hypotheses", 0, "regime_scope"),
            ["RANGE_BOUND"],
            "regime",
        ),
        (
            ("hypotheses", 0, "indicator_set"),
            ["EMA", "RSI"],
            "indicator",
        ),
        (
            ("hypotheses", 0, "economic_thesis"),
            "too short",
            "economic thesis",
        ),
        (("evaluation_authorized",), True, "must remain false"),
        (("automatic_mutation_authorized",), True, "must remain false"),
        (("round_execution_authorized",), True, "must remain false"),
    ],
)
def test_manifest_rejects_unknown_unbounded_or_authorized_content(
    path, value, message
):
    manifest = valid_manifest()
    target = manifest
    for part in path[:-1]:
        target = target[part]
    target[path[-1]] = value

    with pytest.raises(ValueError, match=message):
        validate_hypothesis_manifest(manifest)


def test_manifest_rejects_reference_a_identity_reuse():
    manifest = valid_manifest()
    manifest["hypotheses"][0]["signal_contract_id"] = (
        "kraken-ai-v2-ccvr-reference-a-v1"
    )

    with pytest.raises(ValueError, match="Reference A identity"):
        validate_hypothesis_manifest(manifest)


def test_manifest_rejects_family_variant_budget_excess():
    manifest = valid_manifest()
    base = manifest["hypotheses"][0]
    for index in range(2):
        variant = copy.deepcopy(base)
        variant["hypothesis_id"] = f"trend-extra-{index}"
        variant["signal_contract_id"] = f"trend-signal-extra-{index}"
        variant["execution_contract_id"] = f"trend-execution-extra-{index}"
        manifest["hypotheses"].append(variant)

    with pytest.raises(ValueError, match="family variant budget"):
        validate_hypothesis_manifest(manifest)


def test_manifest_rejects_asset_route_budget_excess():
    manifest = valid_manifest()
    manifest["hypotheses"] = []
    family_templates = {
        family["family_id"]: family for family in FAMILY_CATALOG
    }
    for index, family_id in enumerate(
        (
            "CAPITULATION_RECOVERY",
            "TREND_PULLBACK_CONTINUATION",
            "RANGE_MEAN_REVERSION",
            "VOLATILITY_BREAKOUT",
            "CAPITULATION_RECOVERY",
        )
    ):
        family = family_templates[family_id]
        manifest["hypotheses"].append(
            {
                "hypothesis_id": f"btc-route-{index}",
                "family_id": family_id,
                "asset_scope": ["BTC-USD"],
                "regime_scope": [family["eligible_regimes"][0]],
                "indicator_set": list(family["permitted_indicators"][:2]),
                "economic_thesis": (
                    "This separately identified BTC route has a causal market "
                    "mechanism that is frozen before development evidence."
                ),
                "signal_contract_id": f"signal-{index}",
                "execution_contract_id": f"execution-{index}",
                "development_gate_id": "gates-r1-v1",
                "parent_hypothesis_id": None,
                "source_feedback_sha256s": [],
            }
        )

    with pytest.raises(ValueError, match="asset route budget"):
        validate_hypothesis_manifest(manifest)


def test_protocol_declaration_opens_nothing_and_authorizes_nothing():
    declaration = discovery_protocol_declaration()

    for field in (
        "dataset_opened",
        "development_data_opened",
        "calibration_data_opened",
        "evaluation_data_opened",
        "hypothesis_manifest_registered",
        "strategy_components_implemented",
        "discovery_runner_implemented",
        "development_run_authorized",
        "performance_evaluation_executed",
        "parameter_sweep_authorized",
        "automatic_ranking_authorized",
        "automatic_strategy_selection_authorized",
        "runtime_learning_authorized",
        "calibration_authorized",
        "evaluation_authorized",
        "candidate_v2_authorized",
        "bounded_forward_paper_authorized",
        "cloud_execution_authorized",
        "live_execution_authorized",
    ):
        assert declaration[field] is False
