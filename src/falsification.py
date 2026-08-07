import math
import random
import statistics


class StatisticalFalsificationEngine:
    """Deterministic statistical stress tests for completed trade histories.

    The engine never changes strategy logic. It consumes realized net trade P&L
    and asks whether the observed edge is stable under resampling and plausible
    null models. All stochastic methods accept an explicit seed.
    """

    def __init__(self, simulations=1000, confidence_level=0.95, random_seed=42):
        if not isinstance(simulations, int) or isinstance(simulations, bool):
            raise TypeError("Simulations must be an integer.")
        if simulations <= 0:
            raise ValueError("Simulations must be greater than zero.")
        if not isinstance(confidence_level, (int, float)) or isinstance(confidence_level, bool):
            raise TypeError("Confidence level must be a number.")
        if not 0 < float(confidence_level) < 1:
            raise ValueError("Confidence level must be between 0 and 1.")
        if random_seed is not None and (not isinstance(random_seed, int) or isinstance(random_seed, bool)):
            raise TypeError("Random seed must be an integer or None.")

        self.simulations = simulations
        self.confidence_level = float(confidence_level)
        self.random_seed = random_seed

    @staticmethod
    def _profit_losses(trade_history):
        if not isinstance(trade_history, list):
            raise TypeError("Trade history must be a list.")
        if not trade_history:
            raise ValueError("Trade history cannot be empty.")

        values = []
        for trade in trade_history:
            if not isinstance(trade, dict):
                raise TypeError("Every trade must be a dictionary.")
            if "profit_loss" not in trade:
                raise ValueError("Every trade must contain profit_loss.")
            value = trade["profit_loss"]
            if not isinstance(value, (int, float)) or isinstance(value, bool):
                raise TypeError("profit_loss must be a number.")
            value = float(value)
            if not math.isfinite(value):
                raise ValueError("profit_loss must be finite.")
            values.append(value)
        return values

    @staticmethod
    def _percentile(values, probability):
        ordered = sorted(values)
        if len(ordered) == 1:
            return ordered[0]
        position = probability * (len(ordered) - 1)
        lower = math.floor(position)
        upper = math.ceil(position)
        if lower == upper:
            return ordered[lower]
        weight = position - lower
        return ordered[lower] * (1 - weight) + ordered[upper] * weight

    @staticmethod
    def _max_drawdown_from_pnl(sequence):
        equity = 0.0
        peak = 0.0
        max_drawdown = 0.0
        for pnl in sequence:
            equity += pnl
            peak = max(peak, equity)
            max_drawdown = max(max_drawdown, peak - equity)
        return max_drawdown

    def bootstrap_expectancy(self, trade_history):
        """Bootstrap mean net trade P&L and return a confidence interval."""
        pnl = self._profit_losses(trade_history)
        rng = random.Random(self.random_seed)
        means = []
        for _ in range(self.simulations):
            sample = [rng.choice(pnl) for _ in pnl]
            means.append(statistics.mean(sample))

        alpha = 1.0 - self.confidence_level
        lower = self._percentile(means, alpha / 2.0)
        upper = self._percentile(means, 1.0 - alpha / 2.0)
        observed = statistics.mean(pnl)
        return {
            "observed_expectancy": observed,
            "confidence_level": self.confidence_level,
            "ci_lower": lower,
            "ci_upper": upper,
            "positive_edge_supported": lower > 0.0,
        }

    def monte_carlo_drawdown(self, trade_history):
        """Shuffle trade order to stress path-dependent P&L drawdown."""
        pnl = self._profit_losses(trade_history)
        rng = random.Random(self.random_seed)
        drawdowns = []
        for _ in range(self.simulations):
            path = pnl.copy()
            rng.shuffle(path)
            drawdowns.append(self._max_drawdown_from_pnl(path))

        return {
            "observed_max_drawdown": self._max_drawdown_from_pnl(pnl),
            "median_max_drawdown": self._percentile(drawdowns, 0.5),
            "drawdown_95th_percentile": self._percentile(drawdowns, 0.95),
            "worst_simulated_drawdown": max(drawdowns),
        }

    def permutation_test(self, trade_history):
        """Sign-flip randomization test for the null hypothesis of zero edge."""
        pnl = self._profit_losses(trade_history)
        observed = statistics.mean(pnl)
        rng = random.Random(self.random_seed)
        null_means = []
        for _ in range(self.simulations):
            randomized = [value if rng.random() < 0.5 else -value for value in pnl]
            null_means.append(statistics.mean(randomized))

        extreme = sum(value >= observed for value in null_means)
        p_value = (extreme + 1) / (self.simulations + 1)
        return {
            "observed_expectancy": observed,
            "p_value": p_value,
            "significant_positive_edge": observed > 0.0 and p_value < (1.0 - self.confidence_level),
        }

    def analyze(self, trade_history):
        """Run all falsification tests and expose a conservative summary."""
        bootstrap = self.bootstrap_expectancy(trade_history)
        monte_carlo = self.monte_carlo_drawdown(trade_history)
        permutation = self.permutation_test(trade_history)
        return {
            "bootstrap": bootstrap,
            "monte_carlo": monte_carlo,
            "permutation": permutation,
            "passes_statistical_falsification": (
                bootstrap["positive_edge_supported"]
                and permutation["significant_positive_edge"]
            ),
        }
