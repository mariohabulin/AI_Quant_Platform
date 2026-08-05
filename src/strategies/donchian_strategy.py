import pandas as pd




class DonchianStrategy:
    name = "donchian"

    def __init__(
        self,
        period=20,
    ):

        if isinstance(period, bool) or not isinstance(period, int):
            raise TypeError(
                "Donchian period must be an integer."
            )

        if period <= 0:
            raise ValueError(
                "Donchian period must be greater than zero."
            )
        self.period = period


    @property
    def required_features(self):
        return [
            {
                "name": "DONCHIAN_CHANNELS",
                "parameters": {
                    "period": self.period,
               },
            },
        ]


    def generate_signals(self, data):
        if not isinstance(data, pd.DataFrame):
            raise TypeError("Input data must be a pandas DataFrame.")

        upper_column = f"DONCHIAN_UPPER_{self.period}"
        lower_column = f"DONCHIAN_LOWER_{self.period}"

        required_columns = [
            upper_column,
            lower_column,
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

        buy = result["Close"] > result[upper_column]
        sell = result["Close"] < result[lower_column]

        result.loc[buy, "Signal"] = 1
        result.loc[sell, "Signal"] = -1

        return result


      