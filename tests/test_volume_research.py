import os
import sys

import numpy as np
import pandas as pd
import pytest

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src")))

from volume_research import (
    VolumeConditionedAnalyzer,
    VolumeResearchConfig,
    generate_volume_research_features,
)


def market_frame(volumes, closes=None):
    volumes = np.asarray(volumes, dtype=float)
    if closes is None:
        closes = 100.0 + np.arange(len(volumes), dtype=float)
    closes = np.asarray(closes, dtype=float)
    index = pd.date_range("2024-01-01T00:00:00Z", periods=len(volumes), freq="6h")
    return pd.DataFrame(
        {
            "Open": closes,
            "High": closes + 1.0,
            "Low": closes - 1.0,
            "Close": closes,
            "Volume": volumes,
        },
        index=index,
    )


def validation_result(trades):
    return {"out_of_sample": {"out_of_sample": {"trade_history": trades}}}


def test_volume_configuration_freezes_relative_cross_asset_defaults():
    configuration = VolumeResearchConfig()

    assert configuration.lookback == 20
    assert configuration.low_relative_volume == pytest.approx(0.75)
    assert configuration.high_relative_volume == pytest.approx(1.50)
    assert configuration.baseline_lag == 1
    assert configuration.as_dict() == {
        "lookback": 20,
        "baseline_statistic": "TRAILING_MEDIAN",
        "baseline_lag": 1,
        "low_relative_volume": 0.75,
        "high_relative_volume": 1.5,
        "cross_asset_normalization": "PER_ASSET_RELATIVE_NOT_RAW_VOLUME",
        "signal_observation": "COMPLETED_BAR_ONLY",
    }


@pytest.mark.parametrize(
    "kwargs,match",
    [
        ({"lookback": True}, "lookback"),
        ({"lookback": 1}, "at least 2"),
        ({"baseline_lag": 0}, "baseline lag"),
        ({"low_relative_volume": 0.0}, "threshold"),
        (
            {"low_relative_volume": 2.0, "high_relative_volume": 1.0},
            "less than",
        ),
    ],
)
def test_volume_configuration_rejects_invalid_values(kwargs, match):
    with pytest.raises((TypeError, ValueError), match=match):
        VolumeResearchConfig(**kwargs)


def test_relative_volume_uses_only_prior_completed_bars():
    data = market_frame([10.0, 20.0, 30.0, 60.0])
    result = generate_volume_research_features(
        data,
        VolumeResearchConfig(lookback=2),
    )

    assert pd.isna(result.iloc[1]["RELATIVE_VOLUME_2"])
    assert result.iloc[2]["VOLUME_BASELINE_2"] == pytest.approx(15.0)
    assert result.iloc[2]["RELATIVE_VOLUME_2"] == pytest.approx(2.0)
    assert result.iloc[2]["VOLUME_REGIME_2"] == "HIGH"
    assert result.iloc[3]["VOLUME_BASELINE_2"] == pytest.approx(25.0)
    assert result.iloc[3]["RELATIVE_VOLUME_2"] == pytest.approx(2.4)


def test_relative_features_are_scale_invariant_across_assets():
    configuration = VolumeResearchConfig(lookback=3)
    first = generate_volume_research_features(
        market_frame([10, 20, 15, 30, 12]),
        configuration,
    )
    second = generate_volume_research_features(
        market_frame([1000, 2000, 1500, 3000, 1200]),
        configuration,
    )

    pd.testing.assert_series_equal(
        first["RELATIVE_VOLUME_3"],
        second["RELATIVE_VOLUME_3"],
    )
    pd.testing.assert_series_equal(
        first["VOLUME_REGIME_3"],
        second["VOLUME_REGIME_3"],
    )


def test_volume_features_are_causal_for_every_completed_prefix():
    configuration = VolumeResearchConfig(lookback=3)
    data = market_frame([10, 12, 11, 25, 9, 30, 18, 7])
    full = generate_volume_research_features(data, configuration)

    for size in range(1, len(data) + 1):
        prefix = generate_volume_research_features(data.iloc[:size], configuration)
        pd.testing.assert_frame_equal(prefix, full.iloc[:size])


