"""Causal features and deterministic entry signals for Kraken V2 Round 2."""

import copy
import math

import numpy as np
import pandas as pd

try:
    from kraken_ai_driven_v2_hybrid_discovery_round_2 import (
        HYPOTHESIS_ORDER,
        ROUND_2_CONFIGURATION_LOCK,
        ROUND_2_HYPOTHESES,
    )
except ImportError:  # pragma: no cover - package import compatibility
    from .kraken_ai_driven_v2_hybrid_discovery_round_2 import (
        HYPOTHESIS_ORDER,
        ROUND_2_CONFIGURATION_LOCK,
        ROUND_2_HYPOTHESES,
    )


REQUIRED_OHLCV_COLUMNS = ("Open", "High", "Low", "Close", "Volume")
DAILY_STEP = pd.Timedelta(days=1)
FEATURE_PREFIX = "KRAKEN_AI_V2_R2_"


def _feature(suffix):
    return f"{FEATURE_PREFIX}{suffix}"


FEATURE_COLUMNS = (
    _feature("PREVIOUS_CLOSE"),
    _feature("PRIOR_HIGH_1"),
    _feature("PRIOR_HIGH_2"),
    _feature("PRIOR_HIGH_3"),
    _feature("PRIOR_CLOSE_MAX_40"),
    _feature("DRAWDOWN_FROM_PRIOR_HIGH_ATR"),
    _feature("ONE_BAR_PRICE_CHANGE_TO_PRIOR_ATR"),
    _feature("TRUE_RANGE"),
    _feature("ATR_14"),
    _feature("PRIOR_ATR_14"),
    _feature("TR_TO_PRIOR_ATR"),
    _feature("PRIOR_ATR_MEDIAN_60"),
    _feature("ATR_TO_PRIOR_MEDIAN_60"),
    _feature("PRIOR_VOLUME_MEDIAN_30"),
    _feature("VOLUME_RATIO"),
    _feature("CLOSE_LOCATION"),
    _feature("EMA_20_PRIOR"),
    _feature("EMA_50_PRIOR"),
    _feature("EMA_200_PRIOR"),
    _feature("EMA_50_SLOPE_20"),
    _feature("ADX_14_PRIOR"),
    _feature("MACD_HISTOGRAM"),
    _feature("MACD_HISTOGRAM_PRIOR"),
    _feature("DONCHIAN_PRIOR_CLOSE_HIGH_55"),
    _feature("PRIOR_CLOSE_LOW_10"),
)

FAMILY_ORDER = (
    "CAPITULATION_RECOVERY",
    "VOLATILITY_BREAKOUT",
    "TREND_PULLBACK_CONTINUATION",
)
FAMILY_COLUMN = _feature("FAMILY_ID")
HYPOTHESIS_COLUMN = _feature("HYPOTHESIS_ID")
FEATURES_AVAILABLE_COLUMN = _feature("FEATURES_AVAILABLE")
REGIME_CONDITION_COLUMN = _feature("REGIME_CONDITION")
SETUP_CONDITION_COLUMN = _feature("SETUP_CONDITION")
SIGNAL_CONDITION_COLUMN = _feature("SIGNAL_CONDITION")
STATE_BEFORE_COLUMN = _feature("STATE_BEFORE")
STATE_AFTER_COLUMN = _feature("STATE_AFTER")
TRANSITION_COLUMN = _feature("TRANSITION")
ACTION_INTENT_COLUMN = _feature("ACTION_INTENT")
SETUP_TIMESTAMP_COLUMN = _feature("SETUP_TIMESTAMP")
SETUP_LOW_COLUMN = _feature("SETUP_LOW")
SIGNAL_ATR_COLUMN = _feature("SIGNAL_PRIOR_ATR")
TARGET_ANCHOR_COLUMN = _feature("TARGET_ANCHOR")
SETUP_LEVEL_COLUMN = _feature("SETUP_LEVEL")
STATE_AGE_COLUMN = _feature("STATE_AGE")
RETEST_OBSERVED_COLUMN = _feature("RETEST_OBSERVED")
MACD_NONPOSITIVE_SEEN_COLUMN = _feature("MACD_NONPOSITIVE_SEEN")
SIGNAL_EVIDENCE_COLUMNS = (
    FAMILY_COLUMN,
    HYPOTHESIS_COLUMN,
    FEATURES_AVAILABLE_COLUMN,
    REGIME_CONDITION_COLUMN,
    SETUP_CONDITION_COLUMN,
    SIGNAL_CONDITION_COLUMN,
    STATE_BEFORE_COLUMN,
    STATE_AFTER_COLUMN,
    TRANSITION_COLUMN,
    ACTION_INTENT_COLUMN,
    SETUP_TIMESTAMP_COLUMN,
    SETUP_LOW_COLUMN,
    SIGNAL_ATR_COLUMN,
    TARGET_ANCHOR_COLUMN,
    SETUP_LEVEL_COLUMN,
    STATE_AGE_COLUMN,
    RETEST_OBSERVED_COLUMN,
    MACD_NONPOSITIVE_SEEN_COLUMN,
)

