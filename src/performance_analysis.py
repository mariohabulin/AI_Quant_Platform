import statistics




class PerformanceAnalyzer:

    """
    Calculates performance metrics from completed backtest results.

    The analyzer receives Trade History, Equity Curve,
    and the initial portfolio capital.

    It does not execute trades and does not generate signals.
    """

    def __init__(self, initial_capital):
        if not isinstance(initial_capital, (int, float)):
            raise TypeError("Initial capital must be a number.")

        if initial_capital <= 0:
            raise ValueError("Initial capital must be greater than zero.")

        self.initial_capital = float(initial_capital)

    def _calculate_total_return(self, equity_curve):
        if not equity_curve:
            return 0.0

        final_equity = equity_curve[-1]["equity"]

        return (
            (final_equity - self.initial_capital)
            / self.initial_capital
        ) * 100

    def _calculate_number_of_trades(self, trade_history):
        return len(trade_history)

    def _calculate_winning_trades(self, trade_history):
        return sum(
            1
            for trade in trade_history
            if trade["profit_loss"] > 0
        )

    def _calculate_losing_trades(self, trade_history):
        return sum(
            1
            for trade in trade_history
            if trade["profit_loss"] < 0
        )

    def _calculate_win_rate(self, trade_history):
        number_of_trades = self._calculate_number_of_trades(
            trade_history
        )

        if number_of_trades == 0:
            return 0.0

        winning_trades = self._calculate_winning_trades(
            trade_history
        )

        return (
            winning_trades
            / number_of_trades
        ) * 100

    def _calculate_average_win(self, trade_history):
        winning_profit_losses = [
            trade["profit_loss"]
            for trade in trade_history
            if trade["profit_loss"] > 0
        ]

        if not winning_profit_losses:
            return 0.0

        return (
            sum(winning_profit_losses)
            / len(winning_profit_losses)
        )

    def _calculate_average_loss(self, trade_history):
        losing_profit_losses = [
            trade["profit_loss"]
            for trade in trade_history
            if trade["profit_loss"] < 0
        ]

        if not losing_profit_losses:
            return 0.0

        return (
            sum(losing_profit_losses)
            / len(losing_profit_losses)
        )

    def _calculate_profit_factor(self, trade_history):
        total_wins = sum(
            trade["profit_loss"]
            for trade in trade_history
            if trade["profit_loss"] > 0
        )

        total_losses = abs(
            sum(
                trade["profit_loss"]
                for trade in trade_history
                if trade["profit_loss"] < 0
            )
        )

        if total_wins == 0 and total_losses == 0:
            return 0.0
  
        if total_losses == 0:
            return float("inf")

        return total_wins / total_losses

    def _calculate_max_drawdown(self, equity_curve):
        if not equity_curve:
            return 0.0

        peak_equity = equity_curve[0]["equity"]
        max_drawdown = 0.0

        for equity_point in equity_curve:
            current_equity = equity_point["equity"]

            if current_equity > peak_equity:
                peak_equity = current_equity

            drawdown = (
               (peak_equity - current_equity)
               / peak_equity
            ) * 100

            if drawdown > max_drawdown:
               max_drawdown = drawdown

        return max_drawdown

    def _calculate_expectancy(self, trade_history):
        number_of_trades = self._calculate_number_of_trades(
            trade_history
        )

        if number_of_trades == 0:
            return 0.0

        winning_trades = self._calculate_winning_trades(
            trade_history
        )
        losing_trades = self._calculate_losing_trades(
            trade_history
        )

        average_win = self._calculate_average_win(
            trade_history
        )
        average_loss = self._calculate_average_loss(
            trade_history
        )

        win_probability = winning_trades / number_of_trades
        loss_probability = losing_trades / number_of_trades

        return (
             win_probability * average_win
             + loss_probability * average_loss
        )

    def _calculate_sharpe_ratio(self, equity_curve):
        if len(equity_curve) < 3:
            return 0.0

        returns = []

        for index in range(1, len(equity_curve)):
            previous_equity = equity_curve[index - 1]["equity"]
            current_equity = equity_curve[index]["equity"]

            period_return = (
                current_equity - previous_equity
            ) / previous_equity

            returns.append(period_return)

        return_volatility = statistics.stdev(returns)

        if return_volatility == 0:
            return 0.0

        average_return = statistics.mean(returns)

        return average_return / return_volatility

    
         

    def calculate(self, trade_history, equity_curve):
        """
        Calculate backtest performance metrics.

        Parameters
        ----------
        trade_history : list
            Completed trades generated by BacktestingEngine.

        equity_curve : list
            Portfolio equity records generated during the backtest.

        Returns
        -------
        dict
            Calculated performance metrics.
        """
        if not isinstance(trade_history, list):
            raise TypeError("Trade history must be a list.")

        if not isinstance(equity_curve, list):
            raise TypeError("Equity curve must be a list.")

        return {
            "total_return": self._calculate_total_return(equity_curve),
            "number_of_trades": self._calculate_number_of_trades(
               trade_history
            ),
            "winning_trades": self._calculate_winning_trades(
               trade_history
            ),
            "losing_trades": self._calculate_losing_trades(
               trade_history
            ),
           "win_rate": self._calculate_win_rate(
               trade_history
            ),
            "average_win": self._calculate_average_win(
               trade_history
            ),
            "average_loss": self._calculate_average_loss(
               trade_history
            ),
            "profit_factor": self._calculate_profit_factor(
               trade_history
            ),
            "max_drawdown": self._calculate_max_drawdown(
               equity_curve
            ),
            "expectancy": self._calculate_expectancy(
               trade_history
            ),
            "sharpe_ratio": self._calculate_sharpe_ratio(
               equity_curve
            ),
        }

       