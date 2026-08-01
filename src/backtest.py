import pandas as pd


class BacktestingEngine:
    """
    Executes a trading strategy through StrategyEngine.

    This first version only connects the Backtesting Engine
    with the existing strategy execution pipeline.
    """

    def __init__(self, strategy_engine, initial_capital=10000.0):
        self.strategy_engine = strategy_engine

        self.initial_capital = initial_capital
        self.capital = initial_capital
        self.shares = 0.0
        self.position = 0
        self.entry_price = 0.0
        self.entry_index = None
        self.trade_history = []
        self.equity_curve = []

    def _reset_state(self):
        self.capital = self.initial_capital
        self.shares = 0.0
        self.position = 0
        self.entry_price = 0.0
        self.entry_index = None
        self.trade_history = []
        self.equity_curve = []

    def _calculate_equity(self, price):
        return self.capital + self.shares * price

    def _record_equity(self, price, index):
        self.equity_curve.append(
        {
            "index": index,
            "equity": self._calculate_equity(price),
        }
    )

    def _buy(self, price, index):
        self.shares = self.capital / price
        self.capital = 0.0
        self.position = 1
        self.entry_price = price
        self.entry_index = index

    def _sell(self, price, index):
        profit_loss = self.shares * (price - self.entry_price)

        self.capital = self.shares * price

        self.trade_history.append(
        {
            "entry_index": self.entry_index,
            "exit_index": index,
            "entry_price": self.entry_price,
            "exit_price": price,
            "profit_loss": profit_loss,
        }
    )

        self.shares = 0.0
        self.position = 0
        self.entry_price = 0.0
        self.entry_index = None
        

    def _process_signals(self, data):
       for index, row in data.iterrows():
        price = float(row["Close"])
        signal = int(row["Signal"])

        if signal == 1 and self.position == 0:
            self._buy(price, index)

        elif signal == -1 and self.position == 1:
            self._sell(price, index)

        self._record_equity(price, index)

    def _close_open_position(self, data):
        if self.position == 1:
            final_index = data.index[-1]
            final_price = float(data.iloc[-1]["Close"])

            self._sell(final_price, final_index)

    def run(self, data):
        """
        Execute the selected strategy on market data.

        Parameters
        ----------
        data : pandas.DataFrame
            Raw OHLCV market data.

        Returns
        -------
        pandas.DataFrame
            Market data containing generated features and Signal column.
        """
        if not isinstance(data, pd.DataFrame):
            raise TypeError("Input data must be a pandas DataFrame.")

        if data.empty:
            raise ValueError("Input DataFrame cannot be empty.")

        self._reset_state()

        result = self.strategy_engine.run(data)

        self._process_signals(result)
        self._close_open_position(result)

        return result