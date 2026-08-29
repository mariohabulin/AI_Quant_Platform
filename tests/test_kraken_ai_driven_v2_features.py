import os
import sys

import numpy as np
import pandas as pd
import pytest

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src")))

from kraken_ai_driven_v2_features import (
    FEATURE_COLUMNS,
    KrakenAIDrivenV2FeatureConfig,
    KrakenAIDrivenV2FeatureEngine,
)


def market_frame(rows=12):
    close = np.array(
        [100.0, 102.0, 101.0, 90.0, 91.0, 92.0, 94.0, 93.0, 95.0, 96.0, 97.0, 98.0]
    )[:rows]
    high = close + 2.0
    low = close - 2.0
    volume = np.array(
        [10.0, 20.0, 30.0, 60.0, 40.0, 30.0, 25.0, 35.0, 45.0, 55.0, 50.0, 40.0]
    )[:rows]
    return pd.DataFrame(
        {
            "Open": close,
            "High": high,
            "Low": low,
            "Close": close,
            "Volume": volume,
        },
        index=pd.date_range("2026-01-01", periods=rows, freq="D", tz="UTC"),
    )


def engine():
    return KrakenAIDrivenV2FeatureEngine(
        KrakenAIDrivenV2FeatureConfig(
            decline_lookback_bars=3,
            volume_lookback_bars=3,
            atr_lookback_bars=3,
        )
    )


def test_configuration_has_no_action_threshold_or_future_access():
    configuration = engine().configuration()

    assert configuration["observation_timing"] == "COMPLETED_DAILY_BAR_CLOSE"
    assert configuration["execution_timing"] == "NOT_DEFINED_BY_FEATURE_CONTRACT"
    assert configuration["baseline_current_bar_included"] is False
    assert configuration["future_bar_access"] is False
    assert configuration["signal_thresholds_frozen"] is False
    assert configuration["trading_actions_emitted"] is False
    assert configuration["gap_policy"] == "SPLIT_BEFORE_FEATURE_GENERATION"
    assert "entry" not in " ".join(configuration["feature_columns"]).lower()
    assert "signal" not in " ".join(configuration["feature_columns"]).lower()


@pytest.mark.parametrize("field", [0, 1, 2])
@pytest.mark.parametrize("value", [0, -1, 1.5, True, "30"])
def test_feature_windows_must_be_explicit_positive_integers(field, value):
    values = [3, 3, 3]
    values[field] = value
    with pytest.raises(ValueError, match="positive integer"):
        KrakenAIDrivenV2FeatureConfig(*values)


def test_feature_engine_requires_exact_config_type():
    with pytest.raises(TypeError, match="FeatureConfig"):
        KrakenAIDrivenV2FeatureEngine({"decline_lookback_bars": 3})


def test_completed_bar_features_use_only_prior_baselines_and_current_measurement():
    result = engine().generate(market_frame())
    row = result.iloc[3]

    assert row[FEATURE_COLUMNS[0]] == pytest.approx(101.0)
    assert row[FEATURE_COLUMNS[1]] == pytest.approx(90.0 / 101.0 - 1.0)
    assert row[FEATURE_COLUMNS[2]] == pytest.approx(102.0)
    assert row[FEATURE_COLUMNS[3]] == pytest.approx((102.0 - 90.0) / 102.0)
    assert row[FEATURE_COLUMNS[4]] == pytest.approx(20.0)
    assert row[FEATURE_COLUMNS[5]] == pytest.approx(3.0)
    assert row[FEATURE_COLUMNS[6]] == pytest.approx(13.0)
    assert row[FEATURE_COLUMNS[7]] == pytest.approx(4.0)
    assert row[FEATURE_COLUMNS[8]] == pytest.approx(3.25)
    assert row[FEATURE_COLUMNS[9]] == pytest.approx(0.5)


def test_current_volume_cannot_change_its_own_lagged_baseline():
    original = market_frame()
    changed = original.copy(deep=True)
    changed.iloc[3, changed.columns.get_loc("Volume")] = 6000.0

    first = engine().generate(original).iloc[3]
    second = engine().generate(changed).iloc[3]

    assert first[FEATURE_COLUMNS[4]] == second[FEATURE_COLUMNS[4]] == 20.0
    assert first[FEATURE_COLUMNS[5]] == pytest.approx(3.0)
    assert second[FEATURE_COLUMNS[5]] == pytest.approx(300.0)


def test_feature_path_is_prefix_causal_and_future_stable():
    data = market_frame()
    full = engine().generate(data)
    prefix = engine().generate(data.iloc[:8])

    pd.testing.assert_frame_equal(full.iloc[:8], prefix)

    changed_future = data.copy(deep=True)
    changed_future.iloc[8:, :] = changed_future.iloc[8:, :] * 50.0
    changed = engine().generate(changed_future)
    pd.testing.assert_frame_equal(full.iloc[:8], changed.iloc[:8])


def test_generator_does_not_mutate_the_source_frame():
    data = market_frame()
    before = data.copy(deep=True)

    result = engine().generate(data)

    pd.testing.assert_frame_equal(data, before)
    assert all(column not in data.columns for column in FEATURE_COLUMNS)
    assert all(column in result.columns for column in FEATURE_COLUMNS)


def test_warmup_and_unavailable_denominators_fail_closed_with_nan():
    data = market_frame()
    data.loc[data.index[:4], "Volume"] = 0.0
    data.loc[data.index[5], ["Open", "High", "Low", "Close"]] = 92.0

    result = engine().generate(data)

    assert pd.isna(result.iloc[2][FEATURE_COLUMNS[2]])
    assert pd.isna(result.iloc[3][FEATURE_COLUMNS[5]])
    assert pd.isna(result.iloc[5][FEATURE_COLUMNS[9]])
    assert not np.isinf(result.loc[:, FEATURE_COLUMNS].to_numpy(dtype=float)).any()


@pytest.mark.parametrize(
    "mutator,error",
    [
        (lambda data: data.rename(columns={"Volume": "Trades"}), "ordered OHLCV"),
        (lambda data: data.assign(Trades=1), "ordered OHLCV"),
        (lambda data: data.set_index(pd.RangeIndex(len(data))), "DatetimeIndex"),
        (lambda data: data.tz_localize(None), "timezone-aware"),
        (lambda data: data.iloc[::-1], "increase"),
        (
            lambda data: pd.concat([data, data.iloc[[-1]]]),
            "unique",
        ),
        (lambda data: data.drop(data.index[4]), "continuous daily"),
        (
            lambda data: data.set_axis(
                data.index + pd.Timedelta(hours=1), axis="index"
            ),
            "UTC midnight",
        ),
        (
            lambda data: data.assign(Volume=np.nan),
            "finite numeric",
        ),
        (
            lambda data: data.assign(Volume=-1.0),
            "volume nonnegative",
        ),
        (
            lambda data: data.assign(High=data["Low"] - 1.0),
            "geometry",
        ),
    ],
)
def test_feature_data_validation_fails_closed(mutator, error):
    with pytest.raises((TypeError, ValueError), match=error):
        engine().generate(mutator(market_frame()))


def test_non_dataframe_and_empty_data_are_rejected():
    with pytest.raises(TypeError, match="DataFrame"):
        engine().generate([])
    with pytest.raises(ValueError, match="cannot be empty"):
        engine().generate(market_frame().iloc[:0])
