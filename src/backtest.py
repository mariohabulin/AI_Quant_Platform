import pandas as pd


class BacktestingEngine:
    """
    Executes a trading strategy through StrategyEngine.

    The engine is long-only and supports realistic execution costs through
    commission, slippage, and bid/ask spread assumptions. All execution-cost
    parameters are expressed as decimal rates (for example 0.001 = 0.10%).

    Zero-cost defaults preserve the behavior of the original backtester.
    """

    SAME_BAR_CLOSE = "same_bar_close"
    NEXT_BAR_OPEN = "next_bar_open"
    EXECUTION_TIMINGS = {SAME_BAR_CLOSE, NEXT_BAR_OPEN}

    def __init__(
        self,
        strategy_engine,
        initial_capital=10000.0,
        commission_rate=0.0,
        slippage_rate=0.0,
        spread_rate=0.0,
        execution_timing=SAME_BAR_CLOSE,
        risk_engine=None,
        risk_stop_column="Stop",
        risk_target_column="Target",
    ):
        self.strategy_engine = strategy_engine
        self.risk_engine = risk_engine
        self.risk_stop_column = risk_stop_column
        self.risk_target_column = risk_target_column

        self.initial_capital = self._validate_positive_number(
            initial_capital,
            "Initial capital",
        )
        self.commission_rate = self._validate_rate(
            commission_rate,
            "Commission rate",
        )
        self.slippage_rate = self._validate_rate(
            slippage_rate,
            "Slippage rate",
        )
        self.spread_rate = self._validate_rate(
            spread_rate,
            "Spread rate",
        )
        self.execution_timing = self._validate_execution_timing(
            execution_timing,
        )

        self._reset_state()

    @staticmethod
    def _validate_positive_number(value, name):
        if not isinstance(value, (int, float)) or isinstance(value, bool):
            raise TypeError(f"{name} must be a number.")

        value = float(value)

        if value <= 0:
            raise ValueError(f"{name} must be greater than zero.")

        return value

    @staticmethod
    def _validate_rate(value, name):
        if not isinstance(value, (int, float)) or isinstance(value, bool):
            raise TypeError(f"{name} must be a number.")

        value = float(value)

        if value < 0:
            raise ValueError(f"{name} cannot be negative.")

        if value >= 1:
            raise ValueError(f"{name} must be less than 1.0.")

        return value

    @classmethod
    def _validate_execution_timing(cls, value):
        if not isinstance(value, str):
            raise TypeError("Execution timing must be a string.")
        value = value.strip()
        if value not in cls.EXECUTION_TIMINGS:
            allowed = ", ".join(sorted(cls.EXECUTION_TIMINGS))
            raise ValueError(f"Execution timing must be one of: {allowed}.")
        return value

    def _reset_state(self):
        self.capital = self.initial_capital
        self.shares = 0.0
        self.position = 0
        self.entry_price = 0.0
        self.entry_market_price = 0.0
        self.entry_commission = 0.0
        self.entry_index = None
        self.entry_signal_index = None
        self.entry_risk_decision = None
        self.trade_history = []
        self.equity_curve = []

    def _calculate_execution_price(self, market_price, side):
        half_spread = self.spread_rate / 2.0

        if side == "buy":
            return market_price * (1.0 + self.slippage_rate + half_spread)

        if side == "sell":
            return market_price * (1.0 - self.slippage_rate - half_spread)

        raise ValueError("Side must be 'buy' or 'sell'.")

    def _calculate_equity(self, price):
        return self.capital + self.shares * price

    def _record_equity(self, price, index):
        self.equity_curve.append(
            {
                "index": index,
                "equity": self._calculate_equity(price),
            }
        )

    def _buy(
        self,
        price,
        index,
        position_size=None,
        risk_decision=None,
        signal_index=None,
    ):
        execution_price = self._calculate_execution_price(price, "buy")

        # All-in sizing is preserved when no Risk Engine is configured.
        affordable_shares = self.capital / (
            execution_price * (1.0 + self.commission_rate)
        )
        self.shares = affordable_shares if position_size is None else min(
            float(position_size), affordable_shares
        )
        self.entry_risk_decision = risk_decision
        entry_notional = self.shares * execution_price
        self.entry_commission = entry_notional * self.commission_rate

        self.capital -= entry_notional + self.entry_commission
        if abs(self.capital) < 1e-12:
            self.capital = 0.0

        self.position = 1
        self.entry_price = execution_price
        self.entry_market_price = float(price)
        self.entry_index = index
        self.entry_signal_index = signal_index

    def _sell(self, price, index, signal_index=None):
        exit_market_price = float(price)
        execution_price = self._calculate_execution_price(
            exit_market_price,
            "sell",
        )

        gross_proceeds = self.shares * execution_price
        exit_commission = gross_proceeds * self.commission_rate
        net_proceeds = gross_proceeds - exit_commission

        gross_profit_loss = self.shares * (
            exit_market_price - self.entry_market_price
        )
        execution_cost = self.shares * (
            (self.entry_price - self.entry_market_price)
            + (exit_market_price - execution_price)
        )
        total_commission = self.entry_commission + exit_commission
        total_costs = execution_cost + total_commission
        profit_loss = gross_profit_loss - total_costs

        self.capital += net_proceeds

        self.trade_history.append(
            {
                "entry_index": self.entry_index,
                "exit_index": index,
                "entry_signal_index": self.entry_signal_index,
                "exit_signal_index": signal_index,
                "execution_timing": self.execution_timing,
                "entry_market_price": self.entry_market_price,
                "exit_market_price": exit_market_price,
                "entry_price": self.entry_price,
                "exit_price": execution_price,
                "shares": self.shares,
                "gross_profit_loss": gross_profit_loss,
                "entry_commission": self.entry_commission,
                "exit_commission": exit_commission,
                "total_commission": total_commission,
                "execution_cost": execution_cost,
                "total_costs": total_costs,
                "profit_loss": profit_loss,
                "risk_status": (
                    self.entry_risk_decision.status
                    if self.entry_risk_decision is not None else None
                ),
                "planned_monetary_risk": (
                    self.entry_risk_decision.monetary_risk
                    if self.entry_risk_decision is not None else None
                ),
                "planned_stop_price": (
                    self.entry_risk_decision.stop_price
                    if self.entry_risk_decision is not None else None
                ),
                "planned_target_price": (
                    self.entry_risk_decision.target_price
                    if self.entry_risk_decision is not None else None
                ),
                "planned_reward_risk_ratio": (
                    self.entry_risk_decision.reward_risk_ratio
                    if self.entry_risk_decision is not None else None
                ),
            }
        )

        self.shares = 0.0
        self.position = 0
        self.entry_price = 0.0
        self.entry_market_price = 0.0
        self.entry_commission = 0.0
        self.entry_index = None
        self.entry_signal_index = None
        self.entry_risk_decision = None

    def _process_signals(self, data):
        if self.execution_timing == self.NEXT_BAR_OPEN:
            self._process_signals_next_bar_open(data)
            return

        for index, row in data.iterrows():
            price = float(row["Close"])
            signal = int(row["Signal"])

            protection = None
            if self.risk_engine is not None:
                protection = self.risk_engine.observe_equity(
                    self._calculate_equity(price), index
                )

            if signal == 1 and self.position == 0:
                if self.risk_engine is None:
                    self._buy(price, index, signal_index=index)
                elif protection.status != "REJECT":
                    if self.risk_stop_column not in data.columns:
                        raise ValueError(
                            f"Risk-managed backtest requires '{self.risk_stop_column}' column."
                        )
                    stop_price = float(row[self.risk_stop_column])
                    target_price = None
                    if self.risk_engine.min_reward_risk is not None:
                        if self.risk_target_column not in data.columns:
                            raise ValueError(
                                f"Reward/risk policy requires '{self.risk_target_column}' column."
                            )
                        target_price = float(row[self.risk_target_column])
                    elif self.risk_target_column in data.columns:
                        target_price = float(row[self.risk_target_column])

                    decision = self.risk_engine.assess_long(
                        equity=self._calculate_equity(price),
                        entry_price=price,
                        stop_price=stop_price,
                        target_price=target_price,
                    )
                    if decision.status != "REJECT":
                        self._buy(
                            price, index,
                            position_size=decision.position_size,
                            risk_decision=decision,
                            signal_index=index,
                        )

            elif signal == -1 and self.position == 1:
                self._sell(price, index, signal_index=index)

            self._record_equity(price, index)

    @staticmethod
    def _validate_next_bar_open_data(data):
        if "Open" not in data.columns:
            raise ValueError(
                "Next-bar-open execution requires an 'Open' column."
            )
        open_prices = pd.to_numeric(data["Open"], errors="coerce")
        if open_prices.isna().any() or (open_prices <= 0.0).any():
            raise ValueError(
                "Next-bar-open execution requires positive numeric Open prices."
            )

    def _process_signals_next_bar_open(self, data):
        self._validate_next_bar_open_data(data)
        pending = None

        for index, row in data.iterrows():
            open_price = float(row["Open"])
            close_price = float(row["Close"])
            protection = None
            if self.risk_engine is not None:
                protection = self.risk_engine.observe_equity(
                    self._calculate_equity(open_price), index
                )

            if pending is not None:
                signal, signal_index, signal_row = pending
                if signal == 1 and self.position == 0:
                    if self.risk_engine is None:
                        self._buy(
                            open_price,
                            index,
                            signal_index=signal_index,
                        )
                    elif protection.status != "REJECT":
                        if self.risk_stop_column not in signal_row.index:
                            raise ValueError(
                                f"Risk-managed backtest requires '{self.risk_stop_column}' column."
                            )
                        stop_price = float(signal_row[self.risk_stop_column])
                        target_price = None
                        if self.risk_engine.min_reward_risk is not None:
                            if self.risk_target_column not in signal_row.index:
                                raise ValueError(
                                    f"Reward/risk policy requires '{self.risk_target_column}' column."
                                )
                            target_price = float(signal_row[self.risk_target_column])
                        elif self.risk_target_column in signal_row.index:
                            target_price = float(signal_row[self.risk_target_column])

                        decision = self.risk_engine.assess_long(
                            equity=self._calculate_equity(open_price),
                            entry_price=open_price,
                            stop_price=stop_price,
                            target_price=target_price,
                        )
                        if decision.status != "REJECT":
                            self._buy(
                                open_price,
                                index,
                                position_size=decision.position_size,
                                risk_decision=decision,
                                signal_index=signal_index,
                            )
                elif signal == -1 and self.position == 1:
                    self._sell(
                        open_price,
                        index,
                        signal_index=signal_index,
                    )

            self._record_equity(close_price, index)
            pending = (int(row["Signal"]), index, row.copy())

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
        if self.risk_engine is not None:
            self.risk_engine.reset_protection_state()

        result = self.strategy_engine.run(data)

        self._process_signals(result)
        self._close_open_position(result)

        return result
