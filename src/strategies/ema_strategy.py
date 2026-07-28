import pandas as pd


class EMAStrategy:
    """
    EMA Crossover trading strategy.

    Generates BUY and SELL signals using precomputed EMA features.

    BUY  -> EMA_20 crosses above EMA_50
    SELL -> EMA_20 crosses below EMA_50
    """

    name = "ema_crossover"

    def generate_signals(self, df):
        """
        Generate trading signals.

        Parameters
        ----------
        df : pandas.DataFrame
            DataFrame containing EMA_20 and EMA_50 columns.

        Returns
        -------
        pandas.DataFrame
            DataFrame containing the Signal column.
        """

        self._validate_input(df)

        df = df.copy()

        df["Signal"] = 0

        buy = (
            (df["EMA_20"] > df["EMA_50"])
            & (df["EMA_20"].shift(1) <= df["EMA_50"].shift(1))
        )

        sell = (
            (df["EMA_20"] < df["EMA_50"])
            & (df["EMA_20"].shift(1) >= df["EMA_50"].shift(1))
        )

        df.loc[buy, "Signal"] = 1
        df.loc[sell, "Signal"] = -1

        return df

    @staticmethod
    def _validate_input(df):
        if not isinstance(df, pd.DataFrame):
            raise TypeError("Input data must be a pandas DataFrame.")

        required_columns = [
            "Close",
            "EMA_20",
            "EMA_50"
        ]

        missing = [col for col in required_columns if col not in df.columns]

        if missing:
         raise ValueError(
        f"Missing required columns: {missing}"
    )


if __name__ == "__main__":
    df = pd.read_csv("data/AAPL.csv", index_col=0)

    strategy = EMAStrategy()

    result = strategy.generate_signals(df)

    print(result[["Close", "EMA_20", "EMA_50", "Signal"]].tail())
    print(result["Signal"].value_counts())
         