import os
import sys
import pytest

sys.path.append(
    os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src"))
)

from performance_analysis import PerformanceAnalyzer


def test_performance_analyzer_initialization():
    analyzer = PerformanceAnalyzer(10000)

    assert analyzer.initial_capital == 10000.0


def test_performance_analyzer_rejects_non_numeric_initial_capital():
    with pytest.raises(
        TypeError,
        match="Initial capital must be a number.",
    ):
        PerformanceAnalyzer("10000")


def test_performance_analyzer_rejects_non_positive_initial_capital():
    with pytest.raises(
        ValueError,
        match="Initial capital must be greater than zero.",
    ):
        PerformanceAnalyzer(0)


def test_calculate_rejects_invalid_trade_history():
    analyzer = PerformanceAnalyzer(10000)

    with pytest.raises(
        TypeError,
        match="Trade history must be a list.",
    ):
        analyzer.calculate({}, [])


def test_calculate_rejects_invalid_equity_curve():
    analyzer = PerformanceAnalyzer(10000)

    with pytest.raises(
        TypeError,
        match="Equity curve must be a list.",
    ):
        analyzer.calculate([], {})


def test_calculate_returns_dictionary():
    analyzer = PerformanceAnalyzer(10000)

    result = analyzer.calculate([], [])

    assert isinstance(result, dict)
    assert result == {
    "total_return": 0.0,
    "number_of_trades": 0,
    "winning_trades": 0,
    "losing_trades": 0,
    "win_rate": 0.0,
    "average_win": 0.0,
    "average_loss": 0.0,
    "profit_factor": 0.0,
    "max_drawdown": 0.0,
    "expectancy": 0.0,
    "sharpe_ratio": 0.0,
}

def test_total_return_is_zero_for_empty_equity_curve():
    analyzer = PerformanceAnalyzer(10000)

    result = analyzer.calculate([], [])

    assert result["total_return"] == 0.0

def test_total_return_is_positive():
    analyzer = PerformanceAnalyzer(10000)

    equity_curve = [
        {"index": 0, "equity": 10000.0},
        {"index": 1, "equity": 11000.0},
    ]

    result = analyzer.calculate([], equity_curve)

    assert result["total_return"] == 10.0

def test_total_return_is_negative():
    analyzer = PerformanceAnalyzer(10000)

    equity_curve = [
        {"index": 0, "equity": 10000.0},
        {"index": 1, "equity": 9000.0},
    ]

    result = analyzer.calculate([], equity_curve)

    assert result["total_return"] == -10.0

def test_total_return_is_zero():
    analyzer = PerformanceAnalyzer(10000)

    equity_curve = [
        {"index": 0, "equity": 10000.0},
        {"index": 1, "equity": 10000.0},
    ]

    result = analyzer.calculate([], equity_curve)

    assert result["total_return"] == 0.0

def test_number_of_trades_is_zero():
    analyzer = PerformanceAnalyzer(10000)

    result = analyzer.calculate([], [])

    assert result["number_of_trades"] == 0


def test_number_of_trades_is_one():
    analyzer = PerformanceAnalyzer(10000)

    trade_history = [
        {
            "entry_price": 100,
            "exit_price": 110,
            "profit_loss": 10,
        }
    ]

    result = analyzer.calculate(trade_history, [])

    assert result["number_of_trades"] == 1


def test_number_of_trades_is_three():
    analyzer = PerformanceAnalyzer(10000)

    trade_history = [
        {
            "entry_price": 100,
            "exit_price": 105,
            "profit_loss": 5,
        },
        {
            "entry_price": 110,
            "exit_price": 120,
            "profit_loss": 10,
        },
        {
            "entry_price": 90,
            "exit_price": 95,
            "profit_loss": 5,
        },
    ]

    result = analyzer.calculate(trade_history, [])

    assert result["number_of_trades"] == 3

def test_winning_trades_is_zero():
    analyzer = PerformanceAnalyzer(10000)

    result = analyzer.calculate([], [])

    assert result["winning_trades"] == 0

def test_losing_trades_is_zero():
    analyzer = PerformanceAnalyzer(10000)

    result = analyzer.calculate([], [])

    assert result["losing_trades"] == 0

def test_winning_and_losing_trades():
    analyzer = PerformanceAnalyzer(10000)

    trade_history = [
        {"profit_loss": 100},
        {"profit_loss": -50},
        {"profit_loss": 200},
        {"profit_loss": -25},
        {"profit_loss": 0},
    ]

    result = analyzer.calculate(trade_history, [])

    assert result["winning_trades"] == 2
    assert result["losing_trades"] == 2

def test_all_winning_trades():
    analyzer = PerformanceAnalyzer(10000)

    trade_history = [
        {"profit_loss": 50},
        {"profit_loss": 100},
        {"profit_loss": 25},
    ]

    result = analyzer.calculate(trade_history, [])

    assert result["winning_trades"] == 3
    assert result["losing_trades"] == 0

def test_win_rate_is_zero_when_there_are_no_trades():
    analyzer = PerformanceAnalyzer(10000)

    result = analyzer.calculate([], [])

    assert result["win_rate"] == 0.0


def test_win_rate_is_calculated_from_all_completed_trades():
    analyzer = PerformanceAnalyzer(10000)

    trade_history = [
        {"profit_loss": 100},
        {"profit_loss": -50},
        {"profit_loss": 200},
        {"profit_loss": -25},
        {"profit_loss": 0},
    ]

    result = analyzer.calculate(trade_history, [])

    assert result["win_rate"] == 40.0

