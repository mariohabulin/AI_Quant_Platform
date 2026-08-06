import pandas as pd


class ATRStrategy:
    """Volatility breakout strategy based on Average True Range."""

    name = "atr"

    def __init__(self, period=14, multiplier=1.0):
        if isinstance(period, bool) or not isinstance(period, int):
            raise TypeError("ATR period must be an integer.")

        if period <= 0:
            raise ValueError("ATR period must be greater than zero.")

        if (
            isinstance(multiplier, bool)
            or not isinstance(multiplier, (int, float))
        ):
            raise TypeError("ATR multiplier must be a number.")

        if multiplier <= 0:
            raise ValueError(
                "ATR multiplier must be greater than zero."
            )

        self.period = period
        self.multiplier = multiplier

    @property
    def required_features(self):
        return [
            {
                "name": "ATR",
                "parameters": {
                    "period": self.period,
                },
            },
        ]

    def generate_signals(self, data):
        if not isinstance(data, pd.DataFrame):
            raise TypeError("Input data must be a pandas DataFrame.")

        atr_column = f"ATR_{self.period}"
        required_columns = ["Close", atr_column]
        missing = [
            column
            for column in required_columns
            if column not in data.columns
        ]

        if missing:
            raise ValueError(f"Missing required columns: {missing}")

        result = data.copy()
        result["Signal"] = 0

        previous_close = result["Close"].shift(1)
        previous_atr = result[atr_column].shift(1)
        breakout_distance = previous_atr * self.multiplier

        buy = result["Close"] > (previous_close + breakout_distance)
        sell = result["Close"] < (previous_close - breakout_distance)

        result.loc[buy, "Signal"] = 1
        result.loc[sell, "Signal"] = -1

        return result
