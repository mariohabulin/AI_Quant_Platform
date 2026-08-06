import pandas as pd


class ADXStrategy:
    """Trend-strength strategy based on ADX and directional movement."""

    name = "adx"

    def __init__(self, period=14, threshold=25.0):
        if isinstance(period, bool) or not isinstance(period, int):
            raise TypeError("ADX period must be an integer.")
        if period <= 0:
            raise ValueError("ADX period must be greater than zero.")
        if isinstance(threshold, bool) or not isinstance(threshold, (int, float)):
            raise TypeError("ADX threshold must be a number.")
        if threshold <= 0 or threshold > 100:
            raise ValueError("ADX threshold must be greater than zero and at most 100.")
        self.period = period
        self.threshold = threshold

    @property
    def required_features(self):
        return [{
            "name": "ADX",
            "parameters": {"period": self.period},
        }]

    def generate_signals(self, data):
        if not isinstance(data, pd.DataFrame):
            raise TypeError("Input data must be a pandas DataFrame.")

        adx_column = f"ADX_{self.period}"
        plus_di_column = f"PLUS_DI_{self.period}"
        minus_di_column = f"MINUS_DI_{self.period}"
        required_columns = ["Close", adx_column, plus_di_column, minus_di_column]
        missing = [column for column in required_columns if column not in data.columns]
        if missing:
            raise ValueError(f"Missing required columns: {missing}")

        result = data.copy()
        result["Signal"] = 0

        bullish = (result[adx_column] >= self.threshold) & (result[plus_di_column] > result[minus_di_column])
        bearish = (result[adx_column] >= self.threshold) & (result[minus_di_column] > result[plus_di_column])
        previous_bullish = bullish.shift(1, fill_value=False)
        previous_bearish = bearish.shift(1, fill_value=False)

        result.loc[bullish & ~previous_bullish, "Signal"] = 1
        result.loc[bearish & ~previous_bearish, "Signal"] = -1
        return result
