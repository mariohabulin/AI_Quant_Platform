import pandas as pd

from feature_engine import validate_input, generate_atr


class MarketRegimeDetector:
    """Causal, deterministic market-regime detector for research analysis.

    Regimes are two-dimensional: trend (BULLISH/BEARISH/SIDEWAYS) and
    volatility (LOW/NORMAL/HIGH). Every value at time t uses only data at or
    before t, preventing future leakage during historical validation.
    """

    def __init__(
        self,
        fast_period=10,
        slow_period=30,
        atr_period=14,
        volatility_lookback=30,
        trend_threshold=0.50,
        high_volatility_ratio=1.25,
        low_volatility_ratio=0.80,
    ):
        for value, name in (
            (fast_period, "Fast period"),
            (slow_period, "Slow period"),
            (atr_period, "ATR period"),
            (volatility_lookback, "Volatility lookback"),
        ):
            if not isinstance(value, int) or isinstance(value, bool):
                raise TypeError(f"{name} must be an integer.")
            if value <= 0:
                raise ValueError(f"{name} must be greater than zero.")
        if fast_period >= slow_period:
            raise ValueError("Fast period must be less than slow period.")
        for value, name in (
            (trend_threshold, "Trend threshold"),
            (high_volatility_ratio, "High volatility ratio"),
            (low_volatility_ratio, "Low volatility ratio"),
        ):
            if not isinstance(value, (int, float)) or isinstance(value, bool):
                raise TypeError(f"{name} must be a number.")
            if float(value) <= 0:
                raise ValueError(f"{name} must be greater than zero.")
        if low_volatility_ratio >= high_volatility_ratio:
            raise ValueError("Low volatility ratio must be less than high volatility ratio.")

        self.fast_period = fast_period
        self.slow_period = slow_period
        self.atr_period = atr_period
        self.volatility_lookback = volatility_lookback
        self.trend_threshold = float(trend_threshold)
        self.high_volatility_ratio = float(high_volatility_ratio)
        self.low_volatility_ratio = float(low_volatility_ratio)

    def detect(self, data):
        validate_input(data)
        if not data.index.is_monotonic_increasing or data.index.has_duplicates:
            raise ValueError("Market regime data must have a unique chronological index.")

        result = generate_atr(data, self.atr_period)
        close = result["Close"].astype(float)
        fast = close.ewm(span=self.fast_period, adjust=False).mean()
        slow = close.ewm(span=self.slow_period, adjust=False).mean()
        atr = result[f"ATR_{self.atr_period}"]

        # ATR-normalized EMA separation makes trend strength comparable across
        # instruments with different price scales and volatility levels.
        trend_score = (fast - slow) / atr
        normalized_volatility = atr / close
        volatility_baseline = normalized_volatility.rolling(
            self.volatility_lookback,
            min_periods=self.volatility_lookback,
        ).median()
        volatility_ratio = normalized_volatility / volatility_baseline

        trend = pd.Series("UNKNOWN", index=result.index, dtype=object)
        ready_trend = trend_score.notna()
        trend.loc[ready_trend & (trend_score > self.trend_threshold)] = "BULLISH"
        trend.loc[ready_trend & (trend_score < -self.trend_threshold)] = "BEARISH"
        trend.loc[ready_trend & (trend_score.abs() <= self.trend_threshold)] = "SIDEWAYS"

        volatility = pd.Series("UNKNOWN", index=result.index, dtype=object)
        ready_vol = volatility_ratio.notna()
        volatility.loc[ready_vol & (volatility_ratio > self.high_volatility_ratio)] = "HIGH"
        volatility.loc[ready_vol & (volatility_ratio < self.low_volatility_ratio)] = "LOW"
        volatility.loc[
            ready_vol
            & (volatility_ratio >= self.low_volatility_ratio)
            & (volatility_ratio <= self.high_volatility_ratio)
        ] = "NORMAL"

        regime = trend + "_" + volatility
        regime.loc[(trend == "UNKNOWN") | (volatility == "UNKNOWN")] = "UNKNOWN"

        return pd.DataFrame(
            {
                "trend_score": trend_score,
                "normalized_volatility": normalized_volatility,
                "volatility_ratio": volatility_ratio,
                "trend_regime": trend,
                "volatility_regime": volatility,
                "market_regime": regime,
            },
            index=result.index,
        )


class RegimeConditionedAnalyzer:
    """Attribute unseen OOS trades to the regime present at trade entry."""

    def __init__(self, detector=None):
        if detector is not None and not isinstance(detector, MarketRegimeDetector):
            raise TypeError("Detector must be a MarketRegimeDetector.")
        self.detector = detector or MarketRegimeDetector()

    @staticmethod
    def _summarize(trades):
        pnl = [float(trade["profit_loss"]) for trade in trades]
        total = sum(pnl)
        return {
            "trade_count": len(trades),
            "net_profit_loss": total,
            "average_profit_loss": total / len(trades) if trades else 0.0,
            "win_rate": sum(value > 0.0 for value in pnl) / len(pnl) if pnl else 0.0,
        }

    def analyze(self, data, validation_result):
        if not isinstance(validation_result, dict):
            raise TypeError("Validation result must be a dictionary.")
        try:
            trades = validation_result["out_of_sample"]["out_of_sample"]["trade_history"]
        except (KeyError, TypeError) as exc:
            raise ValueError("Validation result does not contain OOS trade history.") from exc

        regimes = self.detector.detect(data)
        grouped = {}
        unattributed = 0
        for trade in trades:
            entry_index = trade.get("entry_index")
            if entry_index not in regimes.index:
                unattributed += 1
                continue
            label = regimes.at[entry_index, "market_regime"]
            if label == "UNKNOWN":
                unattributed += 1
                continue
            grouped.setdefault(label, []).append(trade)

        summaries = {label: self._summarize(grouped[label]) for label in sorted(grouped)}
        return {
            "regimes": summaries,
            "attributed_trade_count": sum(item["trade_count"] for item in summaries.values()),
            "unattributed_trade_count": unattributed,
            "observed_regime_count": len(summaries),
        }