def test_volume_features_preserve_input_and_compute_obv():
    data = market_frame(
        [10, 20, 30, 40],
        closes=[100, 102, 101, 101],
    )
    original = data.copy(deep=True)
    result = generate_volume_research_features(
        data,
        VolumeResearchConfig(lookback=2),
    )

    pd.testing.assert_frame_equal(data, original)
    assert result["ON_BALANCE_VOLUME"].tolist() == pytest.approx(
        [0.0, 20.0, -10.0, -10.0]
    )


@pytest.mark.parametrize("problem", ["reverse", "duplicate", "negative", "nan"])
def test_volume_features_reject_invalid_market_evidence(problem):
    data = market_frame([10, 20, 30, 40])
    if problem == "reverse":
        data = data.iloc[::-1]
    elif problem == "duplicate":
        data = pd.concat([data.iloc[:2], data.iloc[[1]], data.iloc[2:]])
    elif problem == "negative":
        data.loc[data.index[1], "Volume"] = -1.0
    else:
        data.loc[data.index[1], "Volume"] = np.nan

    with pytest.raises(ValueError):
        generate_volume_research_features(data, VolumeResearchConfig(lookback=2))


def test_volume_conditioning_uses_signal_bar_not_execution_bar():
    data = market_frame([10, 10, 10, 50, 10, 10, 10])
    signal_index = data.index[3]
    execution_index = data.index[4]
    trade = {
        "entry_signal_index": signal_index,
        "entry_index": execution_index,
        "exit_index": data.index[5],
        "gross_profit_loss": 30.0,
        "total_costs": 5.0,
        "profit_loss": 25.0,
    }

    result = VolumeConditionedAnalyzer(
        VolumeResearchConfig(lookback=3)
    ).analyze(data, validation_result([trade]))

    assert result["signal_bar_attribution"] is True
    assert result["volume_regimes"]["HIGH"]["trade_count"] == 1
    assert result["volume_regimes"]["HIGH"]["net_profit_loss"] == pytest.approx(25.0)


def test_volume_conditioning_separates_gross_cost_and_net_results():
    data = market_frame([10, 10, 10, 50, 12, 8, 30, 9])
    trades = [
        {
            "entry_signal_index": data.index[3],
            "entry_index": data.index[4],
            "exit_index": data.index[5],
            "gross_profit_loss": 40.0,
            "total_costs": 10.0,
            "profit_loss": 30.0,
        },
        {
            "entry_signal_index": data.index[6],
            "entry_index": data.index[7],
            "exit_index": data.index[7],
            "gross_profit_loss": -5.0,
            "total_costs": 3.0,
            "profit_loss": -8.0,
        },
    ]

    result = VolumeConditionedAnalyzer(
        VolumeResearchConfig(lookback=3)
    ).analyze(data, validation_result(trades))
    high = result["volume_regimes"]["HIGH"]

    assert high["trade_count"] == 2
    assert high["gross_profit_loss"] == pytest.approx(35.0)
    assert high["total_costs"] == pytest.approx(13.0)
    assert high["net_profit_loss"] == pytest.approx(22.0)
    assert high["win_rate"] == pytest.approx(0.5)


def test_volume_conditioning_reports_warmup_as_unattributed():
    data = market_frame([10, 10, 10, 50])
    trade = {
        "entry_signal_index": data.index[0],
        "entry_index": data.index[1],
        "exit_index": data.index[2],
        "gross_profit_loss": 5.0,
        "total_costs": 1.0,
        "profit_loss": 4.0,
    }

    result = VolumeConditionedAnalyzer(
        VolumeResearchConfig(lookback=3)
    ).analyze(data, validation_result([trade]))

    assert result["attributed_trade_count"] == 0
    assert result["unattributed_trade_count"] == 1


def test_volume_conditioning_rejects_malformed_validation_result():
    analyzer = VolumeConditionedAnalyzer(VolumeResearchConfig(lookback=2))
    with pytest.raises(TypeError):
        analyzer.analyze(market_frame([10, 20, 30]), [])
    with pytest.raises(ValueError, match="trade history"):
        analyzer.analyze(market_frame([10, 20, 30]), {})
