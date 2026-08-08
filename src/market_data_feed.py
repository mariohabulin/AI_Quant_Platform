from dataclasses import dataclass

import pandas as pd


REQUIRED_OHLCV_COLUMNS = ("Open", "High", "Low", "Close", "Volume")


@dataclass(frozen=True)
class MarketDataEvent:
    """Normalized event delivered to the paper-trading boundary.

    ``data`` contains only information available up to and including this
    event.  This makes the same contract usable by deterministic replay and a
    later real-time adapter without giving the consumer access to future bars.
    """

    sequence: int
    timestamp: pd.Timestamp
    data: pd.DataFrame

    @property
    def bar(self):
        return self.data.iloc[-1].copy()


class HistoricalReplayFeed:
    """Deterministically replay validated OHLCV bars as forward-time events."""

    def __init__(self, data):
        self._data = self._normalize(data)

    @staticmethod
    def _normalize(data):
        if not isinstance(data, pd.DataFrame):
            raise TypeError("Replay data must be a pandas DataFrame.")
        if data.empty:
            raise ValueError("Replay data cannot be empty.")

        missing = [column for column in REQUIRED_OHLCV_COLUMNS if column not in data.columns]
        if missing:
            raise ValueError(f"Replay data missing required OHLCV columns: {missing}")

        normalized = data.loc[:, REQUIRED_OHLCV_COLUMNS].copy()
        try:
            normalized.index = pd.DatetimeIndex(pd.to_datetime(normalized.index))
        except Exception as exc:
            raise TypeError("Replay index must be datetime-like.") from exc

        if normalized.index.hasnans:
            raise ValueError("Replay timestamps must be valid.")
        if normalized.index.has_duplicates:
            raise ValueError("Replay timestamps must be unique.")
        if not normalized.index.is_monotonic_increasing:
            raise ValueError("Replay timestamps must be strictly increasing.")

        for column in REQUIRED_OHLCV_COLUMNS:
            normalized[column] = pd.to_numeric(normalized[column], errors="coerce")
        if normalized.isna().any().any():
            raise ValueError("Replay OHLCV values must be numeric and non-null.")

        prices = normalized[["Open", "High", "Low", "Close"]]
        if (prices <= 0).any().any():
            raise ValueError("Replay OHLC prices must be greater than zero.")
        if (normalized["Volume"] < 0).any():
            raise ValueError("Replay Volume cannot be negative.")
        if (normalized["High"] < normalized[["Open", "Low", "Close"]].max(axis=1)).any():
            raise ValueError("Replay High must be at least Open, Low and Close.")
        if (normalized["Low"] > normalized[["Open", "High", "Close"]].min(axis=1)).any():
            raise ValueError("Replay Low must be at most Open, High and Close.")

        return normalized

    @property
    def bar_count(self):
        return len(self._data)

    def __iter__(self):
        # A fresh iterator always replays from the beginning.  Each event gets
        # its own copy so downstream mutation cannot corrupt feed state.
        for offset, timestamp in enumerate(self._data.index):
            yield MarketDataEvent(
                sequence=offset + 1,
                timestamp=timestamp,
                data=self._data.iloc[: offset + 1].copy(),
            )
