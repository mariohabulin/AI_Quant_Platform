"""Causal features and deterministic entry signals for Kraken V2 Round 1."""

import copy
import math

import numpy as np
import pandas as pd

try:
    from kraken_ai_driven_v2_hybrid_discovery_round_1 import (
        HYPOTHESIS_ORDER,
        ROUND_1_CONFIGURATION_LOCK,
        ROUND_1_HYPOTHESES,
    )
except ImportError:  # pragma: no cover - package import compatibility
    from .kraken_ai_driven_v2_hybrid_discovery_round_1 import (
        HYPOTHESIS_ORDER,
        ROUND_1_CONFIGURATION_LOCK,
        ROUND_1_HYPOTHESES,
    )


REQUIRED_OHLCV_COLUMNS = ("Open", "High", "Low", "Close", "Volume")
DAILY_STEP = pd.Timedelta(days=1)
FEATURE_PREFIX = "KRAKEN_AI_V2_R1_"


def _feature(suffix):
    return f"{FEATURE_PREFIX}{suffix}"


FEATURE_COLUMNS = (
    _feature("PREVIOUS_CLOSE"),
    _feature("PRIOR_HIGH_1"),
    _feature("CLOSE_RETURN_1"),
    _feature("PRIOR_CLOSE_MAX_60"),
    _feature("DRAWDOWN_60"),
    _feature("TRUE_RANGE"),
    _feature("ATR_14"),
    _feature("PRIOR_ATR_14"),
    _feature("TR_TO_PRIOR_ATR"),
    _feature("PRIOR_ATR_MEDIAN_60"),
    _feature("ATR_TO_PRIOR_MEDIAN_60"),
    _feature("PRIOR_ATR_MEDIAN_120"),
    _feature("ATR_TO_PRIOR_MEDIAN_120"),
    _feature("PRIOR_VOLUME_MEDIAN_30"),
    _feature("VOLUME_RATIO"),
    _feature("CLOSE_LOCATION"),
    _feature("EMA_20_PRIOR"),
    _feature("EMA_50_PRIOR"),
    _feature("EMA_200_PRIOR"),
    _feature("EMA_50_SLOPE_20"),
    _feature("ADX_14_PRIOR"),
    _feature("BOLLINGER_MID_20_PRIOR"),
    _feature("BOLLINGER_LOWER_20_PRIOR"),
    _feature("BOLLINGER_UPPER_20_PRIOR"),
    _feature("BOLLINGER_WIDTH_20_PRIOR"),
    _feature("PRIOR_BOLLINGER_WIDTH_MEDIAN_120"),
    _feature("BAND_WIDTH_TO_PRIOR_MEDIAN_120"),
    _feature("RSI_14"),
    _feature("STOCHASTIC_K_14"),
    _feature("STOCHASTIC_D_14_3"),
    _feature("DONCHIAN_PRIOR_CLOSE_HIGH_55"),
    _feature("PRIOR_CLOSE_LOW_10"),
)

FAMILY_ORDER = (
    "CAPITULATION_RECOVERY",
    "TREND_PULLBACK_CONTINUATION",
    "RANGE_MEAN_REVERSION",
    "VOLATILITY_BREAKOUT",
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
)

STATE_FLAT = "FLAT"
STATE_ARMED = "ARMED"
INTENT_NONE = "NONE"
ENTER_NEXT_OPEN = "ENTER_NEXT_OPEN"
FEATURE_COMPONENT_ID = "kraken-ai-v2-round-1-causal-features-v1"
SIGNAL_COMPONENT_ID = "kraken-ai-v2-round-1-causal-signals-v1"

_HYPOTHESES_BY_FAMILY = {
    item["family_id"]: copy.deepcopy(item) for item in ROUND_1_HYPOTHESES
}


