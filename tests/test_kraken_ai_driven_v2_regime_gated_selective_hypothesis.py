import os
from pathlib import Path
import sys

import pytest


sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src")))

from kraken_ai_driven_v2_regime_gated_selective_hypothesis import (
    CONTEXT_CONFIRMATION_FEATURE_COLUMNS,
    MATCHED_CONTROL,
    PARENT_COMMIT,
    PROBABILITY_SAFETY_BUFFER,
    REGIME_FEATURE_COLUMNS,
    TERMINAL_FAILURE_STATUS,
    VARIANT_SPECS,
    break_even_positive_probability,
    classify_spot_regime,
    context_confirms_direction,
    regime_gated_selective_hypothesis_declaration,
    required_positive_probability,
    select_regime_gated_action,
)


ROOT = Path(__file__).resolve().parents[1]


def _spot(a, b, c):
    return {
        "return_14": a,
        "ema_12_48_spread": b,
        "ema_180_distance": c,
    }


def _context(funding, open_interest, basis):
    return {
        "funding_rate_zscore_60": funding,
        "open_interest_log_change_6": open_interest,
        "basis_change_1": basis,
    }


def test_declaration_is_bound_to_closed_parent_and_one_terminal_experiment():
    declaration = regime_gated_selective_hypothesis_declaration()

    assert declaration["parent_commit"] == PARENT_COMMIT
    assert declaration["parent_commit"].startswith("0511fe5")
    assert declaration["prior_closure_status"].endswith("HOLD_CASH")
    assert declaration["one_economic_development_execution"] is True
    assert declaration["terminal_failure_status"] == TERMINAL_FAILURE_STATUS
    assert TERMINAL_FAILURE_STATUS.endswith("STOP_KRAKEN_12H_RESEARCH")
    assert declaration["automatic_successor_authorized"] is False


def test_spot_regime_requires_strict_three_feature_sign_agreement():
    assert tuple(REGIME_FEATURE_COLUMNS) == (
        "return_14",
        "ema_12_48_spread",
        "ema_180_distance",
    )
    assert classify_spot_regime(_spot(0.1, 0.2, 0.3)) == "LONG_REGIME"
    assert classify_spot_regime(_spot(-0.1, -0.2, -0.3)) == "SHORT_REGIME"
    assert classify_spot_regime(_spot(0.1, -0.2, 0.3)) == "NEUTRAL"
    assert classify_spot_regime(_spot(0.0, 0.2, 0.3)) == "NEUTRAL"


def test_context_confirmation_is_directional_participation_without_crowding():
    assert tuple(CONTEXT_CONFIRMATION_FEATURE_COLUMNS) == (
        "funding_rate_zscore_60",
        "open_interest_log_change_6",
        "basis_change_1",
    )
    assert context_confirms_direction(_context(0.5, 0.01, 0.001), "LONG") is True
    assert context_confirms_direction(_context(-0.5, 0.01, -0.001), "SHORT") is True
    assert context_confirms_direction(_context(1.01, 0.01, 0.001), "LONG") is False
    assert context_confirms_direction(_context(-1.01, 0.01, -0.001), "SHORT") is False
    assert context_confirms_direction(_context(0.0, 0.0, 0.001), "LONG") is False
    assert context_confirms_direction(_context(0.0, 0.01, -0.001), "LONG") is False


def test_payoff_derived_threshold_has_fixed_five_point_safety_buffer():
    assert PROBABILITY_SAFETY_BUFFER == 0.05
    assert break_even_positive_probability(3.0, -1.0) == pytest.approx(0.25)
    assert required_positive_probability(3.0, -1.0) == pytest.approx(0.30)
    assert required_positive_probability(0.01, -1.0) == 1.0


def test_payoff_derived_threshold_rejects_invalid_outcome_means():
    with pytest.raises(ValueError, match="strictly positive"):
        break_even_positive_probability(0.0, -1.0)
    with pytest.raises(ValueError, match="strictly negative"):
        break_even_positive_probability(3.0, 0.0)


@pytest.mark.parametrize(
    "regime,long_p,short_p,long_required,short_required,confirmed,expected",
    [
        ("LONG_REGIME", 0.31, 0.99, 0.30, 0.30, True, "LONG"),
        ("LONG_REGIME", 0.30, 0.99, 0.30, 0.30, True, "HOLD_CASH"),
        ("SHORT_REGIME", 0.99, 0.31, 0.30, 0.30, True, "SHORT"),
        ("SHORT_REGIME", 0.99, 0.30, 0.30, 0.30, True, "HOLD_CASH"),
        ("NEUTRAL", 0.99, 0.99, 0.30, 0.30, True, "HOLD_CASH"),
        ("LONG_REGIME", 0.99, 0.01, 0.30, 0.30, False, "HOLD_CASH"),
    ],
)
def test_action_uses_only_regime_direction_and_strict_economic_threshold(
    regime, long_p, short_p, long_required, short_required, confirmed, expected
):
    assert (
        select_regime_gated_action(
            regime,
            long_probability=long_p,
            short_probability=short_p,
            long_required_probability=long_required,
            short_required_probability=short_required,
            context_confirmed=confirmed,
        )
        == expected
    )


def test_variant_and_fit_budget_is_exact_and_small():
    declaration = regime_gated_selective_hypothesis_declaration()

    assert list(VARIANT_SPECS) == [
        "SPOT_REGIME_CALIBRATED_LOGISTIC_CONTROL",
        "SPOT_CONTEXT_REGIME_CALIBRATED_LOGISTIC",
    ]
    assert declaration["matched_control"] == MATCHED_CONTROL
    assert declaration["maximum_base_model_fits"] == 12
    assert declaration["maximum_calibrator_fits"] == 12
    assert declaration["maximum_total_fits"] == 24
    assert declaration["new_indicator_count"] == 0
    assert declaration["class_weight"] is None
    assert declaration["direct_net_r_regression_authorized"] is False


def test_declaration_keeps_all_real_learning_and_later_boundaries_closed():
    declaration = regime_gated_selective_hypothesis_declaration()
    required_false = (
        "source_values_opened",
        "labels_generated",
        "model_training_executed",
        "direct_net_r_regression_authorized",
        "feature_search_authorized",
        "hyperparameter_sweep_authorized",
        "threshold_sweep_authorized",
        "top_k_rule_authorized",
        "automatic_model_selection",
        "automatic_successor_authorized",
        "calibration_data_opened",
        "evaluation_data_opened",
        "candidate_v2_authorized",
        "bounded_forward_paper_authorized",
        "cloud_execution_authorized",
        "real_orders_submitted",
        "live_execution_authorized",
    )
    assert all(declaration[field] is False for field in required_false)


def test_protocol_records_material_change_and_terminal_stop():
    protocol = (
        ROOT
        / "KRAKEN_BTC_ETH_XRP_AI_DRIVEN_V2_REGIME_GATED_SELECTIVE_DEVELOPMENT_HYPOTHESIS_PROTOCOL_V1.md"
    ).read_text(encoding="utf-8")
    normalized = " ".join(protocol.split())
    for marker in (
        "No new indicator is created",
        "strictly positive",
        "strictly negative",
        "break-even value plus an immutable `0.05`",
        "Exactly one economic Development execution",
        "STOP_KRAKEN_12H_RESEARCH",
        "There is no threshold relaxation",
        "Calibration, Evaluation, Candidate v2",
    ):
        assert marker in normalized