def test_average_win_is_zero_when_there_are_no_winning_trades():
    analyzer = PerformanceAnalyzer(10000)

    trade_history = [
        {"profit_loss": -50},
        {"profit_loss": 0},
    ]

    result = analyzer.calculate(trade_history, [])

    assert result["average_win"] == 0.0


def test_average_win_is_calculated_from_winning_trades_only():
    analyzer = PerformanceAnalyzer(10000)

    trade_history = [
        {"profit_loss": 100},
        {"profit_loss": -50},
        {"profit_loss": 200},
        {"profit_loss": 0},
    ]

    result = analyzer.calculate(trade_history, [])

    assert result["average_win"] == 150.0

def test_average_loss_is_zero_when_there_are_no_losing_trades():
    analyzer = PerformanceAnalyzer(10000)

    trade_history = [
        {"profit_loss": 100},
        {"profit_loss": 0},
    ]

    result = analyzer.calculate(trade_history, [])

    assert result["average_loss"] == 0.0


def test_average_loss_is_calculated_from_losing_trades_only():
    analyzer = PerformanceAnalyzer(10000)

    trade_history = [
        {"profit_loss": 100},
        {"profit_loss": -50},
        {"profit_loss": -150},
        {"profit_loss": 0},
    ]

    result = analyzer.calculate(trade_history, [])

    assert result["average_loss"] == -100.0

def test_profit_factor_is_zero_when_there_are_no_trades():
    analyzer = PerformanceAnalyzer(10000)

    result = analyzer.calculate([], [])

    assert result["profit_factor"] == 0.0


def test_profit_factor_is_infinite_when_there_are_wins_but_no_losses():
    analyzer = PerformanceAnalyzer(10000)

    trade_history = [
        {"profit_loss": 100},
        {"profit_loss": 200},
        {"profit_loss": 0},
    ]

    result = analyzer.calculate(trade_history, [])

    assert result["profit_factor"] == float("inf")


def test_profit_factor_is_calculated_from_total_wins_and_losses():
    analyzer = PerformanceAnalyzer(10000)

    trade_history = [
        {"profit_loss": 100},
        {"profit_loss": -50},
        {"profit_loss": 200},
        {"profit_loss": -100},
        {"profit_loss": 0},
    ]

    result = analyzer.calculate(trade_history, [])

    assert result["profit_factor"] == 2.0

def test_max_drawdown_is_zero_when_equity_curve_is_empty():
    analyzer = PerformanceAnalyzer(10000)

    result = analyzer.calculate([], [])

    assert result["max_drawdown"] == 0.0


def test_max_drawdown_is_zero_when_equity_curve_never_declines():
    analyzer = PerformanceAnalyzer(10000)

    equity_curve = [
        {"equity": 10000},
        {"equity": 11000},
        {"equity": 12000},
        {"equity": 13000},
    ]

    result = analyzer.calculate([], equity_curve)

    assert result["max_drawdown"] == 0.0


def test_max_drawdown_is_calculated_from_peak_to_trough():
    analyzer = PerformanceAnalyzer(10000)

    equity_curve = [
        {"equity": 10000},
        {"equity": 12000},
        {"equity": 9000},
        {"equity": 11000},
    ]

    result = analyzer.calculate([], equity_curve)

    assert result["max_drawdown"] == 25.0

def test_expectancy_is_zero_when_there_are_no_trades():
    analyzer = PerformanceAnalyzer(10000)

    result = analyzer.calculate([], [])

    assert result["expectancy"] == 0.0


def test_expectancy_is_positive():
    analyzer = PerformanceAnalyzer(10000)

    trade_history = [
        {"profit_loss": 200},
        {"profit_loss": -100},
    ]

    result = analyzer.calculate(trade_history, [])

    assert result["expectancy"] == 50.0


def test_expectancy_is_negative():
    analyzer = PerformanceAnalyzer(10000)

    trade_history = [
        {"profit_loss": 100},
        {"profit_loss": -300},
    ]

    result = analyzer.calculate(trade_history, [])

    assert result["expectancy"] == -100.0

def test_sharpe_ratio_is_zero_when_equity_curve_is_empty():
    analyzer = PerformanceAnalyzer(10000)

    result = analyzer.calculate([], [])

    assert result["sharpe_ratio"] == 0.0


def test_sharpe_ratio_is_zero_when_there_are_not_enough_returns():
    analyzer = PerformanceAnalyzer(10000)

    equity_curve = [
        {"equity": 10000},
        {"equity": 11000},
    ]

    result = analyzer.calculate([], equity_curve)

    assert result["sharpe_ratio"] == 0.0


def test_sharpe_ratio_is_zero_when_return_volatility_is_zero():
    analyzer = PerformanceAnalyzer(10000)

    equity_curve = [
        {"equity": 10000},
        {"equity": 11000},
        {"equity": 12100},
    ]

    result = analyzer.calculate([], equity_curve)

    assert result["sharpe_ratio"] == 0.0


def test_sharpe_ratio_is_calculated_from_equity_returns():
    analyzer = PerformanceAnalyzer(10000)

    equity_curve = [
        {"equity": 10000},
        {"equity": 11000},
        {"equity": 11000},
    ]

    result = analyzer.calculate([], equity_curve)

    assert result["sharpe_ratio"] == pytest.approx(
        0.7071067811865476
    )