import os
import sys

import numpy as np
import pandas as pd
import pytest

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src")))

from alpha_discovery_protocol import (
    CALIBRATION_PARAMETER_CATALOG,
    PARAMETER_SET_ORDER,
)
from alpha_discovery_strategy import (
    AlphaDiscoveryStrategy,
    alpha_discovery_strategy_engines,
)
from strategy_engine import StrategyEngine
from strategy_library import StrategyLibrary


def featured_frame(rows=12):
    index = pd.date_range("2024-01-01T00:00:00Z", periods=rows, freq="6h")
    close = 100.0 + np.arange(rows, dtype=float)
    return pd.DataFrame(
        {
            "Open": close,
            "High": close + 1.0,
            "Low": close - 1.0,
            "Close": close,
            "Volume": np.full(rows, 100.0),
            "ADX_14": np.full(rows, 30.0),
            "PLUS_DI_14": np.full(rows, 25.0),
            "MINUS_DI_14": np.full(rows, 10.0),
            "ATR_14": np.full(rows, 2.0),
        },
        index=index,
    )


class FixedRegimeDetector:
    def __init__(self, labels="BULLISH_NORMAL"):
        self.labels = labels

    def detect(self, data):
        labels = (
            [self.labels] * len(data)
            if isinstance(self.labels, str)
            else list(self.labels)
        )
        return pd.DataFrame(
            {
                "trend_score": 1.0,
                "normalized_volatility": 0.01,
                "volatility_ratio": 1.0,
                "trend_regime": [value.split("_")[0] for value in labels],
                "volatility_regime": [value.split("_")[1] for value in labels],
                "market_regime": labels,
            },
            index=data.index,
        )


class FixedTrendStructure:
    def __init__(self, values=True):
        self.values = values

    def generate(self, data):
        result = data.copy(deep=True)
        values = (
            [self.values] * len(result)
            if isinstance(self.values, bool)
            else list(self.values)
        )
        result["ALPHA_DISCOVERY_EMA_50"] = result["Close"]
        result["ALPHA_DISCOVERY_EMA_200"] = result["Close"] - 1.0
        result["ALPHA_DISCOVERY_EMA_50_SLOPE_4"] = 1.0
        result["ALPHA_DISCOVERY_TREND_STRUCTURE"] = values
        return result

    def configuration(self):
        return {
            "fast_period": 50,
            "slow_period": 200,
            "slope_lookback": 4,
            "causal": True,
        }


def fixed_volume(data, configuration):
    result = data.copy(deep=True)
    suffix = configuration.lookback
    result[f"VOLUME_REGIME_{suffix}"] = "HIGH"
    result[f"RELATIVE_VOLUME_{suffix}"] = 2.0
    result[f"ON_BALANCE_VOLUME_DIRECTION_{suffix}"] = "RISING"
    return result


def strategy(parameter_index=0, **kwargs):
    return AlphaDiscoveryStrategy(
        CALIBRATION_PARAMETER_CATALOG[parameter_index],
        regime_detector=kwargs.pop(
            "regime_detector", FixedRegimeDetector()
        ),
        volume_feature_generator=kwargs.pop(
            "volume_feature_generator", fixed_volume
        ),
        trend_structure=kwargs.pop(
            "trend_structure", FixedTrendStructure()
        ),
        **kwargs,
    )


def test_discovery_strategy_engines_cover_exact_catalog_order():
    engines = alpha_discovery_strategy_engines()
    assert tuple(engines) == PARAMETER_SET_ORDER
    assert tuple(
        engine.strategy.parameter_set.parameter_set_id
        for engine in engines.values()
    ) == PARAMETER_SET_ORDER
    assert len({engine.strategy_name for engine in engines.values()}) == 8


def test_entry_requires_trend_regime_volume_direction_and_completed_atr():
    data = featured_frame()
    result = strategy().generate_signals(data)
    assert result["Signal"].tolist() == [1] + [0] * (len(data) - 1)
    assert result.iloc[0]["ALPHA_DISCOVERY_ENTRY_CONDITION"]
    assert result.iloc[0]["ALPHA_V2_ATR_RISK_DISTANCE"] == pytest.approx(3.0)
    assert result.iloc[0]["ALPHA_V2_REWARD_RISK_RATIO"] == pytest.approx(3.0)
    assert result.iloc[0]["ALPHA_DISCOVERY_PARAMETER_SET_ID"] == (
        "adx20-15-atr1p5-static3r"
    )

    blocked = strategy(
        trend_structure=FixedTrendStructure(False)
    ).generate_signals(data)
    assert blocked["Signal"].eq(0).all()
    assert not blocked["ALPHA_DISCOVERY_ENTRY_CONDITION"].any()


def test_evaluation_start_resets_position_state_without_losing_prior_features():
    data = featured_frame(10)
    result = strategy().generate_signals(data, evaluation_start_position=5)
    assert result["Signal"].tolist() == [0, 0, 0, 0, 0, 1, 0, 0, 0, 0]
    assert result.iloc[4]["ALPHA_DISCOVERY_ENTRY_CONDITION"]
    assert result.iloc[5]["ALPHA_DISCOVERY_ENTRY_CONDITION"]


def test_hysteresis_and_cooldown_use_parameter_set_values():
    data = featured_frame(10)
    data.loc[data.index[2], "ADX_14"] = 14.0
    result = strategy().generate_signals(data)
    assert result["Signal"].tolist() == [1, 0, -1, 0, 0, 0, 0, 1, 0, 0]


@pytest.mark.parametrize("value", [-1, True, 12])
def test_evaluation_start_fails_closed(value):
    with pytest.raises((TypeError, ValueError), match="Evaluation start"):
        strategy().generate_signals(featured_frame(), value)


def test_real_feature_path_is_prefix_causal():
    rows = 280
    index = pd.date_range("2024-01-01T00:00:00Z", periods=rows, freq="6h")
    close = 100.0 + np.linspace(0.0, 60.0, rows) + np.sin(np.arange(rows) / 5.0)
    data = pd.DataFrame(
        {
            "Open": close - 0.1,
            "High": close + 1.0,
            "Low": close - 1.0,
            "Close": close,
            "Volume": 100.0 + (np.arange(rows) % 11) * 40.0,
        },
        index=index,
    )
    instance = AlphaDiscoveryStrategy(CALIBRATION_PARAMETER_CATALOG[0])
    library = StrategyLibrary()
    library.register(instance)
    engine = StrategyEngine(library, instance.name)

    full = engine.run(data)
    prefix = engine.run(data.iloc[:250])

    pd.testing.assert_series_equal(
        full.iloc[:250]["Signal"], prefix["Signal"], check_names=True
    )
    pd.testing.assert_series_equal(
        full.iloc[:250]["ALPHA_DISCOVERY_TREND_STRUCTURE"],
        prefix["ALPHA_DISCOVERY_TREND_STRUCTURE"],
        check_names=True,
    )
