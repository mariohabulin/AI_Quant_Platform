import pandas as pd


class SupertrendStrategy:
    """Trend-following strategy based on Supertrend direction changes."""

    name = "supertrend"

    def __init__(self, period=10, multiplier=3.0):
        if isinstance(period, bool) or not isinstance(period, int):
            raise TypeError("Supertrend period must be an integer.")

        if period <= 0:
            raise ValueError("Supertrend period must be greater than zero.")

        if (
            isinstance(multiplier, bool)
            or not isinstance(multiplier, (int, float))
        ):
            raise TypeError("Supertrend multiplier must be a number.")

        if multiplier <= 0:
            raise ValueError(
                "Supertrend multiplier must be greater than zero."
            )

        self.period = period
        self.multiplier = multiplier

    @property
    def required_features(self):
        return [
            {
                "name": "SUPERTREND",
                "parameters": {
                    "period": self.period,
                    "multiplier": self.multiplier,
                },
            },
        ]

    def generate_signals(self, data):
        if not isinstance(data, pd.DataFrame):
            raise TypeError("Input data must be a pandas DataFrame.")

        direction_column = (
            f"SUPERTREND_DIRECTION_{self.period}_{self.multiplier}"
        )
        required_columns = ["Close", direction_column]
        missing = [
            column
            for column in required_columns
            if column not in data.columns
        ]

        if missing:
            raise ValueError(f"Missing required columns: {missing}")

        result = data.copy()
        result["Signal"] = 0

        previous_direction = result[direction_column].shift(1)
        buy = (result[direction_column] == 1) & (previous_direction == -1)
        sell = (result[direction_column] == -1) & (previous_direction == 1)

        result.loc[buy, "Signal"] = 1
        result.loc[sell, "Signal"] = -1

        return result
