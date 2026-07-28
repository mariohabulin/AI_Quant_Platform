import pandas as pd

from feature_engine import generate_features


class StrategyEngine:
    
    """
    Coordinates feature generation and strategy execution.

    The Strategy Engine does not decide which strategy to use.
    It executes the strategy provided during initialization.
    """

    def __init__(self, strategy_library, strategy_name):
        strategy = strategy_library.get(strategy_name)

        self._validate_strategy(strategy)

        self.strategy = strategy

    @property
    def strategy_name(self):
        return self.strategy.name

    def run(self, data):
        """
        Generate features and execute the selected strategy.

        Parameters
        ----------
        data : pandas.DataFrame
            Raw OHLCV market data.

        Returns
        -------
        pandas.DataFrame
            Market data containing generated features and Signal column.
        """
        self._validate_data(data)

        featured_data = generate_features(data)

        result = self.strategy.generate_signals(featured_data)

        self._validate_result(result)

        return result

    @staticmethod
    def _validate_strategy(strategy):
        if strategy is None:
            raise ValueError("Strategy cannot be None.")

        if not hasattr(strategy, "name"):
            raise TypeError("Strategy must contain a 'name' attribute.")

        if not callable(getattr(strategy, "generate_signals", None)):
            raise TypeError(
                "Strategy must contain a callable 'generate_signals' method."
            )

    @staticmethod

    def _validate_data(data):
        if not isinstance(data, pd.DataFrame):
            raise TypeError("Input data must be a pandas DataFrame.")

        if data.empty:
            raise ValueError("Input DataFrame cannot be empty.")

    @staticmethod
    def _validate_result(result):
        if not isinstance(result, pd.DataFrame):
            raise TypeError("Strategy result must be a pandas DataFrame.")

        if "Signal" not in result.columns:
            raise ValueError(
                "Strategy result must contain a 'Signal' column."
            )

        valid_signals = {-1, 0, 1}
        actual_signals = set(result["Signal"].dropna().unique())

        if not actual_signals.issubset(valid_signals):
            raise ValueError(
                "Signal column may only contain -1, 0, or 1."
            )


if __name__ == "__main__":
    from strategies.ema_strategy import EMAStrategy

    data = pd.read_csv("data/AAPL.csv", index_col=0)

    strategy = EMAStrategy()
    engine = StrategyEngine(strategy)

    result = engine.run(data)

    print(f"Strategy: {engine.strategy_name}")
    print(result[["Close", "EMA_20", "EMA_50", "Signal"]].tail())
    print(result["Signal"].value_counts())