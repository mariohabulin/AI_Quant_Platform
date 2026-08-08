from dataclasses import dataclass

import pandas as pd

from src.market_data_feed import MarketDataEvent, REQUIRED_OHLCV_COLUMNS


class FeedHealthError(RuntimeError):
    """Raised when external market data is unsafe to forward to trading."""


@dataclass(frozen=True)
class FeedHealthSnapshot:
    status: str
    accepted_events: int
    last_timestamp: object = None
    last_received_at: object = None
    reason: str = ""


class AlpacaCryptoBarAdapter:
    """Normalize Alpaca crypto websocket bar messages into the internal OHLCV contract.

    Transport/authentication intentionally stay outside this adapter.  The adapter
    knows the provider schema; downstream trading code does not.
    """

    def __init__(self, symbol="BTC/USD"):
        if not isinstance(symbol, str) or not symbol.strip():
            raise ValueError("symbol is required.")
        self.symbol = symbol.strip().upper()

    def normalize(self, message):
        if not isinstance(message, dict):
            raise TypeError("Provider message must be a dict.")
        if message.get("T") != "b":
            raise ValueError("Provider message must be an Alpaca bar event.")
        if str(message.get("S", "")).upper() != self.symbol:
            raise ValueError(f"Provider bar symbol must be {self.symbol}.")

        required = ("t", "o", "h", "l", "c", "v")
        missing = [field for field in required if field not in message]
        if missing:
            raise ValueError(f"Provider bar missing required fields: {missing}")

        try:
            timestamp = pd.Timestamp(message["t"])
        except Exception as exc:
            raise TypeError("Provider bar timestamp must be datetime-like.") from exc
        if pd.isna(timestamp):
            raise ValueError("Provider bar timestamp must be valid.")

        values = {}
        mapping = {"Open": "o", "High": "h", "Low": "l", "Close": "c", "Volume": "v"}
        for column, field in mapping.items():
            try:
                values[column] = float(message[field])
            except (TypeError, ValueError) as exc:
                raise ValueError("Provider OHLCV values must be numeric.") from exc

        if any(values[column] <= 0 for column in ("Open", "High", "Low", "Close")):
            raise ValueError("Provider OHLC prices must be greater than zero.")
        if values["Volume"] < 0:
            raise ValueError("Provider Volume cannot be negative.")
        if values["High"] < max(values["Open"], values["Low"], values["Close"]):
            raise ValueError("Provider High has invalid price geometry.")
        if values["Low"] > min(values["Open"], values["High"], values["Close"]):
            raise ValueError("Provider Low has invalid price geometry.")

        return timestamp, values


class RealTimeMarketDataFeed:
    """Health-gated real-time bar boundary that emits normalized MarketDataEvent objects."""

    def __init__(self, adapter, timeframe="1min", stale_after="2min", max_gap="2min"):
        if adapter is None:
            raise ValueError("adapter is required.")
        self.adapter = adapter
        self.timeframe = pd.Timedelta(timeframe)
        self.stale_after = pd.Timedelta(stale_after)
        self.max_gap = pd.Timedelta(max_gap)
        if self.timeframe <= pd.Timedelta(0):
            raise ValueError("timeframe must be positive.")
        if self.stale_after < pd.Timedelta(0):
            raise ValueError("stale_after cannot be negative.")
        if self.max_gap < self.timeframe:
            raise ValueError("max_gap cannot be shorter than timeframe.")
        self._history = pd.DataFrame(columns=REQUIRED_OHLCV_COLUMNS, dtype=float)
        self._last_timestamp = None
        self._last_received_at = None
        self._accepted = 0
        self._health = FeedHealthSnapshot("WAITING", 0, reason="No market data received yet.")

    @property
    def health(self):
        return self._health

    @property
    def history(self):
        return self._history.copy()

    def _fail(self, reason, received_at=None):
        self._health = FeedHealthSnapshot(
            "UNHEALTHY", self._accepted, self._last_timestamp,
            received_at if received_at is not None else self._last_received_at, reason,
        )
        raise FeedHealthError(reason)

    def ingest(self, provider_message, received_at=None):
        timestamp, values = self.adapter.normalize(provider_message)
        received = pd.Timestamp(received_at) if received_at is not None else pd.Timestamp.now(tz="UTC")
        if pd.isna(received):
            raise ValueError("received_at must be valid.")

        # Normalize timezone awareness for age comparisons without altering event timestamp.
        compare_ts = timestamp
        compare_received = received
        if compare_ts.tzinfo is None and compare_received.tzinfo is not None:
            compare_ts = compare_ts.tz_localize("UTC")
        elif compare_ts.tzinfo is not None and compare_received.tzinfo is None:
            compare_received = compare_received.tz_localize("UTC")

        age = compare_received - compare_ts
        if age < pd.Timedelta(0):
            self._fail("Provider bar timestamp is in the future.", received)
        if age > self.stale_after:
            self._fail("Provider bar is stale.", received)

        if self._last_timestamp is not None:
            if timestamp == self._last_timestamp:
                self._fail("Duplicate provider bar rejected.", received)
            if timestamp < self._last_timestamp:
                self._fail("Out-of-order provider bar rejected.", received)
            gap = timestamp - self._last_timestamp
            if gap > self.max_gap:
                self._fail("Missing-bar gap exceeds configured tolerance.", received)

        row = pd.DataFrame([values], index=pd.DatetimeIndex([timestamp]))
        if self._history.empty:
            self._history = row.loc[:, REQUIRED_OHLCV_COLUMNS].copy()
        else:
            self._history = pd.concat([self._history, row]).loc[:, REQUIRED_OHLCV_COLUMNS]
        self._accepted += 1
        self._last_timestamp = timestamp
        self._last_received_at = received
        self._health = FeedHealthSnapshot("HEALTHY", self._accepted, timestamp, received, "Feed healthy.")
        return MarketDataEvent(self._accepted, timestamp, self._history.copy())
