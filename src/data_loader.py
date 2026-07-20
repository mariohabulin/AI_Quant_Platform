import yfinance as yf
import pandas as pd
from pathlib import Path

from config import (
    TICKER,
    PERIOD,
    FAST_EMA,
    SLOW_EMA,
)

DATA_DIR = Path("data")


def download_data(ticker=TICKER, period=PERIOD):

    DATA_DIR.mkdir(exist_ok=True)

    print(f"Downloading {ticker}...")

    data = yf.download(ticker, period=period)

    # Pretvori MultiIndex u obične stupce
    if isinstance(data.columns, pd.MultiIndex):
        data.columns = data.columns.get_level_values(0)

    if data.empty:
        raise ValueError(f"No data found for {ticker}")

   

    file_path = DATA_DIR / f"{ticker}.csv"

    data.to_csv(file_path)

    print(f"Saved to {file_path}")

    return data


if __name__ == "__main__":
    df = download_data()
    print(df.tail())