def _validated_continuous_daily_frame(data):
    if not isinstance(data, pd.DataFrame):
        raise TypeError("Round 1 causal data must be a pandas DataFrame.")
    if data.empty:
        raise ValueError("Round 1 causal data cannot be empty.")
    if tuple(data.columns) != REQUIRED_OHLCV_COLUMNS:
        raise ValueError(
            "Round 1 causal data must contain exact ordered OHLCV columns: "
            f"{REQUIRED_OHLCV_COLUMNS}."
        )
    if not isinstance(data.index, pd.DatetimeIndex):
        raise TypeError("Round 1 causal data must use a DatetimeIndex.")
    if data.index.tz is None:
        raise ValueError("Round 1 causal timestamps must be timezone-aware.")
    if not data.index.is_monotonic_increasing:
        raise ValueError("Round 1 causal timestamps must increase.")
    if data.index.has_duplicates:
        raise ValueError("Round 1 causal timestamps must be unique.")

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
        raise ValueError("Round 1 causal timestamps must align to UTC midnight.")
    if len(frame.index) > 1:
        deltas = frame.index[1:] - frame.index[:-1]
        if any(delta != DAILY_STEP for delta in deltas):
            raise ValueError(
                "Round 1 causal features require one continuous daily segment."
            )

    numeric = frame.loc[:, REQUIRED_OHLCV_COLUMNS].apply(
        pd.to_numeric, errors="coerce"
    )
    values = numeric.to_numpy(dtype=float)
    if numeric.isna().any().any() or not np.isfinite(values).all():
        raise ValueError("Round 1 OHLCV values must be finite numeric data.")
    if (values[:, :4] <= 0.0).any() or (values[:, 4] < 0.0).any():
        raise ValueError("Round 1 prices must be positive and volume nonnegative.")
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
        raise ValueError("Round 1 OHLC price geometry is invalid.")
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


def _rsi(close, period=14):
    change = close.diff()
    gains = change.clip(lower=0.0)
    losses = -change.clip(upper=0.0)
    average_gain = gains.rolling(period, min_periods=period).mean()
    average_loss = losses.rolling(period, min_periods=period).mean()
    relative_strength = average_gain.div(average_loss.where(average_loss != 0.0))
    result = 100.0 - 100.0 / (1.0 + relative_strength)
    result = result.where(average_loss != 0.0, 100.0)
    result = result.where(~((average_gain == 0.0) & (average_loss == 0.0)), 50.0)
    return result