STATE_FLAT = "FLAT"
STATE_ARMED = "ARMED"
STATE_BREAKOUT_ARMED = "BREAKOUT_ARMED"
STATE_RETEST_OBSERVED = "RETEST_OBSERVED"
INTENT_NONE = "NONE"
ENTER_NEXT_OPEN = "ENTER_NEXT_OPEN"
FEATURE_COMPONENT_ID = "kraken-ai-v2-round-2-causal-features-v1"
SIGNAL_COMPONENT_ID = "kraken-ai-v2-round-2-causal-signals-v1"

_HYPOTHESES_BY_FAMILY = {
    item["family_id"]: copy.deepcopy(item) for item in ROUND_2_HYPOTHESES
}


def _validated_continuous_daily_frame(data):
    if not isinstance(data, pd.DataFrame):
        raise TypeError("Round 2 causal data must be a pandas DataFrame.")
    if data.empty:
        raise ValueError("Round 2 causal data cannot be empty.")
    if tuple(data.columns) != REQUIRED_OHLCV_COLUMNS:
        raise ValueError(
            "Round 2 causal data must contain exact ordered OHLCV columns: "
            f"{REQUIRED_OHLCV_COLUMNS}."
        )
    if not isinstance(data.index, pd.DatetimeIndex):
        raise TypeError("Round 2 causal data must use a DatetimeIndex.")
    if data.index.tz is None:
        raise ValueError("Round 2 causal timestamps must be timezone-aware.")
    if not data.index.is_monotonic_increasing:
        raise ValueError("Round 2 causal timestamps must increase.")
    if data.index.has_duplicates:
        raise ValueError("Round 2 causal timestamps must be unique.")

    frame = data.copy(deep=True)
    frame.index = frame.index.tz_convert("UTC")
    if any(
        timestamp.hour
        or timestamp.minute
        or timestamp.second
        or timestamp.microsecond
        or timestamp.nanosecond
        for timestamp in frame.index
    ):
        raise ValueError("Round 2 causal timestamps must align to UTC midnight.")
    if len(frame.index) > 1:
        deltas = frame.index[1:] - frame.index[:-1]
        if any(delta != DAILY_STEP for delta in deltas):
            raise ValueError(
                "Round 2 causal features require one continuous daily segment."
            )

    numeric = frame.loc[:, REQUIRED_OHLCV_COLUMNS].apply(
        pd.to_numeric, errors="coerce"
    )
    values = numeric.to_numpy(dtype=float)
    if numeric.isna().any().any() or not np.isfinite(values).all():
        raise ValueError("Round 2 OHLCV values must be finite numeric data.")
    if (values[:, :4] <= 0.0).any() or (values[:, 4] < 0.0).any():
        raise ValueError("Round 2 prices must be positive and volume nonnegative.")
    open_values, high_values, low_values, close_values = (
        values[:, 0],
        values[:, 1],
        values[:, 2],
        values[:, 3],
    )
    if (
        (high_values < open_values).any()
        or (high_values < close_values).any()
        or (low_values > open_values).any()
        or (low_values > close_values).any()
        or (high_values < low_values).any()
    ):
        raise ValueError("Round 2 OHLC price geometry is invalid.")
    return frame, numeric.astype(float)


def _wilder_atr(high, low, close, period=14):
    previous_close = close.shift(1)
    true_range = pd.concat(
        (
            high.sub(low),
            high.sub(previous_close).abs(),
            low.sub(previous_close).abs(),
        ),
        axis=1,
    ).max(axis=1, skipna=True)
    atr = true_range.ewm(
        alpha=1.0 / period,
        adjust=False,
        min_periods=period,
    ).mean()
    return true_range, atr


