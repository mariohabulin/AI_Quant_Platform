"""Deterministic diagnostics for explaining rejected strategy behavior."""

import math

import numpy as np
import pandas as pd

try:
    from market_regime import MarketRegimeDetector
    from volume_research import VolumeConditionedAnalyzer, VolumeResearchConfig
except ImportError:  # package import when src is not placed directly on sys.path
    from src.market_regime import MarketRegimeDetector
    from src.volume_research import (
        VolumeConditionedAnalyzer,
        VolumeResearchConfig,
    )


TRADE_NUMERIC_FIELDS = (
    "entry_market_price",
    "exit_market_price",
    "shares",
    "gross_profit_loss",
    "total_commission",
    "execution_cost",
    "total_costs",
    "profit_loss",
)


def _finite_float(value, name):
    try:
        result = float(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{name} must be numeric.") from exc
    if not math.isfinite(result):
        raise ValueError(f"{name} must be finite.")
    return result


def _trade_summary(trades):
    gross = sum(_finite_float(item["gross_profit_loss"], "Gross P/L") for item in trades)
    costs = sum(_finite_float(item["total_costs"], "Total costs") for item in trades)
    net = sum(_finite_float(item["profit_loss"], "Net P/L") for item in trades)
    return {
        "trade_count": len(trades),
        "gross_profit_loss": gross,
        "total_costs": costs,
        "net_profit_loss": net,
        "average_net_profit_loss": net / len(trades) if trades else 0.0,
        "win_rate": (
            sum(_finite_float(item["profit_loss"], "Net P/L") > 0.0 for item in trades)
            / len(trades)
            if trades
            else 0.0
        ),
    }


class FailureAttributionMetrics:
    """Derive causal OOS failure diagnostics from one raw asset evaluation."""

    def __init__(
        self,
        granularity_seconds=21600,
        market_regime_detector=None,
        volume_configuration=None,
    ):
        if isinstance(granularity_seconds, bool) or not isinstance(
            granularity_seconds, int
        ):
            raise TypeError("Granularity seconds must be an integer.")
        if granularity_seconds <= 0:
            raise ValueError("Granularity seconds must be greater than zero.")
        if market_regime_detector is None:
            market_regime_detector = MarketRegimeDetector()
        if not callable(getattr(market_regime_detector, "detect", None)):
            raise TypeError("Market-regime detector must provide detect(data).")
        if volume_configuration is None:
            volume_configuration = VolumeResearchConfig()
        if not isinstance(volume_configuration, VolumeResearchConfig):
            raise TypeError("Volume configuration must be a VolumeResearchConfig.")
        self.granularity_seconds = granularity_seconds
        self.market_regime_detector = market_regime_detector
        self.volume_analyzer = VolumeConditionedAnalyzer(volume_configuration)

    @staticmethod
    def _validated_inputs(data, asset_result):
        if not isinstance(data, pd.DataFrame):
            raise TypeError("Attribution market data must be a pandas DataFrame.")
        if data.empty or not isinstance(data.index, pd.DatetimeIndex):
            raise ValueError("Attribution market data must have a DatetimeIndex.")
        if not data.index.is_monotonic_increasing or data.index.has_duplicates:
            raise ValueError("Attribution market data index must be unique and ordered.")
        if not isinstance(asset_result, dict):
            raise TypeError("Asset validation result must be a dictionary.")
        try:
            split_position = asset_result["out_of_sample"]["split"]["split_position"]
            partition = asset_result["out_of_sample"]["out_of_sample"]
            trades = partition["trade_history"]
            equity_curve = partition["equity_curve"]
            initial_capital = _finite_float(
                partition["initial_capital"], "Initial capital"
            )
        except (KeyError, TypeError) as exc:
            raise ValueError("Asset validation result is missing raw OOS evidence.") from exc
        if isinstance(split_position, bool) or not isinstance(split_position, int):
            raise ValueError("OOS split position must be an integer.")
        if not 0 <= split_position < len(data):
            raise ValueError("OOS split position is outside market data.")
        if not isinstance(trades, list) or not isinstance(equity_curve, list):
            raise ValueError("OOS trade history and equity curve must be lists.")
        if initial_capital <= 0.0:
            raise ValueError("Initial capital must be greater than zero.")
        oos_data = data.iloc[split_position:]
        if len(equity_curve) != len(oos_data):
            raise ValueError("OOS equity curve must align with the OOS market frame.")
        for trade in trades:
            if not isinstance(trade, dict):
                raise ValueError("Every trade must be a dictionary.")
            for field in TRADE_NUMERIC_FIELDS:
                try:
                    _finite_float(trade[field], f"Trade {field}")
                except KeyError as exc:
                    raise ValueError(f"Trade evidence is missing {field}.") from exc
            gross = float(trade["gross_profit_loss"])
            commission = float(trade["total_commission"])
            execution = float(trade["execution_cost"])
            costs = float(trade["total_costs"])
            net = float(trade["profit_loss"])
            tolerance = max(1.0, abs(gross), abs(costs), abs(net)) * 1e-10
            if abs((commission + execution) - costs) > tolerance:
                raise ValueError("Trade cost components do not equal total costs.")
            if abs((gross - costs) - net) > tolerance:
                raise ValueError("Trade gross minus costs does not equal net P/L.")
            for field in ("entry_signal_index", "entry_index", "exit_index"):
                if trade.get(field) not in data.index:
                    raise ValueError(f"Trade {field} is outside market evidence.")
        for point in equity_curve:
            if not isinstance(point, dict) or point.get("index") not in oos_data.index:
                raise ValueError("Equity evidence index is outside the OOS frame.")
            _finite_float(point.get("equity"), "Equity")
        return oos_data, partition, trades, equity_curve, initial_capital

    @staticmethod
    def _cost_turnover(trades, initial_capital):
        gross = sum(float(item["gross_profit_loss"]) for item in trades)
        commission = sum(float(item["total_commission"]) for item in trades)
        execution = sum(float(item["execution_cost"]) for item in trades)
        costs = sum(float(item["total_costs"]) for item in trades)
        net = sum(float(item["profit_loss"]) for item in trades)
        entry_notional = sum(
            float(item["shares"]) * float(item["entry_market_price"])
            for item in trades
        )
        exit_notional = sum(
            float(item["shares"]) * float(item["exit_market_price"])
            for item in trades
        )
        round_trip_notional = entry_notional + exit_notional
        tolerance = max(1.0, abs(gross), abs(costs), abs(net)) * 1e-10
        return {
            "trade_count": len(trades),
            "gross_profit_loss": gross,
            "total_commission": commission,
            "execution_cost": execution,
            "total_costs": costs,
            "net_profit_loss": net,
            "gross_minus_costs_equals_net": abs((gross - costs) - net)
            <= tolerance,
            "entry_notional": entry_notional,
            "exit_notional": exit_notional,
            "round_trip_notional": round_trip_notional,
            "turnover_multiple_of_initial_capital": (
                round_trip_notional / initial_capital
            ),
            "average_total_cost_per_trade": (
                costs / len(trades) if trades else 0.0
            ),
        }

    def _exposure_holding(self, oos_data, trades):
        positions = {value: index for index, value in enumerate(oos_data.index)}
        occupied = set()
        holding_bars = []
        terminal_count = 0
        for trade in trades:
            entry = trade["entry_index"]
            exit_ = trade["exit_index"]
            if entry not in positions or exit_ not in positions:
                raise ValueError("OOS trade boundary is outside the OOS market frame.")
            entry_position = positions[entry]
            exit_position = positions[exit_]
            if exit_position < entry_position:
                raise ValueError("Trade exit precedes entry.")
            terminal = trade.get("exit_signal_index") is None
            held = exit_position - entry_position + (1 if terminal else 0)
            if held <= 0:
                raise ValueError("Trade holding period must be positive.")
            terminal_count += int(terminal)
            holding_bars.append(held)
            stop = exit_position + (1 if terminal else 0)
            interval = set(range(entry_position, stop))
            if occupied.intersection(interval):
                raise ValueError("Long-only OOS trades must not overlap.")
            occupied.update(interval)
        holding_hours = [
            value * self.granularity_seconds / 3600.0 for value in holding_bars
        ]
        return {
            "oos_bars": len(oos_data),
            "exposure_bars": len(occupied),
            "exposure_percent": len(occupied) / len(oos_data) * 100.0,
            "holding_bars": holding_bars,
            "holding_hours": holding_hours,
            "mean_holding_bars": (
                float(np.mean(holding_bars)) if holding_bars else None
            ),
            "median_holding_bars": (
                float(np.median(holding_bars)) if holding_bars else None
            ),
            "minimum_holding_bars": min(holding_bars) if holding_bars else None,
            "maximum_holding_bars": max(holding_bars) if holding_bars else None,
            "terminal_force_close_count": terminal_count,
        }

    @staticmethod
    def _drawdown(equity_curve):
        if not equity_curve:
            raise ValueError("OOS equity curve cannot be empty.")
        peak_equity = float(equity_curve[0]["equity"])
        peak_index = equity_curve[0]["index"]
        max_drawdown = 0.0
        max_peak_index = None
        trough_index = None
        trough_peak_equity = None
        drawdowns = []
        by_year = {}
        for point in equity_curve:
            equity = float(point["equity"])
            index = point["index"]
            if equity > peak_equity:
                peak_equity = equity
                peak_index = index
            drawdown = (peak_equity - equity) / peak_equity * 100.0
            drawdowns.append(drawdown)
            year = str(pd.Timestamp(index).year)
            by_year[year] = max(by_year.get(year, 0.0), drawdown)
            if drawdown > max_drawdown:
                max_drawdown = drawdown
                max_peak_index = peak_index
                trough_index = index
                trough_peak_equity = peak_equity

        recovery_index = None
        if trough_index is not None:
            trough_position = next(
                index
                for index, point in enumerate(equity_curve)
                if point["index"] == trough_index
            )
            for point in equity_curve[trough_position + 1 :]:
                if float(point["equity"]) >= trough_peak_equity:
                    recovery_index = point["index"]
                    break
        underwater_count = sum(value > 0.0 for value in drawdowns)
        return {
            "max_drawdown_percent": max_drawdown,
            "peak_index": max_peak_index,
            "trough_index": trough_index,
            "recovery_index": recovery_index,
            "recovered": recovery_index is not None if trough_index is not None else True,
            "underwater_bar_count": underwater_count,
            "underwater_percent": underwater_count / len(drawdowns) * 100.0,
            "max_drawdown_by_year_percent": {
                year: by_year[year] for year in sorted(by_year)
            },
        }

    def _market_regime(self, data, trades):
        regimes = self.market_regime_detector.detect(data)
        if (
            not isinstance(regimes, pd.DataFrame)
            or "market_regime" not in regimes.columns
            or not regimes.index.equals(data.index)
        ):
            raise ValueError("Market-regime evidence must align with market data.")
        grouped = {}
        unattributed = 0
        for trade in trades:
            signal_index = trade.get("entry_signal_index")
            if signal_index not in regimes.index:
                unattributed += 1
                continue
            label = regimes.at[signal_index, "market_regime"]
            if not isinstance(label, str) or label == "UNKNOWN":
                unattributed += 1
                continue
            grouped.setdefault(label, []).append(trade)
        summaries = {
            label: _trade_summary(grouped[label]) for label in sorted(grouped)
        }
        return {
            "signal_bar_attribution": True,
            "regimes": summaries,
            "attributed_trade_count": sum(
                item["trade_count"] for item in summaries.values()
            ),
            "unattributed_trade_count": unattributed,
            "observed_regime_count": len(summaries),
        }

    def analyze(self, data, asset_result):
        oos_data, _partition, trades, equity_curve, initial_capital = (
            self._validated_inputs(data, asset_result)
        )
        return {
            "cost_turnover": self._cost_turnover(trades, initial_capital),
            "exposure_holding": self._exposure_holding(oos_data, trades),
            "drawdown": self._drawdown(equity_curve),
            "market_regime": self._market_regime(data, trades),
            "volume": self.volume_analyzer.analyze(data, asset_result),
        }
