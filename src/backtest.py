import pandas as pd

from chart import plot_chart
from performance import calculate_performance
from strategy import generate_signals


def run_backtest(df, show_chart=False):

    initial_capital = 10000.0

    capital = initial_capital

    shares = 0.0

    position = 0

    entry_price = 0.0

    trades = []

    equity_curve = []

    trade_history = []

    position_history = []

    for index, row in df.iterrows():

        price = float(row["Close"])

        signal = int(row["Signal"])

        if position == 0:

            equity = capital

        else:

            equity = shares * price

        equity_curve.append(equity)

        position_history.append(position)

        # BUY

        if signal == 1 and position == 0:

            shares = capital / price

            capital = 0.0

            position = 1

            entry_price = price

            continue
                # SELL

        if signal == -1 and position == 1:

            exit_price = price

            capital = shares * exit_price

            trade_return = (
                (exit_price - entry_price)
                / entry_price
                * 100
            )

            trades.append(trade_return)

            trade_history.append({

                "entry_price": entry_price,

                "exit_price": exit_price,

                "return": trade_return,

                "shares": shares

            })

            shares = 0.0

            position = 0

            entry_price = 0.0

    if position == 1:

        last_price = float(df.iloc[-1]["Close"])

        capital = shares * last_price

        trade_return = (
            (last_price - entry_price)
            / entry_price
            * 100
        )

        trades.append(trade_return)

        trade_history.append({

            "entry_price": entry_price,

            "exit_price": last_price,

            "return": trade_return,

            "shares": shares

        })
            # PERFORMANCE METRICS

    winning_trades = [t for t in trades if t > 0]
    losing_trades = [t for t in trades if t <= 0]

    total_trades = len(trades)

    if total_trades > 0:
        win_rate = len(winning_trades) / total_trades * 100
    else:
        win_rate = 0
    result = {
        "initial_capital": initial_capital,
        "final_capital": capital,
        "profit": capital - initial_capital,
        "return": (capital / initial_capital - 1) * 100,
        "trades": total_trades,
        "winning_trades": len(winning_trades),
        "losing_trades": len(losing_trades),
        "win_rate": win_rate,
    }
    performance = calculate_performance(
        trades,
        equity_curve,
        result["return"]
    )

    result.update(performance)
    if show_chart:
        plot_chart("data/AAPL.csv")

    return result
if __name__ == "__main__":

    df = pd.read_csv("data/AAPL.csv", index_col=0)
    df = generate_signals(df)

    result = run_backtest(df)

    print("\n==============================")
    print("PERFORMANCE REPORT")
    print("==============================")

    print(f"Initial Capital : ${result['initial_capital']:.2f}")
    print(f"Final Capital   : ${result['final_capital']:.2f}")
    print(f"Profit          : ${result['profit']:.2f}")
    print(f"Return          : {result['return']:.2f}%")

    print(f"Trades          : {result['trades']}")
    print(f"Winning Trades  : {result['winning_trades']}")
    print(f"Losing Trades   : {result['losing_trades']}")
    print(f"Win Rate        : {result['win_rate']:.2f}%")