def _adx(high, low, close, period=14):
    previous_close = close.shift(1)
    high_change = high.diff()
    low_change = -low.diff()
    positive_dm = high_change.where(
        (high_change > low_change) & (high_change > 0.0), 0.0
    )
    negative_dm = low_change.where(
        (low_change > high_change) & (low_change > 0.0), 0.0
    )
    true_range = pd.concat(
        (
            high.sub(low),
            high.sub(previous_close).abs(),
            low.sub(previous_close).abs(),
        ),
        axis=1,
    ).max(axis=1, skipna=True)
    smoothed_tr = true_range.ewm(
        alpha=1.0 / period, adjust=False, min_periods=period
    ).mean()
    smoothed_positive = positive_dm.ewm(
        alpha=1.0 / period, adjust=False, min_periods=period
    ).mean()
    smoothed_negative = negative_dm.ewm(
        alpha=1.0 / period, adjust=False, min_periods=period
    ).mean()
    positive_di = 100.0 * smoothed_positive.div(smoothed_tr)
    negative_di = 100.0 * smoothed_negative.div(smoothed_tr)
    denominator = positive_di.add(negative_di)
    dx = 100.0 * positive_di.sub(negative_di).abs().div(
        denominator.where(denominator != 0.0)
    )
    dx = dx.where(denominator != 0.0, 0.0)
    return dx.ewm(
        alpha=1.0 / period, adjust=False, min_periods=period
    ).mean()


class KrakenAIDrivenV2Round2CausalFeatureEngine:
    """Generate the Round 2 feature frame for one continuous segment."""

    def configuration(self):
        return {
            "component_id": FEATURE_COMPONENT_ID,
            "round_2_configuration_sha256": ROUND_2_CONFIGURATION_LOCK.sha256,
            "feature_columns": list(FEATURE_COLUMNS),
            "completed_daily_bar_only": True,
            "rolling_baseline_current_bar_included": False,
            "ema_and_adx_decision_value": "PRIOR_COMPLETED_BAR",
            "macd_decision_value": "CURRENT_COMPLETED_BAR",
            "atr_formula": "WILDER_EWM_ALPHA_1_OVER_14",
            "adx_formula": "WILDER_DI_DX_EWM_ALPHA_1_OVER_14",
            "macd_formula": "EMA_12_MINUS_EMA_26_SIGNAL_EMA_9",
            "volume_baseline_bars": 30,
            "gap_policy": "SPLIT_BEFORE_GENERATION",
            "signal_emitted": False,
            "execution_implemented": False,
            "dataset_opened": False,
        }

    def generate(self, data):
        frame, numeric = _validated_continuous_daily_frame(data)
        high = numeric["High"]
        low = numeric["Low"]
        close = numeric["Close"]
        volume = numeric["Volume"]

        previous_close = close.shift(1)
        prior_high_1 = high.shift(1)
        prior_high_2 = high.shift(1).rolling(2, min_periods=2).max()
        prior_high_3 = high.shift(1).rolling(3, min_periods=3).max()
        prior_close_max_40 = close.shift(1).rolling(40, min_periods=40).max()

        true_range, atr_14 = _wilder_atr(high, low, close, period=14)
        prior_atr_14 = atr_14.shift(1)
        positive_prior_atr = prior_atr_14.where(prior_atr_14 > 0.0)
        drawdown_from_prior_high_atr = close.sub(prior_close_max_40).div(
            positive_prior_atr
        )
        one_bar_price_change_to_prior_atr = close.sub(previous_close).div(
            positive_prior_atr
        )
        tr_to_prior_atr = true_range.div(positive_prior_atr)
        prior_atr_median_60 = atr_14.shift(1).rolling(60, min_periods=60).median()
        atr_to_prior_median_60 = atr_14.div(
            prior_atr_median_60.where(prior_atr_median_60 > 0.0)
        )

        prior_volume_median_30 = volume.shift(1).rolling(
            30, min_periods=30
        ).median()
        volume_ratio = volume.div(
            prior_volume_median_30.where(prior_volume_median_30 > 0.0)
        )
        completed_range = high.sub(low)
        close_location = close.sub(low).div(
            completed_range.where(completed_range > 0.0)
        )

        ema_20_prior = close.ewm(
            span=20, adjust=False, min_periods=20
        ).mean().shift(1)
        ema_50_prior = close.ewm(
            span=50, adjust=False, min_periods=50
        ).mean().shift(1)
        ema_200_prior = close.ewm(
            span=200, adjust=False, min_periods=200
        ).mean().shift(1)
        ema_50_slope_20 = ema_50_prior.div(ema_50_prior.shift(20)).sub(1.0)
        adx_14_prior = _adx(high, low, close, period=14).shift(1)

        macd_fast = close.ewm(span=12, adjust=False, min_periods=12).mean()
        macd_slow = close.ewm(span=26, adjust=False, min_periods=26).mean()
        macd_line = macd_fast.sub(macd_slow)
        macd_signal = macd_line.ewm(
            span=9, adjust=False, min_periods=9
        ).mean()
        macd_histogram = macd_line.sub(macd_signal)
        macd_histogram_prior = macd_histogram.shift(1)

        donchian_prior_high_55 = close.shift(1).rolling(
            55, min_periods=55
        ).max()
        prior_close_low_10 = close.shift(1).rolling(10, min_periods=10).min()

        values = (
            previous_close,
            prior_high_1,
            prior_high_2,
            prior_high_3,
            prior_close_max_40,
            drawdown_from_prior_high_atr,
            one_bar_price_change_to_prior_atr,
            true_range,
            atr_14,
            prior_atr_14,
            tr_to_prior_atr,
            prior_atr_median_60,
            atr_to_prior_median_60,
            prior_volume_median_30,
            volume_ratio,
            close_location,
            ema_20_prior,
            ema_50_prior,
            ema_200_prior,
            ema_50_slope_20,
            adx_14_prior,
            macd_histogram,
            macd_histogram_prior,
            donchian_prior_high_55,
            prior_close_low_10,
        )
        result = frame.copy(deep=True)
        for column, value in zip(FEATURE_COLUMNS, values):
            result[column] = value
        return result


