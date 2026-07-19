"""
AI Alpha Engine
----------------

Module: Data Visualization

Purpose:
Visualize market data, technical indicators, and trading signals
using candlestick charts.

Current Features:
- Load market data from CSV
- Display candlestick chart
- Plot EMA20 and EMA50
- Display BUY/SELL signals
- Display trading volume

This module is part of Phase 1 – Data Foundation.
"""
import os
import pandas as pd
import mplfinance as mpf



def plot_chart(csv_file):
    """
    Plot a candlestick chart from a CSV file.

    Parameters
    ----------
    csv_file : str
        Path to the CSV file containing OHLCV data,
        technical indicators, and trading signals.
    """

    if not os.path.exists(csv_file):
        raise FileNotFoundError(f"CSV file not found: {csv_file}")

    df = pd.read_csv(csv_file, header=[0, 1], index_col=0)

    df.index = pd.to_datetime(df.index)
    df.columns = df.columns.get_level_values(0)

    required_columns = [
        "Open",
        "High",
        "Low",
        "Close",
        "Volume",
        "EMA20",
        "EMA50",
        
    ]

    missing_columns = [
        column for column in required_columns
        if column not in df.columns
    ]

    if missing_columns:
        raise ValueError(
            f"Missing required columns: {', '.join(missing_columns)}"
        )

        # Position markers slightly below/above candles (if signals exist)
    if "Signal" in df.columns:
        buy = df["Low"].where(df["Signal"] == 1) * 0.995
        sell = df["High"].where(df["Signal"] == -1) * 1.005
    else:
        buy = None
        sell = None

    apds = [
    mpf.make_addplot(df["EMA20"], color="blue", width=1),
    mpf.make_addplot(df["EMA50"], color="orange", width=1),
]

    if buy is not None:
        apds.append(
            mpf.make_addplot(
                buy,
                type="scatter",
                marker="^",
                markersize=40,
                color="green",
            )
        )

        apds.append(
            mpf.make_addplot(
                sell,
                type="scatter",
                marker="v",
                markersize=40,
                color="red",
            )
        )

    ticker = os.path.splitext(os.path.basename(csv_file))[0]
    chart_title = f"{ticker} Price Chart"

    mpf.plot(
        df,
        type="candle",
        style="yahoo",
        volume=True,
        addplot=apds,
        title=chart_title,
        figsize=(15, 8),
    )

if __name__ == "__main__":
    plot_chart("data/AAPL.csv")