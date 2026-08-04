import pandas as pd


class BollingerStrategy:
    name = "bollinger"


    def __init__(
        self,
        period=20,
        standard_deviations=2.0,
    ):
    

        if isinstance(period, bool) or not isinstance(period, int):
            raise TypeError(
                "Bollinger period must be an integer."
            )

        if period <= 0:
            raise ValueError(
                "Bollinger period must be greater than zero."
            )

        if (
           isinstance(standard_deviations, bool)
           or not isinstance(standard_deviations, (int, float))
    ):
            raise TypeError(
                "Bollinger standard deviations must be a number."
            )

        if standard_deviations <= 0:
            raise ValueError(
                "Bollinger standard deviations must be greater than zero."
            )

        self.period = period
        self.standard_deviations = standard_deviations


    @property
    def required_features(self):
        return [
            {
               "name": "BOLLINGER_BANDS",
               "parameters": {
                   "period": self.period,
                   "standard_deviations": self.standard_deviations,
               },
            },
        ]


    def generate_signals(self, data):
        if not isinstance(data, pd.DataFrame):
            raise TypeError("Input data must be a pandas DataFrame.")

        lower_column = (
            f"BOLLINGER_LOWER_"
            f"{self.period}_{self.standard_deviations}"
        )

        upper_column = (
            f"BOLLINGER_UPPER_"
            f"{self.period}_{self.standard_deviations}"
        )

        required_columns = [
            lower_column,
            upper_column,
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

        buy = result["Close"] < result[lower_column]
        sell = result["Close"] > result[upper_column]

        result.loc[buy, "Signal"] = 1
        result.loc[sell, "Signal"] = -1

        return result