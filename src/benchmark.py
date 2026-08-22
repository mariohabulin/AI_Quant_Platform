import pandas as pd


class BuyAndHoldBenchmark:
    """Deterministic long-only buy-and-hold benchmark with execution costs."""

    def __init__(
        self,
        initial_capital=10000.0,
        commission_rate=0.0,
        slippage_rate=0.0,
        spread_rate=0.0,
        entry_price_column="Close",
    ):
        self.initial_capital = self._validate_positive_number(initial_capital, "Initial capital")
        self.commission_rate = self._validate_rate(commission_rate, "Commission rate")
        self.slippage_rate = self._validate_rate(slippage_rate, "Slippage rate")
        self.spread_rate = self._validate_rate(spread_rate, "Spread rate")
        if not isinstance(entry_price_column, str):
            raise TypeError("Benchmark entry price column must be a string.")
        entry_price_column = entry_price_column.strip()
        if entry_price_column not in {"Open", "Close"}:
            raise ValueError("Benchmark entry price column must be Open or Close.")
        self.entry_price_column = entry_price_column

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

    def _execution_price(self, market_price, side):
        half_spread = self.spread_rate / 2.0
        if side == "buy":
            return market_price * (1.0 + self.slippage_rate + half_spread)
        if side == "sell":
            return market_price * (1.0 - self.slippage_rate - half_spread)
        raise ValueError("Side must be 'buy' or 'sell'.")

    def run(self, data):
        if not isinstance(data, pd.DataFrame):
            raise TypeError("Input data must be a pandas DataFrame.")
        if data.empty:
            raise ValueError("Input DataFrame cannot be empty.")
        required = {"Close", self.entry_price_column}
        missing = sorted(required - set(data.columns))
        if missing:
            raise ValueError(
                f"Input DataFrame is missing required price columns: {missing}."
            )

        close = pd.to_numeric(data["Close"], errors="coerce")
        if close.isna().any() or (close <= 0).any():
            raise ValueError("Close prices must be positive numeric values.")
        entry = pd.to_numeric(data[self.entry_price_column], errors="coerce")
        if entry.isna().any() or (entry <= 0).any():
            raise ValueError(
                f"{self.entry_price_column} prices must be positive numeric values."
            )

        entry_market_price = float(entry.iloc[0])
        exit_market_price = float(close.iloc[-1])
        entry_price = self._execution_price(entry_market_price, "buy")
        exit_price = self._execution_price(exit_market_price, "sell")

        shares = self.initial_capital / (entry_price * (1.0 + self.commission_rate))
        entry_notional = shares * entry_price
        entry_commission = entry_notional * self.commission_rate
        exit_notional = shares * exit_price
        exit_commission = exit_notional * self.commission_rate
        final_capital = exit_notional - exit_commission

        gross_profit_loss = shares * (exit_market_price - entry_market_price)
        execution_cost = shares * (
            (entry_price - entry_market_price)
            + (exit_market_price - exit_price)
        )
        total_commission = entry_commission + exit_commission
        total_costs = execution_cost + total_commission
        net_profit_loss = final_capital - self.initial_capital
        total_return = net_profit_loss / self.initial_capital

        return {
            "benchmark": "buy_and_hold",
            "entry_price_column": self.entry_price_column,
            "initial_capital": self.initial_capital,
            "final_capital": final_capital,
            "total_return": total_return,
            "entry_index": data.index[0],
            "exit_index": data.index[-1],
            "entry_market_price": entry_market_price,
            "exit_market_price": exit_market_price,
            "entry_price": entry_price,
            "exit_price": exit_price,
            "shares": shares,
            "gross_profit_loss": gross_profit_loss,
            "entry_commission": entry_commission,
            "exit_commission": exit_commission,
            "total_commission": total_commission,
            "execution_cost": execution_cost,
            "total_costs": total_costs,
            "net_profit_loss": net_profit_loss,
        }


def compare_strategy_to_benchmark(strategy_final_capital, benchmark_result):
    """Return strategy, benchmark and excess returns on the same capital base."""
    if not isinstance(strategy_final_capital, (int, float)) or isinstance(strategy_final_capital, bool):
        raise TypeError("Strategy final capital must be a number.")
    if not isinstance(benchmark_result, dict):
        raise TypeError("Benchmark result must be a dictionary.")
    if "initial_capital" not in benchmark_result or "total_return" not in benchmark_result:
        raise ValueError("Benchmark result is missing required fields.")

    initial_capital = float(benchmark_result["initial_capital"])
    strategy_return = (float(strategy_final_capital) - initial_capital) / initial_capital
    benchmark_return = float(benchmark_result["total_return"])

    return {
        "strategy_return": strategy_return,
        "benchmark_return": benchmark_return,
        "excess_return": strategy_return - benchmark_return,
    }
