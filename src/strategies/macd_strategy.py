import pandas as pd



class MACDStrategy:
    name = "macd"

    def __init__(
        self,
        fast_period=12,
        slow_period=26,
        signal_period=9,
    ):

        if isinstance(fast_period, bool) or not isinstance(fast_period, int):
            raise TypeError("MACD fast period must be an integer.")

        if fast_period <= 0:
            raise ValueError(
                "MACD fast period must be greater than zero."
        )

        if isinstance(slow_period, bool) or not isinstance(slow_period, int):
            raise TypeError("MACD slow period must be an integer.")

        if slow_period <= 0:
            raise ValueError(
                "MACD slow period must be greater than zero."
        )

        if (
           isinstance(signal_period, bool)
           or not isinstance(signal_period, int)
        ):
            raise TypeError(
                "MACD signal period must be an integer."
        )

        if signal_period <= 0:
            raise ValueError(
                "MACD signal period must be greater than zero."
        )

        if fast_period >= slow_period:
            raise ValueError(
                "MACD fast period must be less than slow period."
        )

        self.fast_period = fast_period
        self.slow_period = slow_period
        self.signal_period = signal_period


    @property
    def required_features(self):
        return [
            {
                "name": "MACD",
                "parameters": {
                  "fast_period": self.fast_period,
                  "slow_period": self.slow_period,
                  "signal_period": self.signal_period,
               },
            },
        ]


    def generate_signals(self, data):
        if not isinstance(data, pd.DataFrame):
            raise TypeError("Input data must be a pandas DataFrame.")

        macd_column = (
            f"MACD_{self.fast_period}_{self.slow_period}"
        )

        signal_column = (
            f"MACD_SIGNAL_"
            f"{self.fast_period}_{self.slow_period}_"
            f"{self.signal_period}"
        )

        required_columns = [
            macd_column,
            signal_column,
        ]

        missing = [
           column
           for column in required_columns
           if column not in data.columns
        ]

        if missing:
           raise ValueError(
               f"Missing required columns: {missing}"
            )

        result = data.copy()
        result["Signal"] = 0

        buy = (
            (result[macd_column] > result[signal_column])
            & (
              result[macd_column].shift(1)
              <= result[signal_column].shift(1)
            )
        )

        sell = (
           (result[macd_column] < result[signal_column])
           & (
             result[macd_column].shift(1)
             >= result[signal_column].shift(1)
            )
        )

        result.loc[buy, "Signal"] = 1
        result.loc[sell, "Signal"] = -1

        return result