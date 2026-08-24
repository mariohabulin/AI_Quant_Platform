import os
import sys

import numpy as np
import pandas as pd
import pytest

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src")))

from alpha_development_strategy import (
    ALPHA_DEVELOPMENT_VARIANTS,
    ADXRegimeVolumeStrategy,
    AlphaDevelopmentVariant,
    alpha_development_strategies,
)
from strategy_engine import StrategyEngine
from strategy_library import StrategyLibrary
from venue_execution_research import (
    VENUE_EXECUTION_SCENARIOS,
    VenueExecutionScenario,
    venue_execution_policy,
)


def featured_frame(rows=10):
    index = pd.date_range("2024-01-01T00:00:00Z", periods=rows, freq="6h")
    close = 100.0 + np.arange(rows, dtype=float)
    return pd.DataFrame(
        {
            "Open": close,
            "High": close + 1.0,
            "Low": close - 1.0,
            "Close": close,
            "Volume": np.full(rows, 10.0),
            "ADX_14": np.full(rows, 30.0),
            "PLUS_DI_14": np.full(rows, 25.0),
            "MINUS_DI_14": np.full(rows, 10.0),
            "ATR_14": np.full(rows, 2.0),
        },
        index=index,
    )


class FixedRegimeDetector:
    def __init__(self, labels):
        self.labels = labels

    def detect(self, data):
        labels = list(self.labels)
        if len(labels) == 1:
            labels *= len(data)
        trend = [label.split("_")[0] for label in labels]
        volatility = [label.split("_")[1] for label in labels]
        return pd.DataFrame(
            {
                "trend_score": np.ones(len(data)),
                "normalized_volatility": np.full(len(data), 0.01),
                "volatility_ratio": np.ones(len(data)),
                "trend_regime": trend,
                "volatility_regime": volatility,
                "market_regime": labels,
            },
            index=data.index,
        )


def fixed_volume(regimes="HIGH", obv="RISING"):
    def generate(data, configuration):
        result = data.copy(deep=True)
        count = len(result)
        regime_values = [regimes] * count if isinstance(regimes, str) else regimes
        obv_values = [obv] * count if isinstance(obv, str) else obv
        suffix = configuration.lookback
        result[f"VOLUME_BASELINE_{suffix}"] = 10.0
        result[f"RELATIVE_VOLUME_{suffix}"] = 2.0
        result["DOLLAR_VOLUME"] = result["Close"] * result["Volume"]
        result[f"DOLLAR_VOLUME_BASELINE_{suffix}"] = 1000.0
        result[f"RELATIVE_DOLLAR_VOLUME_{suffix}"] = 2.0
        result["ON_BALANCE_VOLUME"] = np.arange(count, dtype=float)
        result[f"ON_BALANCE_VOLUME_CHANGE_{suffix}"] = 1.0
        result[f"ON_BALANCE_VOLUME_DIRECTION_{suffix}"] = obv_values
        result[f"VOLUME_REGIME_{suffix}"] = regime_values
        return result

    return generate


def strategy(index=0, **kwargs):
    return ADXRegimeVolumeStrategy(
        ALPHA_DEVELOPMENT_VARIANTS[index],
        regime_detector=kwargs.pop(
            "regime_detector", FixedRegimeDetector(["BULLISH_NORMAL"])
        ),
        volume_feature_generator=kwargs.pop(
            "volume_feature_generator", fixed_volume()
        ),
        **kwargs,
    )


def test_variant_chain_is_exact_ordered_and_not_a_parameter_grid():
    assert [variant.variant_id for variant in ALPHA_DEVELOPMENT_VARIANTS] == [
        "adx_high_relative_volume",
        "adx_bullish_normal_high_relative_volume",
        "adx_bullish_normal_high_relative_volume_obv_rising",
    ]
    assert ALPHA_DEVELOPMENT_VARIANTS[0].required_market_regime is None
    assert ALPHA_DEVELOPMENT_VARIANTS[1].required_market_regime == "BULLISH_NORMAL"
    assert ALPHA_DEVELOPMENT_VARIANTS[2].required_obv_direction == "RISING"
    assert len(alpha_development_strategies()) == 3


@pytest.mark.parametrize(
    "kwargs,match",
    [
        ({"variant_id": ""}, "Variant ID"),
        ({"variant_id": "x", "required_market_regime": "BEARISH_HIGH"}, "BULLISH_NORMAL"),
        ({"variant_id": "x", "required_obv_direction": "FALLING"}, "RISING"),
    ],
)
def test_variant_rejects_unfrozen_condition_scope(kwargs, match):
    with pytest.raises(ValueError, match=match):
        AlphaDevelopmentVariant(**kwargs)


