import pandas as pd


class EMAStrategy:
    """
    EMA Crossover trading strategy.

    Generates BUY and SELL signals using precomputed EMA features.

    BUY  -> EMA_20 crosses above EMA_50
    SELL -> EMA_20 crosses below EMA_50
    """

    name = "ema_crossover"

    def __init__(self, fast_period=20, slow_period=50):
        if not isinstance(fast_period, int):
            raise TypeError("Fast period must be an integer.")

        if not isinstance(slow_period, int):
            raise TypeError("Slow period must be an integer.")

        if fast_period <= 0:
            raise ValueError("Fast period must be greater than zero.")

        if slow_period <= 0:
            raise ValueError("Slow period must be greater than zero.")

        if fast_period >= slow_period:
            raise ValueError( "Fast period must be less than slow period.")
         
    

        self.fast_period = fast_period
        self.slow_period = slow_period

    @property
    def required_features(self):
        return [
           {
                "name": "EMA",
                "parameters": {
                "period": self.fast_period,
               },
           },
           {
                "name": "EMA",
                "parameters": {
                "period": self.slow_period,
              },
           },
        ]

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

        fast_column = f"EMA_{self.fast_period}"
        slow_column = f"EMA_{self.slow_period}"

        buy = (
            (df[fast_column] > df[slow_column])
            & (df[fast_column].shift(1) <= df[slow_column].shift(1))
        )

        sell = (
            (df[fast_column] < df[slow_column])
            & (df[fast_column].shift(1) >= df[slow_column].shift(1))
        ) 

        df.loc[buy, "Signal"] = 1
        df.loc[sell, "Signal"] = -1

        return df

    
    def _validate_input(self, df):
        if not isinstance(df, pd.DataFrame):
            raise TypeError("Input data must be a pandas DataFrame.")

        fast_column = f"EMA_{self.fast_period}"
        slow_column = f"EMA_{self.slow_period}"

        required_columns = [
            fast_column,
            slow_column,
        ]

        missing = [
            col for col in required_columns
        if col not in df.columns
        ]

        if missing:
           raise ValueError(
               f"Missing required columns: {missing}"
           )