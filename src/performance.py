import numpy as np


def calculate_win_rate(trades):

    if len(trades) == 0:
        return 0

    wins = len([t for t in trades if t > 0])

    return wins / len(trades) * 100


def calculate_average_win(trades):

    wins = [t for t in trades if t > 0]

    if len(wins) == 0:
        return 0

    return np.mean(wins)


def calculate_average_loss(trades):

    losses = [t for t in trades if t <= 0]

    if len(losses) == 0:
        return 0

    return np.mean(losses)


def calculate_profit_factor(trades):

    gross_profit = sum([t for t in trades if t > 0])

    gross_loss = abs(sum([t for t in trades if t < 0]))

    if gross_loss == 0:
        return 999

    return gross_profit / gross_loss


def calculate_expectancy(trades):

    if len(trades) == 0:
        return 0

    win_rate = calculate_win_rate(trades) / 100

    loss_rate = 1 - win_rate

    avg_win = calculate_average_win(trades)

    avg_loss = abs(calculate_average_loss(trades))

    return (win_rate * avg_win) - (loss_rate * avg_loss)
def calculate_max_drawdown(equity_curve):

    if len(equity_curve) == 0:
        return 0

    peak = equity_curve[0]
    max_drawdown = 0

    for value in equity_curve:

        if value > peak:
            peak = value

        drawdown = (peak - value) / peak * 100

        if drawdown > max_drawdown:
            max_drawdown = drawdown

    return max_drawdown


def calculate_sharpe_ratio(returns):

    if len(returns) < 2:
        return 0

    std = np.std(returns)

    if std == 0:
        return 0

    return np.mean(returns) / std


def calculate_sortino_ratio(returns):

    if len(returns) < 2:
        return 0

    downside = [r for r in returns if r < 0]

    if len(downside) == 0:
        return 999

    downside_std = np.std(downside)

    if downside_std == 0:
        return 0

    return np.mean(returns) / downside_std


def calculate_calmar_ratio(total_return, max_drawdown):

    if max_drawdown == 0:
        return 999

    return total_return / max_drawdown
def calculate_performance(trades, equity_curve, total_return):

    performance = {

        "win_rate": calculate_win_rate(trades),

        "average_win": calculate_average_win(trades),

        "average_loss": calculate_average_loss(trades),

        "profit_factor": calculate_profit_factor(trades),

        "expectancy": calculate_expectancy(trades),

        "max_drawdown": calculate_max_drawdown(equity_curve),

        "sharpe": calculate_sharpe_ratio(trades),

        "sortino": calculate_sortino_ratio(trades),

        "calmar": calculate_calmar_ratio(
            total_return,
            calculate_max_drawdown(equity_curve)
        ),
    }

    return performance