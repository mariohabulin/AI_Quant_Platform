import pandas as pd


class RSIStrategy:
    name = "rsi"

    def __init__(
        self,
        period=14,
        oversold=30,
        overbought=70,
    ):
        if isinstance(period, bool) or not isinstance(period, int):
            raise TypeError("RSI period must be an integer.")

        if period <= 0:
            raise ValueError("RSI period must be greater than zero.")

        if (
            isinstance(oversold, bool)
            or not isinstance(oversold, (int, float))
        ):
            raise TypeError(
                "RSI oversold threshold must be a number."
            )

        if not 0 < oversold < 100:
            raise ValueError(
                "RSI oversold threshold must be between 0 and 100."
            )

        if (
            isinstance(overbought, bool)
            or not isinstance(overbought, (int, float))
        ):
            raise TypeError(
                "RSI overbought threshold must be a number."
            )

        if not 0 < overbought < 100:
            raise ValueError(
                "RSI overbought threshold must be between 0 and 100."
            )

        if oversold >= overbought:
            raise ValueError(
                "RSI oversold threshold must be less than "
                "overbought threshold."
            )

        self.period = period
        self.oversold = oversold
        self.overbought = overbought

    @property
    def required_features(self):
        return [
            {
                "name": "RSI",
                "parameters": {
                    "period": self.period,
                },
            },
        ]

    def generate_signals(self, data):
        if not isinstance(data, pd.DataFrame):
            raise TypeError("Input data must be a pandas DataFrame.")

        rsi_column = f"RSI_{self.period}"

        if rsi_column not in data.columns:
            raise ValueError(
                f"Missing required columns: ['{rsi_column}']"
            )

        result = data.copy()
        result["Signal"] = 0

        buy = result[rsi_column] < self.oversold
        sell = result[rsi_column] > self.overbought

        result.loc[buy, "Signal"] = 1
        result.loc[sell, "Signal"] = -1

        return result