def test_strategy_enters_on_joint_completed_bar_conditions_and_records_risk_distance():
    data = featured_frame()
    result = strategy().generate_signals(data)
    assert result.iloc[0]["Signal"] == 1
    assert result["Signal"].sum() == 1
    assert result.iloc[0]["ALPHA_V2_ENTRY_CONDITION"]
    assert result.iloc[0]["ALPHA_V2_ATR_RISK_DISTANCE"] == pytest.approx(4.0)
    assert result.iloc[0]["ALPHA_V2_REWARD_RISK_RATIO"] == pytest.approx(3.0)
    assert "Signal" not in data.columns


def test_volume_is_mandatory_entry_confirmation_but_not_an_immediate_exit_trigger():
    data = featured_frame(4)
    result = strategy(
        volume_feature_generator=fixed_volume(
            regimes=["HIGH", "NORMAL", "NORMAL", "NORMAL"]
        )
    ).generate_signals(data)
    assert result["Signal"].tolist() == [1, 0, 0, 0]


def test_bullish_normal_and_obv_gates_are_direct_joint_intersections():
    data = featured_frame(3)
    regime_blocked = strategy(
        1, regime_detector=FixedRegimeDetector(["BULLISH_HIGH"])
    ).generate_signals(data)
    obv_blocked = strategy(
        2, volume_feature_generator=fixed_volume(obv="FALLING")
    ).generate_signals(data)
    assert not regime_blocked["ALPHA_V2_ENTRY_CONDITION"].any()
    assert not obv_blocked["ALPHA_V2_ENTRY_CONDITION"].any()
    assert regime_blocked["Signal"].eq(0).all()
    assert obv_blocked["Signal"].eq(0).all()


def test_exit_hysteresis_and_four_completed_bar_cooldown_reduce_reentry_churn():
    data = featured_frame(9)
    data.loc[data.index[2], "ADX_14"] = 19.0
    result = strategy().generate_signals(data)
    assert result["Signal"].tolist() == [1, 0, -1, 0, 0, 0, 0, 1, 0]


def test_strategy_engine_generates_adx_atr_and_causal_prefix_is_stable():
    rows = 100
    index = pd.date_range("2024-01-01T00:00:00Z", periods=rows, freq="6h")
    close = 100.0 + np.linspace(0.0, 30.0, rows) + np.sin(np.arange(rows) / 3.0)
    data = pd.DataFrame(
        {
            "Open": close - 0.2,
            "High": close + 1.0,
            "Low": close - 1.0,
            "Close": close,
            "Volume": 100.0 + (np.arange(rows) % 9) * 20.0,
        },
        index=index,
    )
    instance = ADXRegimeVolumeStrategy(ALPHA_DEVELOPMENT_VARIANTS[1])
    library = StrategyLibrary()
    library.register(instance)
    engine = StrategyEngine(library, instance.name)
    full = engine.run(data)
    prefix = engine.run(data.iloc[:70])
    pd.testing.assert_series_equal(
        full.iloc[:70]["Signal"], prefix["Signal"], check_names=True
    )
    assert set(full["Signal"].unique()).issubset({-1, 0, 1})


@pytest.mark.parametrize(
    "kwargs,match",
    [
        ({"entry_threshold": 20, "exit_threshold": 20}, "below"),
        ({"cooldown_bars": -1}, "range"),
        ({"reward_risk_ratio": 0}, "positive"),
    ],
)
def test_strategy_rejects_invalid_risk_and_churn_boundaries(kwargs, match):
    with pytest.raises((TypeError, ValueError), match=match):
        ADXRegimeVolumeStrategy(ALPHA_DEVELOPMENT_VARIANTS[0], **kwargs)


def test_venue_policy_keeps_taker_sensitivity_and_blocks_maker_without_fill_model():
    policy = venue_execution_policy()
    assert len(VENUE_EXECUTION_SCENARIOS) == 4
    assert "kraken_pro_10k_30d_taker_sensitivity_20260824" in policy[
        "runner_allowed_labels"
    ]
    assert "kraken_pro_10k_30d_maker_deferred_20260824" not in policy[
        "runner_allowed_labels"
    ]
    assert policy["maker_execution_status"] == "BLOCKED_PENDING_CAUSAL_FILL_MODEL"
    assert policy["static_tier_interpretation"] == (
        "SENSITIVITY_NOT_ACCOUNT_ELIGIBILITY_PROOF"
    )


def test_maker_scenario_cannot_be_marked_executable_without_fill_model():
    with pytest.raises(ValueError, match="fill model"):
        VenueExecutionScenario(
            label="bad",
            venue="venue",
            order_role="MAKER",
            commission_rate=0.001,
            slippage_rate=0.0,
            spread_rate=0.0,
            evidence_role="bad",
            eligibility="bad",
            source_url="https://example.com",
            source_accessed_utc="2026-08-24",
            executable_in_v2_runner=True,
        )
