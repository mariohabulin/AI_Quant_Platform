"""Causal, performance-free daily chart replay primitives."""

import hashlib
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation

import numpy as np
import pandas as pd

try:
    from research_evidence import canonical_json_bytes
except ImportError:  # pragma: no cover - package import compatibility
    from .research_evidence import canonical_json_bytes


REQUIRED_OHLCV_COLUMNS = ("Open", "High", "Low", "Close", "Volume")
DAILY_STEP = pd.Timedelta(days=1)
POSITION_FLAT = "FLAT"
POSITION_LONG = "LONG"
ALLOWED_ACTIONS = {
    POSITION_FLAT: ("ENTER", "SKIP"),
    POSITION_LONG: ("EXIT", "HOLD"),
}


def _validated_daily_frame(data, *, require_continuous):
    if not isinstance(data, pd.DataFrame):
        raise TypeError("Replay data must be a pandas DataFrame.")
    if data.empty:
        raise ValueError("Replay data cannot be empty.")
    if tuple(data.columns) != REQUIRED_OHLCV_COLUMNS:
        raise ValueError(
            "Replay data must contain exact ordered OHLCV columns: "
            f"{REQUIRED_OHLCV_COLUMNS}."
        )
    if not isinstance(data.index, pd.DatetimeIndex):
        raise TypeError("Replay data must use a DatetimeIndex.")
    if data.index.tz is None:
        raise ValueError("Replay data index must be timezone-aware.")
    if not data.index.is_monotonic_increasing:
        raise ValueError("Replay data index must be monotonic increasing.")
    if data.index.has_duplicates:
        raise ValueError("Replay data index must not contain duplicates.")

    normalized = data.copy(deep=True)
    normalized.index = normalized.index.tz_convert("UTC")
    if any(
        timestamp.hour
        or timestamp.minute
        or timestamp.second
        or timestamp.microsecond
        or timestamp.nanosecond
        for timestamp in normalized.index
    ):
        raise ValueError("Replay data timestamps must align to UTC midnight.")
    if require_continuous and len(normalized.index) > 1:
        deltas = normalized.index[1:] - normalized.index[:-1]
        if any(delta != DAILY_STEP for delta in deltas):
            raise ValueError(
                "Replay data must be one continuous daily availability segment."
            )

    try:
        values = normalized.loc[:, REQUIRED_OHLCV_COLUMNS].to_numpy(dtype=float)
    except (TypeError, ValueError) as exc:
        raise ValueError("Replay OHLCV values must be numeric.") from exc
    if not np.isfinite(values).all():
        raise ValueError("Replay OHLCV values must be finite.")
    if (values[:, :4] <= 0).any() or (values[:, 4] < 0).any():
        raise ValueError("Replay prices must be positive and volume nonnegative.")

    open_values = values[:, 0]
    high_values = values[:, 1]
    low_values = values[:, 2]
    close_values = values[:, 3]
    if (
        (high_values < open_values).any()
        or (high_values < close_values).any()
        or (low_values > open_values).any()
        or (low_values > close_values).any()
        or (high_values < low_values).any()
    ):
        raise ValueError("Replay OHLC price geometry is invalid.")
    return normalized


def find_missing_daily_timestamps(data):
    """Return absent UTC-midnight buckets without modifying the source frame."""

    frame = _validated_daily_frame(data, require_continuous=False)
    expected = pd.date_range(frame.index[0], frame.index[-1], freq="D", tz="UTC")
    return tuple(expected.difference(frame.index))


def split_continuous_daily_segments(data):
    """Split at recorded availability gaps; never synthesize missing candles."""

    frame = _validated_daily_frame(data, require_continuous=False)
    if len(frame) == 1:
        return (frame.copy(deep=True),)
    breaks = np.flatnonzero(
        (frame.index[1:] - frame.index[:-1]) != DAILY_STEP
    )
    starts = [0, *[int(value) + 1 for value in breaks]]
    ends = [*[int(value) + 1 for value in breaks], len(frame)]
    return tuple(frame.iloc[start:end].copy(deep=True) for start, end in zip(starts, ends))


def _canonical_replay_decimal(value):
    try:
        number = Decimal(str(value))
    except (InvalidOperation, ValueError) as exc:
        raise ValueError("Replay evidence value must be an exact decimal.") from exc
    if not number.is_finite():
        raise ValueError("Replay evidence value must be finite.")
    if number == 0:
        return "0"
    text = format(number, "f")
    if "." in text:
        text = text.rstrip("0").rstrip(".")
    return text


def visible_frame_sha256(frame):
    """Hash exactly the bars visible to one decision without float coercion."""

    rows = []
    for timestamp, row in frame.iterrows():
        rows.append(
            {
                "Timestamp": timestamp.isoformat(),
                **{
                    column: _canonical_replay_decimal(row[column])
                    for column in REQUIRED_OHLCV_COLUMNS
                },
            }
        )
    return hashlib.sha256(canonical_json_bytes(rows)).hexdigest()


