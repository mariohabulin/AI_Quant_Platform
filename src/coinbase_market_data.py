from dataclasses import dataclass
import json
import time

import pandas as pd


COINBASE_WS_URL = "wss://advanced-trade-ws.coinbase.com"


@dataclass(frozen=True)
class CoinbaseCompletedBar:
    timestamp: pd.Timestamp
    open: float
    high: float
    low: float
    close: float
    volume: float


class CoinbaseOneMinuteTradeAggregator:
    """Aggregate Coinbase public market trades into completed one-minute OHLCV bars.

    The current minute is never emitted. A bar is returned only after a trade from
    a later minute proves the previous bucket has completed.
    """

    def __init__(self, product_id="BTC-USD"):
        if not isinstance(product_id, str) or not product_id.strip():
            raise ValueError("product_id is required.")
        self.product_id = product_id.strip().upper()
        self._bucket = None
        self._ohlcv = None

    @staticmethod
    def _timestamp(value):
        try:
            ts = pd.Timestamp(value)
        except Exception as exc:
            raise ValueError("Trade timestamp must be datetime-like.") from exc
        if pd.isna(ts):
            raise ValueError("Trade timestamp must be valid.")
        return ts

    @staticmethod
    def _number(value, name, positive=True):
        try:
            result = float(value)
        except (TypeError, ValueError) as exc:
            raise ValueError(f"Trade {name} must be numeric.") from exc
        if positive and result <= 0:
            raise ValueError(f"Trade {name} must be greater than zero.")
        if not positive and result < 0:
            raise ValueError(f"Trade {name} cannot be negative.")
        return result

    def ingest_trade(self, trade):
        if not isinstance(trade, dict):
            raise TypeError("Trade must be a dict.")
        product = str(trade.get("product_id", self.product_id)).upper()
        if product != self.product_id:
            raise ValueError(f"Trade product_id must be {self.product_id}.")
        ts = self._timestamp(trade.get("time"))
        price = self._number(trade.get("price"), "price")
        size = self._number(trade.get("size"), "size")
        bucket = ts.floor("min")

        completed = None
        if self._bucket is None:
            self._bucket = bucket
            self._ohlcv = [price, price, price, price, size]
            return None
        if bucket < self._bucket:
            raise ValueError("Out-of-order Coinbase trade rejected.")
        if bucket > self._bucket:
            completed = CoinbaseCompletedBar(self._bucket, *self._ohlcv)
            self._bucket = bucket
            self._ohlcv = [price, price, price, price, size]
            return completed

        self._ohlcv[1] = max(self._ohlcv[1], price)
        self._ohlcv[2] = min(self._ohlcv[2], price)
        self._ohlcv[3] = price
        self._ohlcv[4] += size
        return None

    def ingest_message(self, message):
        """Consume one Coinbase websocket message and return completed bars."""
        if not isinstance(message, dict):
            raise TypeError("Coinbase message must be a dict.")
        channel = message.get("channel")
        if channel == "heartbeats":
            return []
        if channel != "market_trades":
            return []

        completed = []
        for event in message.get("events", []):
            trades = event.get("trades", [])
            # Coinbase batches market trades over a short interval. Normalize provider
            # ordering before feeding the strict stateful minute aggregator because a
            # batch can straddle a minute boundary and need not arrive oldest-first.
            trades = sorted(trades, key=lambda trade: self._timestamp(trade.get("time")))
            for trade in trades:
                bar = self.ingest_trade(trade)
                if bar is not None:
                    completed.append(bar)
        return completed


class CoinbaseOneMinuteBarAdapter:
    """Translate completed Coinbase 1m bars into RealTimeMarketDataFeed schema."""

    def __init__(self, symbol="BTC/USD"):
        if not isinstance(symbol, str) or not symbol.strip():
            raise ValueError("symbol is required.")
        self.symbol = symbol.strip().upper()

    def normalize(self, bar):
        if isinstance(bar, CoinbaseCompletedBar):
            timestamp = bar.timestamp
            values = {
                "Open": bar.open,
                "High": bar.high,
                "Low": bar.low,
                "Close": bar.close,
                "Volume": bar.volume,
            }
        elif isinstance(bar, dict):
            required = ("timestamp", "open", "high", "low", "close", "volume")
            missing = [key for key in required if key not in bar]
            if missing:
                raise ValueError(f"Completed Coinbase bar missing fields: {missing}")
            timestamp = pd.Timestamp(bar["timestamp"])
            values = {
                "Open": float(bar["open"]), "High": float(bar["high"]),
                "Low": float(bar["low"]), "Close": float(bar["close"]),
                "Volume": float(bar["volume"]),
            }
        else:
            raise TypeError("Completed Coinbase bar must be a CoinbaseCompletedBar or dict.")

        if pd.isna(timestamp):
            raise ValueError("Completed bar timestamp must be valid.")
        if any(values[name] <= 0 for name in ("Open", "High", "Low", "Close")):
            raise ValueError("Completed bar OHLC prices must be greater than zero.")
        if values["Volume"] < 0:
            raise ValueError("Completed bar Volume cannot be negative.")
        if values["High"] < max(values["Open"], values["Low"], values["Close"]):
            raise ValueError("Completed bar High has invalid price geometry.")
        if values["Low"] > min(values["Open"], values["High"], values["Close"]):
            raise ValueError("Completed bar Low has invalid price geometry.")
        return timestamp, values


class CoinbasePublicWebSocketTransport:
    """Small replaceable transport for Coinbase public market-data websocket.

    Network access occurs only when iterated. A websocket factory can be injected
    for deterministic tests. Reconnect attempts are bounded.
    """

    def __init__(self, product_id="BTC-USD", websocket_factory=None,
                 max_reconnect_attempts=3, backoff_seconds=1.0):
        if max_reconnect_attempts < 0:
            raise ValueError("max_reconnect_attempts cannot be negative.")
        if backoff_seconds < 0:
            raise ValueError("backoff_seconds cannot be negative.")
        self.product_id = str(product_id).upper()
        self.websocket_factory = websocket_factory
        self.max_reconnect_attempts = int(max_reconnect_attempts)
        self.backoff_seconds = float(backoff_seconds)

    @property
    def subscription_messages(self):
        return (
            {"type": "subscribe", "product_ids": [self.product_id], "channel": "market_trades"},
            {"type": "subscribe", "channel": "heartbeats"},
        )

    def _connect(self):
        if self.websocket_factory is not None:
            return self.websocket_factory(COINBASE_WS_URL)
        try:
            from websocket import create_connection
        except ImportError as exc:
            raise RuntimeError("websocket-client is required for Coinbase transport.") from exc
        return create_connection(COINBASE_WS_URL, timeout=10)

    def __iter__(self):
        attempts = 0
        while True:
            ws = None
            try:
                ws = self._connect()
                for payload in self.subscription_messages:
                    ws.send(json.dumps(payload))
                while True:
                    raw = ws.recv()
                    if raw is None:
                        raise ConnectionError("Coinbase websocket closed.")
                    yield json.loads(raw) if isinstance(raw, str) else raw
            except GeneratorExit:
                raise
            except Exception:
                attempts += 1
                if attempts > self.max_reconnect_attempts:
                    raise
                if self.backoff_seconds:
                    time.sleep(self.backoff_seconds)
            finally:
                if ws is not None:
                    try:
                        ws.close()
                    except Exception:
                        pass
