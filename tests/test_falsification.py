import math

import pytest

from src.falsification import StatisticalFalsificationEngine


def trades(values):
    return [{"profit_loss": value} for value in values]


def test_rejects_invalid_simulation_count():
    with pytest.raises(ValueError):
        StatisticalFalsificationEngine(simulations=0)


def test_rejects_non_integer_simulation_count():
    with pytest.raises(TypeError):
        StatisticalFalsificationEngine(simulations=10.5)


def test_rejects_invalid_confidence_level():
    with pytest.raises(ValueError):
        StatisticalFalsificationEngine(confidence_level=1.0)


def test_rejects_invalid_seed():
    with pytest.raises(TypeError):
        StatisticalFalsificationEngine(random_seed="42")


def test_rejects_empty_trade_history():
    with pytest.raises(ValueError):
        StatisticalFalsificationEngine().analyze([])


def test_rejects_missing_profit_loss():
    with pytest.raises(ValueError):
        StatisticalFalsificationEngine().analyze([{}])


def test_rejects_non_finite_profit_loss():
    with pytest.raises(ValueError):
        StatisticalFalsificationEngine().analyze(trades([1.0, math.inf]))


def test_bootstrap_is_reproducible_with_same_seed():
    history = trades([8, 10, 12, 9, 11])
    first = StatisticalFalsificationEngine(simulations=200, random_seed=7).bootstrap_expectancy(history)
    second = StatisticalFalsificationEngine(simulations=200, random_seed=7).bootstrap_expectancy(history)
    assert first == second


def test_bootstrap_supports_clear_positive_edge():
    result = StatisticalFalsificationEngine(simulations=500, random_seed=1).bootstrap_expectancy(
        trades([8, 9, 10, 11, 12, 9, 10, 11])
    )
    assert result["ci_lower"] > 0
    assert result["positive_edge_supported"] is True


def test_bootstrap_does_not_support_mixed_edge():
    result = StatisticalFalsificationEngine(simulations=500, random_seed=2).bootstrap_expectancy(
        trades([-10, 10, -9, 9, -8, 8])
    )
    assert result["positive_edge_supported"] is False


def test_monte_carlo_drawdown_is_reproducible():
    history = trades([10, -4, 8, -12, 6, 5, -3])
    engine = StatisticalFalsificationEngine(simulations=250, random_seed=99)
    assert engine.monte_carlo_drawdown(history) == engine.monte_carlo_drawdown(history)


def test_monte_carlo_reports_non_negative_drawdowns():
    result = StatisticalFalsificationEngine(simulations=100, random_seed=3).monte_carlo_drawdown(
        trades([10, -5, 7, -2])
    )
    assert result["observed_max_drawdown"] >= 0
    assert result["drawdown_95th_percentile"] >= 0
    assert result["worst_simulated_drawdown"] >= result["drawdown_95th_percentile"]


def test_permutation_detects_strong_positive_edge():
    result = StatisticalFalsificationEngine(simulations=2000, confidence_level=0.95, random_seed=5).permutation_test(
        trades([10] * 12)
    )
    assert result["p_value"] < 0.05
    assert result["significant_positive_edge"] is True


def test_permutation_rejects_zero_edge():
    result = StatisticalFalsificationEngine(simulations=1000, random_seed=5).permutation_test(
        trades([-10, 10, -10, 10, -10, 10])
    )
    assert result["significant_positive_edge"] is False


def test_analyze_requires_both_edge_tests_to_pass():
    result = StatisticalFalsificationEngine(simulations=2000, random_seed=11).analyze(
        trades([10] * 12)
    )
    assert result["bootstrap"]["positive_edge_supported"] is True
    assert result["permutation"]["significant_positive_edge"] is True
    assert result["passes_statistical_falsification"] is True


def test_analyze_does_not_pass_unconvincing_history():
    result = StatisticalFalsificationEngine(simulations=500, random_seed=11).analyze(
        trades([-5, 5, -4, 4, -3, 3])
    )
    assert result["passes_statistical_falsification"] is False
