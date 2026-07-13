import yfinance as yf
import pandas as pd
from pathlib import Path


DATA_DIR = Path("data")


def download_data(ticker: str, period: str = "1y") -> pd.DataFrame:
    """
    Download historical market data from Yahoo Finance
    and save it as a CSV file.
    """

    DATA_DIR.mkdir(exist_ok=True)

    print(f"Downloading {ticker}...")

    data = yf.download(ticker, period=period)
    # Technical Indicators
    data["SMA20"] = data["Close"].rolling(window=20).mean()
    data["SMA50"] = data["Close"].rolling(window=50).mean()

# Daily Returns
    data["Returns"] = data["Close"].pct_change()

# Volatility
    data["Volatility"] = data["Returns"].rolling(window=20).std()

    if data.empty:
        raise ValueError(f"No data found for {ticker}")

    file_path = DATA_DIR / f"{ticker}.csv"
    data.to_csv(file_path)

    print(f"Saved to {file_path}")

    return data


if __name__ == "__main__":
    df = download_data("AAPL")
    print(df.tail())