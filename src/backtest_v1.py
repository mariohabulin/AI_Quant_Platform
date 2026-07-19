import pandas as pd
from chart import plot_chart


def run_backtest(df, show_chart=False):

    initial_capital = 10000
    capital = initial_capital
    position = 0
    shares = 0

    trades = []

    entry_price = 0

    for _, row in df.iterrows():

        price = row["Close"]
        signal = row["Signal"]

        # BUY
        if signal == 1 and position == 0:

            shares = capital / price
            capital = 0
            position = 1
            entry_price = price

        # SELL
        elif signal == -1 and position == 1:

            capital = shares * price

            trade_return = (price - entry_price) / entry_price * 100

            trades.append(trade_return)

            shares = 0
            position = 0

    # Ako je pozicija otvorena na kraju
    if position == 1:

        last_price = df.iloc[-1]["Close"]

        capital = shares * last_price

        trade_return = (last_price - entry_price) / entry_price * 100

        trades.append(trade_return)

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

    if show_chart:
        plot_chart("data/AAPL.csv")

    return result


if __name__ == "__main__":

    df = pd.read_csv("data/AAPL.csv", index_col=0)

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