@dataclass(frozen=True)
class BlindedReplayView:
    asset: str
    sequence: int
    timestamp: pd.Timestamp
    position_state: str
    bars: pd.DataFrame


@dataclass(frozen=True)
class BlindedReplayDecision:
    asset: str
    sequence: int
    timestamp: pd.Timestamp
    action: str
    reason: str
    position_before: str
    position_after: str
    visible_bars_sha256: str

    def as_dict(self):
        return {
            "asset": self.asset,
            "sequence": self.sequence,
            "timestamp": self.timestamp.isoformat(),
            "action": self.action,
            "reason": self.reason,
            "position_before": self.position_before,
            "position_after": self.position_after,
            "visible_bars_sha256": self.visible_bars_sha256,
        }


class BlindedDailyReplaySession:
    """Reveal one completed daily bar only after a precommitted decision."""

    def __init__(self, asset, data, context_bars=30, decision_sink=None):
        if not isinstance(asset, str) or not asset.strip():
            raise ValueError("Replay asset must be a nonempty string.")
        if not isinstance(context_bars, int) or isinstance(context_bars, bool):
            raise TypeError("context_bars must be an integer.")
        if context_bars < 2:
            raise ValueError("context_bars must be at least 2.")
        if decision_sink is not None and not callable(decision_sink):
            raise TypeError("decision_sink must be callable.")
        frame = _validated_daily_frame(data, require_continuous=True)
        if len(frame) <= context_bars:
            raise ValueError("Replay data must contain more rows than context_bars.")

        self._asset = asset.strip()
        self._data = frame
        self._context_bars = context_bars
        self._decision_sink = decision_sink
        self._cursor = context_bars - 1
        self._position = POSITION_FLAT
        self._decisions = []
        self._decision_recorded = False
        self._complete = False

    @property
    def decisions(self):
        return tuple(self._decisions)

    @property
    def is_complete(self):
        return self._complete

    def _visible_bars(self):
        start = self._cursor - self._context_bars + 1
        return self._data.iloc[start : self._cursor + 1].copy(deep=True)

    def current_view(self):
        if self._complete:
            raise RuntimeError("Replay is complete; no current view remains.")
        return BlindedReplayView(
            asset=self._asset,
            sequence=len(self._decisions),
            timestamp=self._data.index[self._cursor],
            position_state=self._position,
            bars=self._visible_bars(),
        )

    def record_decision(self, action, reason):
        if self._complete:
            raise RuntimeError("Replay is complete; decisions are closed.")
        if self._decision_recorded:
            raise RuntimeError("A decision is already recorded for this timestamp.")
        if not isinstance(action, str):
            raise TypeError("Replay action must be a canonical string.")
        if action not in {item for actions in ALLOWED_ACTIONS.values() for item in actions}:
            raise ValueError("Replay action is not recognized.")
        if action not in ALLOWED_ACTIONS[self._position]:
            raise ValueError(
                f"Action {action} is invalid while position is {self._position}."
            )
        if not isinstance(reason, str):
            raise TypeError("Replay reason must be a nonempty string.")
        normalized_reason = reason.strip()
        if not normalized_reason:
            raise ValueError("Replay reason must be recorded before advancing.")

        before = self._position
        after = before
        if action == "ENTER":
            after = POSITION_LONG
        elif action == "EXIT":
            after = POSITION_FLAT
        visible = self._visible_bars()
        decision = BlindedReplayDecision(
            asset=self._asset,
            sequence=len(self._decisions),
            timestamp=self._data.index[self._cursor],
            action=action,
            reason=normalized_reason,
            position_before=before,
            position_after=after,
            visible_bars_sha256=visible_frame_sha256(visible),
        )
        if self._decision_sink is not None:
            self._decision_sink(decision)
        self._decisions.append(decision)
        self._position = after
        self._decision_recorded = True
        return decision

    def advance(self):
        if self._complete:
            raise RuntimeError("Replay is complete and cannot advance.")
        if not self._decision_recorded:
            raise RuntimeError("You must record a decision before revealing another bar.")
        if self._cursor == len(self._data) - 1:
            self._complete = True
            return None
        self._cursor += 1
        self._decision_recorded = False
        return self.current_view()

    def summary(self):
        return {
            "status": (
                "BLINDED_DAILY_REPLAY_COMPLETED"
                if self._complete
                else "BLINDED_DAILY_REPLAY_IN_PROGRESS"
            ),
            "asset": self._asset,
            "context_bars": self._context_bars,
            "decision_count": len(self._decisions),
            "position_state": self._position,
            "decisions": [decision.as_dict() for decision in self._decisions],
            "performance_evaluation_executed": False,
            "strategy_selection_executed": False,
            "candidate_v2_authorized": False,
            "bounded_forward_paper_authorized": False,
            "cloud_execution_authorized": False,
            "live_execution_authorized": False,
        }