def _finite_row_values(row, columns):
    for column in columns:
        value = row[column]
        if isinstance(value, bool):
            return False
        try:
            value = float(value)
        except (TypeError, ValueError):
            return False
        if not math.isfinite(value):
            return False
    return True


def _validated_feature_frame(data):
    if not isinstance(data, pd.DataFrame):
        raise TypeError("Round 2 signal features must be a pandas DataFrame.")
    missing = [
        column
        for column in (*REQUIRED_OHLCV_COLUMNS, *FEATURE_COLUMNS)
        if column not in data.columns
    ]
    if missing:
        raise ValueError(f"Round 2 signal feature columns are missing: {missing}.")
    _validated_continuous_daily_frame(data.loc[:, REQUIRED_OHLCV_COLUMNS])
    return data.copy(deep=True)


class KrakenAIDrivenV2Round2SignalEngine:
    """Emit Round 2 next-open research intents; no position or fill exists."""

    def __init__(self):
        if tuple(_HYPOTHESES_BY_FAMILY) != FAMILY_ORDER:
            raise RuntimeError("Round 2 signal family order mismatch.")
        if tuple(item["hypothesis_id"] for item in ROUND_2_HYPOTHESES) != (
            HYPOTHESIS_ORDER
        ):
            raise RuntimeError("Round 2 signal hypothesis order mismatch.")
        self.feature_engine = KrakenAIDrivenV2Round2CausalFeatureEngine()

    def configuration(self):
        return {
            "component_id": SIGNAL_COMPONENT_ID,
            "round_2_configuration_sha256": ROUND_2_CONFIGURATION_LOCK.sha256,
            "family_order": list(FAMILY_ORDER),
            "asset_scopes": {
                family: list(_HYPOTHESES_BY_FAMILY[family]["asset_scope"])
                for family in FAMILY_ORDER
            },
            "action_intent": ENTER_NEXT_OPEN,
            "capitulation_minimum_post_setup_bars": 2,
            "capitulation_maximum_confirmation_delay_bars": 7,
            "breakout_retest_window_bars": 5,
            "breakout_confirmation_after_retest_required": True,
            "trend_pullback_age_range_bars": [2, 5],
            "trend_macd_zero_cross_required": True,
            "state_role": "ENTRY_SIGNAL_ONLY_NOT_POSITION",
            "position_sizing": False,
            "fill_execution": False,
            "performance_evaluation": False,
            "future_bar_access": False,
            "dataset_opened": False,
        }

    def generate(self, family_id, data):
        if family_id not in FAMILY_ORDER:
            raise ValueError(f"Unknown Round 2 family: {family_id}.")
        features = self.feature_engine.generate(data)
        return self.generate_from_features(family_id, features)

    def generate_all(self, data):
        features = self.feature_engine.generate(data)
        return {
            family_id: self.generate_from_features(family_id, features)
            for family_id in FAMILY_ORDER
        }

    def generate_from_features(self, family_id, data):
        if family_id not in FAMILY_ORDER:
            raise ValueError(f"Unknown Round 2 family: {family_id}.")
        features = _validated_feature_frame(data)
        if family_id == "CAPITULATION_RECOVERY":
            return self._capitulation(features)
        if family_id == "VOLATILITY_BREAKOUT":
            return self._breakout_retest(features)
        return self._trend_macd(features)

    @staticmethod
    def _base_evidence(features, family_id):
        result = features.copy(deep=True)
        result[FAMILY_COLUMN] = family_id
        result[HYPOTHESIS_COLUMN] = _HYPOTHESES_BY_FAMILY[family_id][
            "hypothesis_id"
        ]
        return result

    @staticmethod
    def _finish(result, evidence):
        for column, values in zip(SIGNAL_EVIDENCE_COLUMNS[2:], evidence):
            result[column] = values
        return result

    @staticmethod
    def _append(
        evidence,
        *,
        available,
        regime,
        setup,
        signal,
        state_before,
        state_after,
        transition,
        intent,
        setup_timestamp,
        setup_low,
        signal_atr,
        target_anchor=math.nan,
        setup_level=math.nan,
        state_age=-1,
        retest_observed=False,
        macd_nonpositive_seen=False,
    ):
        row = (
            bool(available),
            bool(regime),
            bool(setup),
            bool(signal),
            state_before,
            state_after,
            transition,
            intent,
            setup_timestamp,
            setup_low,
            signal_atr,
            target_anchor,
            setup_level,
            state_age,
            bool(retest_observed),
            bool(macd_nonpositive_seen),
        )
        for bucket, value in zip(evidence, row):
            bucket.append(value)

    def _capitulation(self, features):
        family = "CAPITULATION_RECOVERY"
        result = self._base_evidence(features, family)
        event_columns = (
            _feature("DRAWDOWN_FROM_PRIOR_HIGH_ATR"),
            _feature("ONE_BAR_PRICE_CHANGE_TO_PRIOR_ATR"),
            _feature("TR_TO_PRIOR_ATR"),
            _feature("VOLUME_RATIO"),
            _feature("CLOSE_LOCATION"),
            _feature("PRIOR_ATR_14"),
            "Close",
            "Low",
        )
        confirmation_columns = (
            _feature("VOLUME_RATIO"),
            _feature("CLOSE_LOCATION"),
            _feature("PRIOR_HIGH_2"),
            _feature("PRIOR_ATR_14"),
            "Close",
            "Low",
        )
        state = STATE_FLAT
        age = -1
        anchor_timestamp = None
        anchor_low = math.nan
        evidence = [[] for _ in range(len(SIGNAL_EVIDENCE_COLUMNS) - 2)]

        for timestamp, row in result.iterrows():
            before = state
            event_available = _finite_row_values(row, event_columns)
            event = event_available and (
                float(row[_feature("DRAWDOWN_FROM_PRIOR_HIGH_ATR")]) <= -6.0
                and float(row[_feature("ONE_BAR_PRICE_CHANGE_TO_PRIOR_ATR")])
                <= -1.5
                and float(row[_feature("TR_TO_PRIOR_ATR")]) >= 1.75
                and float(row[_feature("VOLUME_RATIO")]) >= 1.5
                and float(row[_feature("CLOSE_LOCATION")]) <= 0.35
            )
            confirmation_available = _finite_row_values(row, confirmation_columns)
            confirmation = False
            transition = "FLAT_WAIT"
            intent = INTENT_NONE
            available = event_available
            observed_timestamp = None
            observed_low = math.nan
            signal_atr = math.nan

            if state == STATE_FLAT:
                if event:
                    state = STATE_ARMED
                    age = 0
                    anchor_timestamp = timestamp
                    anchor_low = float(row["Low"])
                    transition = "CAPITULATION_ARMED"
                    observed_timestamp = anchor_timestamp
                    observed_low = anchor_low
                elif not event_available:
                    transition = "FEATURES_UNAVAILABLE"
            else:
                age += 1
                available = confirmation_available
                observed_timestamp = anchor_timestamp
                observed_low = anchor_low
                if event:
                    state = STATE_ARMED
                    age = 0
                    anchor_timestamp = timestamp
                    anchor_low = float(row["Low"])
                    transition = "CAPITULATION_REARMED"
                    observed_timestamp = anchor_timestamp
                    observed_low = anchor_low
                elif not confirmation_available:
                    state = STATE_FLAT
                    transition = "CAPITULATION_EXPIRED_FEATURES_UNAVAILABLE"
                else:
                    current_low = float(row["Low"])
                    observed_low = min(anchor_low, current_low)
                    if float(row["Close"]) < anchor_low:
                        state = STATE_FLAT
                        transition = "CAPITULATION_STRUCTURAL_INVALIDATION"
                    elif age > 7:
                        state = STATE_FLAT
                        transition = "CAPITULATION_EXPIRED"
                    else:
                        confirmation = age >= 2 and (
                            float(row[_feature("CLOSE_LOCATION")]) >= 0.6
                            and float(row["Close"])
                            > float(row[_feature("PRIOR_HIGH_2")])
                            and float(row[_feature("VOLUME_RATIO")]) >= 0.8
                        )
                        anchor_low = observed_low
                        if confirmation:
                            state = STATE_FLAT
                            transition = "CAPITULATION_CONFIRMATION"
                            intent = ENTER_NEXT_OPEN
                            signal_atr = float(row[_feature("PRIOR_ATR_14")])
                        elif age < 2:
                            transition = "CAPITULATION_STABILIZING"
                        else:
                            transition = "CAPITULATION_WAIT"
                if state == STATE_FLAT:
                    age = -1

            self._append(
                evidence,
                available=available,
                regime=event,
                setup=event,
                signal=confirmation,
                state_before=before,
                state_after=state,
                transition=transition,
                intent=intent,
                setup_timestamp=observed_timestamp,
                setup_low=observed_low,
                signal_atr=signal_atr,
                state_age=age,
            )
        return self._finish(result, evidence)

    def _breakout_retest(self, features):
        family = "VOLATILITY_BREAKOUT"
        result = self._base_evidence(features, family)
        setup_columns = (
            _feature("ATR_TO_PRIOR_MEDIAN_60"),
            _feature("ADX_14_PRIOR"),
            _feature("DONCHIAN_PRIOR_CLOSE_HIGH_55"),
            _feature("VOLUME_RATIO"),
            _feature("CLOSE_LOCATION"),
            _feature("PRIOR_ATR_14"),
            "Close",
            "Low",
        )
        active_columns = (
            _feature("PRIOR_ATR_14"),
            _feature("PRIOR_HIGH_1"),
            _feature("VOLUME_RATIO"),
            "Close",
            "Low",
        )
        state = STATE_FLAT
        age = -1
        anchor_timestamp = None
        anchor_low = math.nan
        breakout_level = math.nan
        setup_atr = math.nan
        evidence = [[] for _ in range(len(SIGNAL_EVIDENCE_COLUMNS) - 2)]

        for timestamp, row in result.iterrows():
            before = state
            setup_available = _finite_row_values(row, setup_columns)
            regime = setup_available and (
                float(row[_feature("ATR_TO_PRIOR_MEDIAN_60")]) >= 1.1
                and float(row[_feature("ADX_14_PRIOR")]) >= 20.0
            )
            setup = setup_available and regime and (
                float(row["Close"])
                > float(row[_feature("DONCHIAN_PRIOR_CLOSE_HIGH_55")])
                and float(row[_feature("VOLUME_RATIO")]) >= 1.25
                and float(row[_feature("CLOSE_LOCATION")]) >= 0.7
            )
            active_available = _finite_row_values(row, active_columns)
            available = setup_available if state == STATE_FLAT else active_available
            transition = "BREAKOUT_WAIT"
            intent = INTENT_NONE
            signal = False
            observed_timestamp = None
            observed_low = math.nan
            observed_level = math.nan
            signal_atr = math.nan
            row_retest_observed = False

            if state == STATE_FLAT:
                if setup:
                    state = STATE_BREAKOUT_ARMED
                    age = 0
                    anchor_timestamp = timestamp
                    anchor_low = float(row["Low"])
                    breakout_level = float(
                        row[_feature("DONCHIAN_PRIOR_CLOSE_HIGH_55")]
                    )
                    setup_atr = float(row[_feature("PRIOR_ATR_14")])
                    transition = "BREAKOUT_SETUP_ARMED"
                    observed_timestamp = anchor_timestamp
                    observed_low = anchor_low
                    observed_level = breakout_level
                elif not setup_available:
                    transition = "FEATURES_UNAVAILABLE"
            else:
                age += 1
                observed_timestamp = anchor_timestamp
                observed_low = anchor_low
                observed_level = breakout_level
                row_retest_observed = state == STATE_RETEST_OBSERVED
                if not active_available:
                    state = STATE_FLAT
                    transition = "BREAKOUT_RETEST_EXPIRED_FEATURES_UNAVAILABLE"
                elif float(row["Close"]) < breakout_level:
                    state = STATE_FLAT
                    transition = "BREAKOUT_LEVEL_FAILED"
                elif age > 5:
                    state = STATE_FLAT
                    transition = "BREAKOUT_RETEST_EXPIRED"
                elif state == STATE_BREAKOUT_ARMED:
                    retest = (
                        float(row["Low"]) <= breakout_level + 0.25 * setup_atr
                        and float(row["Close"]) >= breakout_level
                    )
                    if retest:
                        state = STATE_RETEST_OBSERVED
                        anchor_low = float(row["Low"])
                        observed_low = anchor_low
                        row_retest_observed = True
                        transition = "BREAKOUT_RETEST_OBSERVED"
                    else:
                        transition = "BREAKOUT_RETEST_WAIT"
                else:
                    anchor_low = min(anchor_low, float(row["Low"]))
                    observed_low = anchor_low
                    row_retest_observed = True
                    signal = (
                        float(row["Close"])
                        > float(row[_feature("PRIOR_HIGH_1")])
                        and float(row[_feature("VOLUME_RATIO")]) >= 1.0
                    )
                    if signal:
                        state = STATE_FLAT
                        transition = "BREAKOUT_RETEST_CONFIRMATION"
                        intent = ENTER_NEXT_OPEN
                        signal_atr = float(row[_feature("PRIOR_ATR_14")])
                    else:
                        transition = "BREAKOUT_CONFIRMATION_WAIT"
                if state == STATE_FLAT:
                    age = -1

            self._append(
                evidence,
                available=available,
                regime=regime,
                setup=setup,
                signal=signal,
                state_before=before,
                state_after=state,
                transition=transition,
                intent=intent,
                setup_timestamp=observed_timestamp,
                setup_low=observed_low,
                signal_atr=signal_atr,
                setup_level=observed_level,
                state_age=age,
                retest_observed=row_retest_observed,
            )
        return self._finish(result, evidence)

    def _trend_macd(self, features):
        family = "TREND_PULLBACK_CONTINUATION"
        result = self._base_evidence(features, family)
        regime_columns = (
            _feature("EMA_50_PRIOR"),
            _feature("EMA_200_PRIOR"),
            _feature("EMA_50_SLOPE_20"),
            _feature("ADX_14_PRIOR"),
        )
        setup_columns = (
            *regime_columns,
            _feature("EMA_20_PRIOR"),
            _feature("PRIOR_ATR_14"),
            _feature("VOLUME_RATIO"),
            _feature("MACD_HISTOGRAM"),
            "Low",
            "Close",
        )
        confirmation_columns = (
            *regime_columns,
            _feature("EMA_50_PRIOR"),
            _feature("PRIOR_ATR_14"),
            _feature("VOLUME_RATIO"),
            _feature("MACD_HISTOGRAM"),
            _feature("MACD_HISTOGRAM_PRIOR"),
            _feature("PRIOR_HIGH_3"),
            "Low",
            "Close",
        )
        state = STATE_FLAT
        age = -1
        anchor_timestamp = None
        anchor_low = math.nan
        macd_nonpositive_seen = False
        evidence = [[] for _ in range(len(SIGNAL_EVIDENCE_COLUMNS) - 2)]

        for timestamp, row in result.iterrows():
            before = state
            regime_available = _finite_row_values(row, regime_columns)
            regime = regime_available and (
                float(row[_feature("EMA_50_PRIOR")])
                > float(row[_feature("EMA_200_PRIOR")])
                and float(row[_feature("EMA_50_SLOPE_20")]) > 0.0
                and float(row[_feature("ADX_14_PRIOR")]) >= 20.0
            )
            setup_available = _finite_row_values(row, setup_columns)
            prior_atr = (
                float(row[_feature("PRIOR_ATR_14")])
                if setup_available
                else math.nan
            )
            distance = (
                abs(float(row["Low"]) - float(row[_feature("EMA_20_PRIOR")]))
                / prior_atr
                if setup_available and prior_atr > 0.0
                else math.inf
            )
            setup = setup_available and regime and (
                distance <= 0.5
                and float(row["Close"]) > float(row[_feature("EMA_50_PRIOR")])
                and float(row[_feature("VOLUME_RATIO")]) <= 1.0
            )
            confirmation_available = _finite_row_values(
                row, confirmation_columns
            )
            available = setup_available if state == STATE_FLAT else confirmation_available
            transition = "TREND_PULLBACK_WAIT"
            intent = INTENT_NONE
            signal = False
            observed_timestamp = None
            observed_low = math.nan
            signal_atr = math.nan
            row_macd_seen = macd_nonpositive_seen

            if state == STATE_FLAT:
                if setup:
                    state = STATE_ARMED
                    age = 0
                    anchor_timestamp = timestamp
                    anchor_low = float(row["Low"])
                    macd_nonpositive_seen = (
                        float(row[_feature("MACD_HISTOGRAM")]) <= 0.0
                    )
                    row_macd_seen = macd_nonpositive_seen
                    transition = "TREND_PULLBACK_ARMED"
                    observed_timestamp = anchor_timestamp
                    observed_low = anchor_low
                elif not setup_available:
                    transition = "FEATURES_UNAVAILABLE"
            else:
                age += 1
                observed_timestamp = anchor_timestamp
                observed_low = anchor_low
                if not confirmation_available:
                    state = STATE_FLAT
                    transition = "TREND_PULLBACK_EXPIRED_FEATURES_UNAVAILABLE"
                else:
                    anchor_low = min(anchor_low, float(row["Low"]))
                    observed_low = anchor_low
                    current_macd = float(row[_feature("MACD_HISTOGRAM")])
                    prior_macd = float(row[_feature("MACD_HISTOGRAM_PRIOR")])
                    if current_macd <= 0.0:
                        macd_nonpositive_seen = True
                    row_macd_seen = macd_nonpositive_seen
                    if (
                        not regime
                        or float(row["Close"])
                        <= float(row[_feature("EMA_50_PRIOR")])
                    ):
                        state = STATE_FLAT
                        transition = "TREND_PULLBACK_STRUCTURAL_INVALIDATION"
                    elif age > 5:
                        state = STATE_FLAT
                        transition = "TREND_PULLBACK_EXPIRED"
                    else:
                        signal = (
                            age >= 2
                            and macd_nonpositive_seen
                            and prior_macd <= 0.0
                            and current_macd > 0.0
                            and float(row["Close"])
                            > float(row[_feature("PRIOR_HIGH_3")])
                            and float(row[_feature("VOLUME_RATIO")]) >= 1.0
                        )
                        if signal:
                            state = STATE_FLAT
                            transition = "TREND_MACD_RESUMPTION_CONFIRMATION"
                            intent = ENTER_NEXT_OPEN
                            signal_atr = float(row[_feature("PRIOR_ATR_14")])
                        else:
                            transition = "TREND_PULLBACK_BUILDING"
                if state == STATE_FLAT:
                    age = -1
                    macd_nonpositive_seen = False

            self._append(
                evidence,
                available=available,
                regime=regime,
                setup=setup,
                signal=signal,
                state_before=before,
                state_after=state,
                transition=transition,
                intent=intent,
                setup_timestamp=observed_timestamp,
                setup_low=observed_low,
                signal_atr=signal_atr,
                state_age=age,
                macd_nonpositive_seen=row_macd_seen,
            )
        return self._finish(result, evidence)
