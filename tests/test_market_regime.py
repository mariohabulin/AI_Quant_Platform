import os
import sys

import pandas as pd
import pytest

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src")))

from market_regime import MarketRegimeDetector, RegimeConditionedAnalyzer


def market_data(rows=120, slope=0.5, range_size=2.0):
    index = pd.date_range("2024-01-01", periods=rows, freq="D")
    close = [100 + slope * i for i in range(rows)]
    return pd.DataFrame({
        "Open": close,
        "High": [p + range_size / 2 for p in close],
        "Low": [p - range_size / 2 for p in close],
        "Close": close,
        "Volume": [1000] * rows,
    }, index=index)


def validation_result(trades):
    return {"out_of_sample": {"out_of_sample": {"trade_history": trades}}}


def test_detector_returns_aligned_regime_frame():
    data = market_data()
    result = MarketRegimeDetector().detect(data)
    assert result.index.equals(data.index)
    assert set(result.columns) == {"trend_score", "normalized_volatility", "volatility_ratio", "trend_regime", "volatility_regime", "market_regime"}


def test_detector_identifies_bullish_trend_after_warmup():
    result = MarketRegimeDetector().detect(market_data(slope=1.0))
    assert result.iloc[-1]["trend_regime"] == "BULLISH"


def test_detector_identifies_bearish_trend_after_warmup():
    result = MarketRegimeDetector().detect(market_data(slope=-0.4))
    assert result.iloc[-1]["trend_regime"] == "BEARISH"


def test_detector_identifies_sideways_market():
    result = MarketRegimeDetector().detect(market_data(slope=0.0))
    assert result.iloc[-1]["trend_regime"] == "SIDEWAYS"


def test_detector_has_explicit_warmup_unknown_state():
    result = MarketRegimeDetector().detect(market_data())
    assert "UNKNOWN" in set(result["market_regime"])
    assert result.iloc[-1]["market_regime"] != "UNKNOWN"


def test_detector_is_deterministic():
    detector = MarketRegimeDetector()
    data = market_data()
    pd.testing.assert_frame_equal(detector.detect(data), detector.detect(data))


def test_detector_does_not_mutate_input():
    data = market_data(); original = data.copy(deep=True)
    MarketRegimeDetector().detect(data)
    pd.testing.assert_frame_equal(data, original)


def test_detector_rejects_non_chronological_or_duplicate_index():
    data = market_data()
    with pytest.raises(ValueError): MarketRegimeDetector().detect(data.iloc[::-1])
    duplicate = pd.concat([data.iloc[:2], data.iloc[[1]], data.iloc[2:]])
    with pytest.raises(ValueError): MarketRegimeDetector().detect(duplicate)


def test_detector_rejects_invalid_configuration():
    with pytest.raises(ValueError): MarketRegimeDetector(fast_period=30, slow_period=10)
    with pytest.raises(TypeError): MarketRegimeDetector(atr_period="14")
    with pytest.raises(ValueError): MarketRegimeDetector(low_volatility_ratio=1.5, high_volatility_ratio=1.2)


def test_detector_is_causal_for_past_rows():
    data = market_data(140, slope=0.6)
    detector = MarketRegimeDetector()
    prefix = detector.detect(data.iloc[:100])
    full = detector.detect(data)
    pd.testing.assert_frame_equal(prefix, full.iloc[:100])


def test_analyzer_attributes_oos_trade_by_entry_regime():
    data = market_data(140, slope=0.8)
    idx = data.index[-20]
    trades = [{"entry_index": idx, "exit_index": data.index[-18], "profit_loss": 25.0}]
    result = RegimeConditionedAnalyzer().analyze(data, validation_result(trades))
    assert result["attributed_trade_count"] == 1
    assert result["unattributed_trade_count"] == 0
    assert list(result["regimes"].values())[0]["net_profit_loss"] == 25.0


def test_analyzer_reports_unattributed_warmup_trades():
    data = market_data()
    trades = [{"entry_index": data.index[0], "exit_index": data.index[1], "profit_loss": 1.0}]
    result = RegimeConditionedAnalyzer().analyze(data, validation_result(trades))
    assert result["attributed_trade_count"] == 0
    assert result["unattributed_trade_count"] == 1


def test_analyzer_summarizes_win_rate_and_average_pnl():
    data = market_data(140, slope=0.8)
    a, b = data.index[-20], data.index[-10]
    trades = [
        {"entry_index": a, "exit_index": data.index[-19], "profit_loss": 30.0},
        {"entry_index": b, "exit_index": data.index[-9], "profit_loss": -10.0},
    ]
    result = RegimeConditionedAnalyzer().analyze(data, validation_result(trades))
    summary = list(result["regimes"].values())[0]
    assert summary["trade_count"] == 2
    assert summary["net_profit_loss"] == 20.0
    assert summary["average_profit_loss"] == 10.0
    assert summary["win_rate"] == 0.5


def test_analyzer_rejects_malformed_validation_result():
    with pytest.raises(TypeError): RegimeConditionedAnalyzer().analyze(market_data(), [])
    with pytest.raises(ValueError): RegimeConditionedAnalyzer().analyze(market_data(), {})