class KrakenAIDrivenV2Round1CausalFeatureEngine:
    """Generate the complete shared feature frame for one continuous segment."""

    def configuration(self):
        return {
            "component_id": FEATURE_COMPONENT_ID,
            "round_1_configuration_sha256": ROUND_1_CONFIGURATION_LOCK.sha256,
            "feature_columns": list(FEATURE_COLUMNS),
            "completed_daily_bar_only": True,
            "rolling_baseline_current_bar_included": False,
            "ema_and_adx_decision_value": "PRIOR_COMPLETED_BAR",
            "rsi_and_stochastic_decision_value": "CURRENT_COMPLETED_BAR",
            "atr_formula": "WILDER_EWM_ALPHA_1_OVER_14",
            "adx_formula": "WILDER_DI_DX_EWM_ALPHA_1_OVER_14",
            "bollinger_standard_deviation_ddof": 0,
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
        previous_high = high.shift(1)
        close_return = close.div(previous_close).sub(1.0)
        prior_close_max_60 = close.shift(1).rolling(60, min_periods=60).max()
        drawdown_60 = close.div(prior_close_max_60).sub(1.0)

        true_range, atr_14 = _wilder_atr(high, low, close, period=14)
        prior_atr_14 = atr_14.shift(1)
        tr_to_prior_atr = true_range.div(prior_atr_14.where(prior_atr_14 > 0.0))
        prior_atr_median_60 = atr_14.shift(1).rolling(60, min_periods=60).median()
        atr_to_prior_median_60 = atr_14.div(
            prior_atr_median_60.where(prior_atr_median_60 > 0.0)
        )
        prior_atr_median_120 = atr_14.shift(1).rolling(
            120, min_periods=120
        ).median()
        atr_to_prior_median_120 = atr_14.div(
            prior_atr_median_120.where(prior_atr_median_120 > 0.0)
        )

        prior_volume_median_30 = volume.shift(1).rolling(
            30, min_periods=30
        ).median()
        volume_ratio = volume.div(
            prior_volume_median_30.where(prior_volume_median_30 > 0.0)
        )
        completed_range = high.sub(low)
        close_location = close.sub(low).div(completed_range.where(completed_range > 0.0))

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

        prior_close = close.shift(1)
        bollinger_mid = prior_close.rolling(20, min_periods=20).mean()
        bollinger_std = prior_close.rolling(20, min_periods=20).std(ddof=0)
        bollinger_lower = bollinger_mid.sub(2.0 * bollinger_std)
        bollinger_upper = bollinger_mid.add(2.0 * bollinger_std)
        bollinger_width = bollinger_upper.sub(bollinger_lower).div(
            bollinger_mid.where(bollinger_mid > 0.0)
        )
        prior_width_median_120 = bollinger_width.shift(1).rolling(
            120, min_periods=120
        ).median()
        band_width_ratio = bollinger_width.div(
            prior_width_median_120.where(prior_width_median_120 > 0.0)
        )

        rsi_14 = _rsi(close, period=14)
        lowest_low_14 = low.rolling(14, min_periods=14).min()
        highest_high_14 = high.rolling(14, min_periods=14).max()
        stochastic_range = highest_high_14.sub(lowest_low_14)
        stochastic_k_14 = 100.0 * close.sub(lowest_low_14).div(
            stochastic_range.where(stochastic_range > 0.0)
        )
        stochastic_d_14_3 = stochastic_k_14.rolling(3, min_periods=3).mean()
        donchian_prior_high_55 = close.shift(1).rolling(
            55, min_periods=55
        ).max()
        prior_close_low_10 = close.shift(1).rolling(10, min_periods=10).min()

        values = (
            previous_close,
            previous_high,
            close_return,
            prior_close_max_60,
            drawdown_60,
            true_range,
            atr_14,
            prior_atr_14,
            tr_to_prior_atr,
            prior_atr_median_60,
            atr_to_prior_median_60,
            prior_atr_median_120,
            atr_to_prior_median_120,
            prior_volume_median_30,
            volume_ratio,
            close_location,
            ema_20_prior,
            ema_50_prior,
            ema_200_prior,
            ema_50_slope_20,
            adx_14_prior,
            bollinger_mid,
            bollinger_lower,
            bollinger_upper,
            bollinger_width,
            prior_width_median_120,
            band_width_ratio,
            rsi_14,
            stochastic_k_14,
            stochastic_d_14_3,
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
        raise TypeError("Round 1 signal features must be a pandas DataFrame.")
    missing = [
        column
        for column in (*REQUIRED_OHLCV_COLUMNS, *FEATURE_COLUMNS)
        if column not in data.columns
    ]
    if missing:
        raise ValueError(f"Round 1 signal feature columns are missing: {missing}.")
    _validated_continuous_daily_frame(data.loc[:, REQUIRED_OHLCV_COLUMNS])
    return data.copy(deep=True)


class KrakenAIDrivenV2Round1SignalEngine:
    """Emit reproducible research intents; no position or fill is created."""

    def __init__(self):
        if tuple(_HYPOTHESES_BY_FAMILY) != FAMILY_ORDER:
            raise RuntimeError("Round 1 signal family order mismatch.")
        if tuple(item["hypothesis_id"] for item in ROUND_1_HYPOTHESES) != (
            HYPOTHESIS_ORDER
        ):
            raise RuntimeError("Round 1 signal hypothesis order mismatch.")
        self.feature_engine = KrakenAIDrivenV2Round1CausalFeatureEngine()

    def configuration(self):
        return {
            "component_id": SIGNAL_COMPONENT_ID,
            "round_1_configuration_sha256": ROUND_1_CONFIGURATION_LOCK.sha256,
            "family_order": list(FAMILY_ORDER),
            "action_intent": ENTER_NEXT_OPEN,
            "trend_and_range_confirmation_timing": (
                "IMMEDIATE_NEXT_COMPLETED_BAR_ONLY"
            ),
            "capitulation_maximum_confirmation_delay_bars": 5,
            "breakout_confirmation_timing": "CURRENT_COMPLETED_BAR",
            "state_role": "ENTRY_SIGNAL_ONLY_NOT_POSITION",
            "position_sizing": False,
            "fill_execution": False,
            "performance_evaluation": False,
            "future_bar_access": False,
            "dataset_opened": False,
        }

    def generate(self, family_id, data):
        if family_id not in FAMILY_ORDER:
            raise ValueError(f"Unknown Round 1 family: {family_id}.")
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
            raise ValueError(f"Unknown Round 1 family: {family_id}.")
        features = _validated_feature_frame(data)
        if family_id == "CAPITULATION_RECOVERY":
            return self._capitulation(features)
        if family_id == "TREND_PULLBACK_CONTINUATION":
            return self._trend_pullback(features)
        if family_id == "RANGE_MEAN_REVERSION":
            return self._range_reversion(features)
        return self._volatility_breakout(features)

    @staticmethod
    def _base_evidence(features, family_id):
        result = features.copy(deep=True)
        result[FAMILY_COLUMN] = family_id
        result[HYPOTHESIS_COLUMN] = _HYPOTHESES_BY_FAMILY[family_id][
            "hypothesis_id"
        ]
        return result

    @staticmethod
    def _finish(
        result,
        *,
        availability,
        regimes,
        setups,
        signals,
        states_before,
        states_after,
        transitions,
        intents,
        setup_timestamps,
        setup_lows,
        signal_atrs,
        target_anchors,
    ):
        result[FEATURES_AVAILABLE_COLUMN] = availability
        result[REGIME_CONDITION_COLUMN] = regimes
        result[SETUP_CONDITION_COLUMN] = setups
        result[SIGNAL_CONDITION_COLUMN] = signals
        result[STATE_BEFORE_COLUMN] = states_before
        result[STATE_AFTER_COLUMN] = states_after
        result[TRANSITION_COLUMN] = transitions
        result[ACTION_INTENT_COLUMN] = intents
        result[SETUP_TIMESTAMP_COLUMN] = setup_timestamps
        result[SETUP_LOW_COLUMN] = setup_lows
        result[SIGNAL_ATR_COLUMN] = signal_atrs
        result[TARGET_ANCHOR_COLUMN] = target_anchors
        return result

    def _capitulation(self, features):
        family = "CAPITULATION_RECOVERY"
        result = self._base_evidence(features, family)
        event_columns = (
            _feature("DRAWDOWN_60"),
            _feature("CLOSE_RETURN_1"),
            _feature("TR_TO_PRIOR_ATR"),
            _feature("VOLUME_RATIO"),
            _feature("CLOSE_LOCATION"),
            _feature("PRIOR_ATR_14"),
            "Close",
            "Low",
        )
        confirmation_columns = (
            _feature("CLOSE_RETURN_1"),
            _feature("VOLUME_RATIO"),
            _feature("CLOSE_LOCATION"),
            _feature("PRIOR_HIGH_1"),
            _feature("PRIOR_ATR_14"),
            "Close",
            "Low",
        )
        state = STATE_FLAT
        age = -1
        anchor_timestamp = None
        anchor_low = math.nan
        evidence = [[] for _ in range(12)]

        for timestamp, row in result.iterrows():
            before = state
            event_available = _finite_row_values(row, event_columns)
            confirmation_available = _finite_row_values(row, confirmation_columns)
            event = event_available and (
                float(row[_feature("DRAWDOWN_60")]) <= -0.18
                and float(row[_feature("CLOSE_RETURN_1")]) <= -0.06
                and float(row[_feature("TR_TO_PRIOR_ATR")]) >= 1.5
                and float(row[_feature("VOLUME_RATIO")]) >= 1.5
                and float(row[_feature("CLOSE_LOCATION")]) <= 0.35
            )
            confirmation = state == STATE_ARMED and confirmation_available and (
                float(row[_feature("CLOSE_LOCATION")]) >= 0.65
                and float(row[_feature("CLOSE_RETURN_1")]) > 0.0
                and float(row[_feature("VOLUME_RATIO")]) >= 0.8
                and float(row["Close"]) > float(row[_feature("PRIOR_HIGH_1")])
            )
            transition = "FLAT_WAIT"
            intent = INTENT_NONE
            available = event_available
            observed_timestamp = None
            observed_low = math.nan
            signal_atr = math.nan
            target_anchor = math.nan

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
                observed_low = min(anchor_low, float(row["Low"]))
                if event:
                    state = STATE_ARMED
                    age = 0
                    anchor_timestamp = timestamp
                    anchor_low = float(row["Low"])
                    transition = "CAPITULATION_REARMED"
                    observed_timestamp = anchor_timestamp
                    observed_low = anchor_low
                elif float(row["Close"]) < anchor_low:
                    state = STATE_FLAT
                    transition = "CAPITULATION_STRUCTURAL_INVALIDATION"
                elif age > 5:
                    state = STATE_FLAT
                    transition = "CAPITULATION_EXPIRED"
                elif confirmation:
                    anchor_low = observed_low
                    state = STATE_FLAT
                    transition = "CAPITULATION_CONFIRMATION"
                    intent = ENTER_NEXT_OPEN
                    signal_atr = float(row[_feature("PRIOR_ATR_14")])
                else:
                    anchor_low = observed_low
                    transition = (
                        "CAPITULATION_WAIT"
                        if confirmation_available
                        else "CAPITULATION_WAIT_FEATURES_UNAVAILABLE"
                    )
                if state == STATE_FLAT:
                    age = -1

            row_values = (
                bool(available),
                bool(event),
                bool(event),
                bool(confirmation),
                before,
                state,
                transition,
                intent,
                observed_timestamp,
                observed_low,
                signal_atr,
                target_anchor,
            )
            for bucket, value in zip(evidence, row_values):
                bucket.append(value)
        return self._finish(
            result,
            availability=evidence[0],
            regimes=evidence[1],
            setups=evidence[2],
            signals=evidence[3],
            states_before=evidence[4],
            states_after=evidence[5],
            transitions=evidence[6],
            intents=evidence[7],
            setup_timestamps=evidence[8],
            setup_lows=evidence[9],
            signal_atrs=evidence[10],
            target_anchors=evidence[11],
        )

    def _trend_pullback(self, features):
        family = "TREND_PULLBACK_CONTINUATION"
        result = self._base_evidence(features, family)
        regime_columns = (
            _feature("EMA_50_PRIOR"),
            _feature("EMA_200_PRIOR"),
            _feature("EMA_50_SLOPE_20"),
            _feature("ADX_14_PRIOR"),
        )
        setup_columns = (*regime_columns, _feature("EMA_20_PRIOR"), _feature("PRIOR_ATR_14"), _feature("VOLUME_RATIO"), "Low", "Close")
        confirmation_columns = (*regime_columns, _feature("EMA_20_PRIOR"), _feature("PRIOR_HIGH_1"), _feature("PRIOR_ATR_14"), _feature("VOLUME_RATIO"), "Low", "Close")
        state = STATE_FLAT
        anchor_timestamp = None
        anchor_low = math.nan
        evidence = [[] for _ in range(12)]

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
            prior_atr = float(row[_feature("PRIOR_ATR_14")]) if setup_available else math.nan
            distance = (
                abs(float(row["Low"]) - float(row[_feature("EMA_20_PRIOR")]))
                / prior_atr
                if setup_available and prior_atr > 0.0
                else math.inf
            )
            setup = setup_available and regime and (
                distance <= 0.25
                and float(row["Close"]) > float(row[_feature("EMA_50_PRIOR")])
                and float(row[_feature("VOLUME_RATIO")]) <= 0.9
            )
            confirmation_available = _finite_row_values(row, confirmation_columns)
            confirmation = state == STATE_ARMED and confirmation_available and regime and (
                float(row["Close"]) > float(row[_feature("PRIOR_HIGH_1")])
                and float(row["Close"]) > float(row[_feature("EMA_20_PRIOR")])
                and float(row[_feature("VOLUME_RATIO")]) >= 1.1
            )
            available = setup_available if state == STATE_FLAT else confirmation_available
            transition = "TREND_PULLBACK_WAIT"
            intent = INTENT_NONE
            observed_timestamp = None
            observed_low = math.nan
            signal_atr = math.nan

            if state == STATE_FLAT:
                if setup:
                    state = STATE_ARMED
                    anchor_timestamp = timestamp
                    anchor_low = float(row["Low"])
                    transition = "TREND_PULLBACK_ARMED"
                    observed_timestamp = anchor_timestamp
                    observed_low = anchor_low
                elif not setup_available:
                    transition = "FEATURES_UNAVAILABLE"
            else:
                observed_timestamp = anchor_timestamp
                observed_low = anchor_low
                if confirmation:
                    state = STATE_FLAT
                    transition = "TREND_PULLBACK_CONFIRMATION"
                    intent = ENTER_NEXT_OPEN
                    signal_atr = float(row[_feature("PRIOR_ATR_14")])
                elif setup:
                    state = STATE_ARMED
                    anchor_timestamp = timestamp
                    anchor_low = float(row["Low"])
                    transition = "TREND_PULLBACK_REARMED"
                    observed_timestamp = anchor_timestamp
                    observed_low = anchor_low
                else:
                    state = STATE_FLAT
                    transition = (
                        "TREND_PULLBACK_EXPIRED"
                        if confirmation_available
                        else "TREND_PULLBACK_EXPIRED_FEATURES_UNAVAILABLE"
                    )
            row_values = (
                bool(available), bool(regime), bool(setup), bool(confirmation),
                before, state, transition, intent, observed_timestamp,
                observed_low, signal_atr, math.nan,
            )
            for bucket, value in zip(evidence, row_values):
                bucket.append(value)
        return self._finish(
            result,
            availability=evidence[0], regimes=evidence[1], setups=evidence[2],
            signals=evidence[3], states_before=evidence[4], states_after=evidence[5],
            transitions=evidence[6], intents=evidence[7], setup_timestamps=evidence[8],
            setup_lows=evidence[9], signal_atrs=evidence[10], target_anchors=evidence[11],
        )

    def _range_reversion(self, features):
        family = "RANGE_MEAN_REVERSION"
        result = self._base_evidence(features, family)
        regime_columns = (
            _feature("BAND_WIDTH_TO_PRIOR_MEDIAN_120"),
            _feature("ATR_TO_PRIOR_MEDIAN_120"),
        )
        setup_columns = (*regime_columns, _feature("BOLLINGER_LOWER_20_PRIOR"), _feature("RSI_14"), _feature("STOCHASTIC_K_14"), _feature("STOCHASTIC_D_14_3"), _feature("PRIOR_ATR_14"), "Close", "Low")
        confirmation_columns = (*regime_columns, _feature("BOLLINGER_MID_20_PRIOR"), _feature("RSI_14"), _feature("STOCHASTIC_K_14"), _feature("STOCHASTIC_D_14_3"), _feature("PRIOR_ATR_14"), "Close", "Low")
        state = STATE_FLAT
        anchor_timestamp = None
        anchor_low = math.nan
        setup_lower = math.nan
        setup_rsi = math.nan
        setup_k = math.nan
        setup_d = math.nan
        evidence = [[] for _ in range(12)]

        for timestamp, row in result.iterrows():
            before = state
            regime_available = _finite_row_values(row, regime_columns)
            regime = regime_available and (
                float(row[_feature("BAND_WIDTH_TO_PRIOR_MEDIAN_120")]) <= 1.1
                and float(row[_feature("ATR_TO_PRIOR_MEDIAN_120")]) <= 1.1
            )
            setup_available = _finite_row_values(row, setup_columns)
            setup = setup_available and regime and (
                float(row["Close"]) < float(row[_feature("BOLLINGER_LOWER_20_PRIOR")])
                and float(row[_feature("RSI_14")]) <= 25.0
                and float(row[_feature("STOCHASTIC_K_14")]) <= 20.0
            )
            confirmation_available = _finite_row_values(row, confirmation_columns)
            confirmation = state == STATE_ARMED and confirmation_available and regime and (
                float(row["Close"]) > setup_lower
                and float(row[_feature("RSI_14")]) > setup_rsi
                and setup_k <= setup_d
                and float(row[_feature("STOCHASTIC_K_14")])
                > float(row[_feature("STOCHASTIC_D_14_3")])
            )
            available = setup_available if state == STATE_FLAT else confirmation_available
            transition = "RANGE_REVERSION_WAIT"
            intent = INTENT_NONE
            observed_timestamp = None
            observed_low = math.nan
            signal_atr = math.nan
            target_anchor = math.nan

            if state == STATE_FLAT:
                if setup:
                    state = STATE_ARMED
                    anchor_timestamp = timestamp
                    anchor_low = float(row["Low"])
                    setup_lower = float(row[_feature("BOLLINGER_LOWER_20_PRIOR")])
                    setup_rsi = float(row[_feature("RSI_14")])
                    setup_k = float(row[_feature("STOCHASTIC_K_14")])
                    setup_d = float(row[_feature("STOCHASTIC_D_14_3")])
                    transition = "RANGE_REVERSION_ARMED"
                    observed_timestamp = anchor_timestamp
                    observed_low = anchor_low
                elif not setup_available:
                    transition = "FEATURES_UNAVAILABLE"
            else:
                observed_timestamp = anchor_timestamp
                observed_low = min(anchor_low, float(row["Low"]))
                if confirmation:
                    state = STATE_FLAT
                    transition = "RANGE_REVERSION_CONFIRMATION"
                    intent = ENTER_NEXT_OPEN
                    signal_atr = float(row[_feature("PRIOR_ATR_14")])
                    target_anchor = float(row[_feature("BOLLINGER_MID_20_PRIOR")])
                elif setup:
                    state = STATE_ARMED
                    anchor_timestamp = timestamp
                    anchor_low = float(row["Low"])
                    setup_lower = float(row[_feature("BOLLINGER_LOWER_20_PRIOR")])
                    setup_rsi = float(row[_feature("RSI_14")])
                    setup_k = float(row[_feature("STOCHASTIC_K_14")])
                    setup_d = float(row[_feature("STOCHASTIC_D_14_3")])
                    transition = "RANGE_REVERSION_REARMED"
                    observed_timestamp = anchor_timestamp
                    observed_low = anchor_low
                else:
                    state = STATE_FLAT
                    transition = (
                        "RANGE_REVERSION_EXPIRED"
                        if confirmation_available
                        else "RANGE_REVERSION_EXPIRED_FEATURES_UNAVAILABLE"
                    )
            row_values = (
                bool(available), bool(regime), bool(setup), bool(confirmation),
                before, state, transition, intent, observed_timestamp,
                observed_low, signal_atr, target_anchor,
            )
            for bucket, value in zip(evidence, row_values):
                bucket.append(value)
        return self._finish(
            result,
            availability=evidence[0], regimes=evidence[1], setups=evidence[2],
            signals=evidence[3], states_before=evidence[4], states_after=evidence[5],
            transitions=evidence[6], intents=evidence[7], setup_timestamps=evidence[8],
            setup_lows=evidence[9], signal_atrs=evidence[10], target_anchors=evidence[11],
        )

    def _volatility_breakout(self, features):
        family = "VOLATILITY_BREAKOUT"
        result = self._base_evidence(features, family)
        required = (
            _feature("ATR_TO_PRIOR_MEDIAN_60"),
            _feature("ADX_14_PRIOR"),
            _feature("DONCHIAN_PRIOR_CLOSE_HIGH_55"),
            _feature("VOLUME_RATIO"),
            _feature("CLOSE_LOCATION"),
            _feature("PRIOR_ATR_14"),
            "Close",
            "Low",
        )
        evidence = [[] for _ in range(12)]
        for timestamp, row in result.iterrows():
            available = _finite_row_values(row, required)
            regime = available and (
                float(row[_feature("ATR_TO_PRIOR_MEDIAN_60")]) >= 1.1
                and float(row[_feature("ADX_14_PRIOR")]) >= 20.0
            )
            signal = available and regime and (
                float(row["Close"])
                > float(row[_feature("DONCHIAN_PRIOR_CLOSE_HIGH_55")])
                and float(row[_feature("VOLUME_RATIO")]) >= 1.25
                and float(row[_feature("CLOSE_LOCATION")]) >= 0.70
            )
            transition = (
                "VOLATILITY_BREAKOUT_CONFIRMATION"
                if signal
                else "BREAKOUT_WAIT" if available else "FEATURES_UNAVAILABLE"
            )
            row_values = (
                bool(available), bool(regime), bool(signal), bool(signal),
                STATE_FLAT, STATE_FLAT, transition,
                ENTER_NEXT_OPEN if signal else INTENT_NONE,
                timestamp if signal else None,
                float(row["Low"]) if signal else math.nan,
                float(row[_feature("PRIOR_ATR_14")]) if signal else math.nan,
                math.nan,
            )
            for bucket, value in zip(evidence, row_values):
                bucket.append(value)
        return self._finish(
            result,
            availability=evidence[0], regimes=evidence[1], setups=evidence[2],
            signals=evidence[3], states_before=evidence[4], states_after=evidence[5],
            transitions=evidence[6], intents=evidence[7], setup_timestamps=evidence[8],
            setup_lows=evidence[9], signal_atrs=evidence[10], target_anchors=evidence[11],
        )
