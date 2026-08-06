import pandas as pd


class StochasticStrategy:
    """Momentum-reversal strategy based on Stochastic %K/%D crossovers."""

    name = "stochastic"

    def __init__(
        self,
        k_period=14,
        d_period=3,
        oversold=20.0,
        overbought=80.0,
    ):
        if isinstance(k_period, bool) or not isinstance(k_period, int):
            raise TypeError("Stochastic %K period must be an integer.")
        if k_period <= 0:
            raise ValueError(
                "Stochastic %K period must be greater than zero."
            )

        if isinstance(d_period, bool) or not isinstance(d_period, int):
            raise TypeError("Stochastic %D period must be an integer.")
        if d_period <= 0:
            raise ValueError(
                "Stochastic %D period must be greater than zero."
            )

        if (
            isinstance(oversold, bool)
            or not isinstance(oversold, (int, float))
        ):
            raise TypeError(
                "Stochastic oversold threshold must be a number."
            )
        if not 0 <= oversold < 100:
            raise ValueError(
                "Stochastic oversold threshold must be between 0 and 100."
            )

        if (
            isinstance(overbought, bool)
            or not isinstance(overbought, (int, float))
        ):
            raise TypeError(
                "Stochastic overbought threshold must be a number."
            )
        if not 0 < overbought <= 100:
            raise ValueError(
                "Stochastic overbought threshold must be between 0 and 100."
            )

        if oversold >= overbought:
            raise ValueError(
                "Stochastic oversold threshold must be less than "
                "overbought threshold."
            )

        self.k_period = k_period
        self.d_period = d_period
        self.oversold = oversold
        self.overbought = overbought

    @property
    def required_features(self):
        return [{
            "name": "STOCHASTIC",
            "parameters": {
                "k_period": self.k_period,
                "d_period": self.d_period,
            },
        }]

    def generate_signals(self, data):
        if not isinstance(data, pd.DataFrame):
            raise TypeError("Input data must be a pandas DataFrame.")

        k_column = f"STOCHASTIC_K_{self.k_period}"
        d_column = f"STOCHASTIC_D_{self.k_period}_{self.d_period}"
        missing = [
            column
            for column in [k_column, d_column]
            if column not in data.columns
        ]
        if missing:
            raise ValueError(f"Missing required columns: {missing}")

        result = data.copy()
        result["Signal"] = 0

        previous_k = result[k_column].shift(1)
        previous_d = result[d_column].shift(1)
        bullish_cross = (
            (previous_k <= previous_d)
            & (result[k_column] > result[d_column])
            & (previous_k <= self.oversold)
            & (previous_d <= self.oversold)
        )
        bearish_cross = (
            (previous_k >= previous_d)
            & (result[k_column] < result[d_column])
            & (previous_k >= self.overbought)
            & (previous_d >= self.overbought)
        )

        result.loc[bullish_cross, "Signal"] = 1
        result.loc[bearish_cross, "Signal"] = -1
        return result
