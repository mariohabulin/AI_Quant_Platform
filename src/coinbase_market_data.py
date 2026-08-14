from dataclasses import dataclass
import heapq
import json
import socket
import time

import pandas as pd


COINBASE_WS_URL = "wss://advanced-trade-ws.coinbase.com"
COINBASE_EXCHANGE_REST_URL = "https://api.exchange.coinbase.com"


@dataclass(frozen=True)
class CoinbaseCompletedBar:
    timestamp: pd.Timestamp
    open: float
    high: float
    low: float
    close: float
    volume: float


class CoinbaseTradeOrderingError(ValueError):
    """Fail-closed late-trade error with evidence for incident diagnosis."""

    def __init__(
        self,
        *,
        trade_timestamp,
        trade_bucket,
        active_bucket,
        latest_seen_timestamp,
        reorder_window,
    ):
        self.trade_timestamp = pd.Timestamp(trade_timestamp)
        self.trade_bucket = pd.Timestamp(trade_bucket)
        self.active_bucket = pd.Timestamp(active_bucket)
        self.latest_seen_timestamp = (
            None
            if latest_seen_timestamp is None
            else pd.Timestamp(latest_seen_timestamp)
        )
        self.reorder_window_seconds = float(
            pd.Timedelta(reorder_window).total_seconds()
        )
        self.watermark_timestamp = (
            None
            if self.latest_seen_timestamp is None
            else self.latest_seen_timestamp - pd.Timedelta(reorder_window)
        )
        self.lateness_seconds = (
            max(
                0.0,
                (self.watermark_timestamp - self.trade_timestamp).total_seconds(),
            )
            if self.watermark_timestamp is not None
            else max(
                0.0,
                (self.active_bucket - self.trade_timestamp).total_seconds(),
            )
        )
        super().__init__(
            "Out-of-order Coinbase trade rejected "
            f"(trade_timestamp={self.trade_timestamp.isoformat()} "
            f"active_bucket={self.active_bucket.isoformat()} "
            f"latest_seen_timestamp="
            f"{None if self.latest_seen_timestamp is None else self.latest_seen_timestamp.isoformat()} "
            f"reorder_window_seconds={self.reorder_window_seconds:.3f} "
            f"lateness_seconds={self.lateness_seconds:.3f})."
        )

    def diagnostics(self):
        return {
            "trade_timestamp": self.trade_timestamp,
            "trade_bucket": self.trade_bucket,
            "active_bucket": self.active_bucket,
            "latest_seen_timestamp": self.latest_seen_timestamp,
            "watermark_timestamp": self.watermark_timestamp,
            "reorder_window_seconds": self.reorder_window_seconds,
            "lateness_seconds": self.lateness_seconds,
        }


class CoinbaseOneMinuteTradeAggregator:
    """Aggregate Coinbase public market trades into completed one-minute OHLCV bars.

    The current minute is never emitted. A bar is returned only after a trade from
    a later minute proves the previous bucket has completed.
    """

    def __init__(self, product_id="BTC-USD", reorder_window="2s"):
        if not isinstance(product_id, str) or not product_id.strip():
            raise ValueError("product_id is required.")
        self.product_id = product_id.strip().upper()
        self.reorder_window = pd.Timedelta(reorder_window)
        if self.reorder_window < pd.Timedelta(0):
            raise ValueError("reorder_window cannot be negative.")
        self._bucket = None
        self._ohlcv = None
        self._pending_trades = []
        self._latest_seen_ts = None
        self._arrival_sequence = 0

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
            raise CoinbaseTradeOrderingError(
                trade_timestamp=ts,
                trade_bucket=bucket,
                active_bucket=self._bucket,
                latest_seen_timestamp=self._latest_seen_ts,
                reorder_window=self.reorder_window,
            )
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

        # Coinbase messages can arrive slightly out of event-time order across
        # websocket frames. Buffer a small event-time window before handing trades
        # to the strict minute aggregator. This preserves OHLCV correctness instead
        # of silently dropping a late trade after its minute has already been emitted.
        for event in message.get("events", []):
            for trade in event.get("trades", []):
                ts = self._timestamp(trade.get("time"))
                self._arrival_sequence += 1
                heapq.heappush(self._pending_trades, (ts.value, self._arrival_sequence, dict(trade)))
                if self._latest_seen_ts is None or ts > self._latest_seen_ts:
                    self._latest_seen_ts = ts

        if self._latest_seen_ts is None:
            return []
        cutoff = self._latest_seen_ts - self.reorder_window
        completed = []
        while self._pending_trades and pd.Timestamp(self._pending_trades[0][0], tz="UTC") <= cutoff:
            _, _, trade = heapq.heappop(self._pending_trades)
            bar = self.ingest_trade(trade)
            if bar is not None:
                completed.append(bar)
        if self._bucket is not None and cutoff >= self._bucket + pd.Timedelta(minutes=1):
            completed.append(CoinbaseCompletedBar(self._bucket, *self._ohlcv))
            self._bucket = None
            self._ohlcv = None
        return completed

    def reset_stream_boundary(self):
        """Discard incomplete aggregation state across a transport reconnect.

        A reconnect can imply missed trades. Keeping a partial OHLCV bucket across
        that boundary could silently create a bar from incomplete market data, so
        the next connection must start from a clean aggregation boundary.
        """
        self._bucket = None
        self._ohlcv = None
        self._pending_trades = []
        self._latest_seen_ts = None
        self._arrival_sequence = 0

    def export_state(self):
        return {
            "bucket": None if self._bucket is None else pd.Timestamp(self._bucket).isoformat(),
            "ohlcv": self._ohlcv,
            "latest_seen_ts": None if self._latest_seen_ts is None else self._latest_seen_ts.isoformat(),
            "arrival_sequence": self._arrival_sequence,
            "pending_trades": [item[2] for item in sorted(self._pending_trades)],
        }

    def restore_state(self, state):
        state = state or {}
        self._bucket = pd.Timestamp(state["bucket"]) if state.get("bucket") else None
        self._ohlcv = state.get("ohlcv")
        self._latest_seen_ts = pd.Timestamp(state["latest_seen_ts"]) if state.get("latest_seen_ts") else None
        self._arrival_sequence = 0
        self._pending_trades = []
        for trade in state.get("pending_trades", []):
            ts = self._timestamp(trade.get("time"))
            self._arrival_sequence += 1
            heapq.heappush(self._pending_trades, (ts.value, self._arrival_sequence, dict(trade)))
        self._arrival_sequence = max(self._arrival_sequence, int(state.get("arrival_sequence", 0)))


class CoinbaseOneMinuteBarAdapter:
    """Translate completed Coinbase 1m bars into RealTimeMarketDataFeed schema."""

    def __init__(self, symbol="BTC/USD"):
        if not isinstance(symbol, str) or not symbol.strip():
            raise ValueError("symbol is required.")
        self.symbol = symbol.strip().upper()

    @staticmethod
    def freshness_reference(timestamp, timeframe):
        """Completed Coinbase bars are fresh relative to their interval close."""
        return pd.Timestamp(timestamp) + pd.Timedelta(timeframe)

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


class CoinbasePublicRestCandleClient:
    """Public REST fallback for completed Coinbase Exchange one-minute candles.

    The client is deliberately read-only and unauthenticated. It is used only to
    repair market-data continuity after websocket gaps; it has no order/execution
    capability. A request function can be injected for deterministic tests.
    """

    def __init__(self, product_id="BTC-USD", request_fn=None, timeout_seconds=10.0):
        if not isinstance(product_id, str) or not product_id.strip():
            raise ValueError("product_id is required.")
        if float(timeout_seconds) <= 0:
            raise ValueError("timeout_seconds must be positive.")
        self.product_id = product_id.strip().upper()
        self.request_fn = request_fn
        self.timeout_seconds = float(timeout_seconds)

    def _get(self, start, end):
        params = {
            "start": pd.Timestamp(start).isoformat(),
            "end": pd.Timestamp(end).isoformat(),
            "granularity": 60,
        }
        url = f"{COINBASE_EXCHANGE_REST_URL}/products/{self.product_id}/candles"
        if self.request_fn is not None:
            response = self.request_fn(url, params=params, timeout=self.timeout_seconds)
        else:
            import requests
            response = requests.get(url, params=params, timeout=self.timeout_seconds)
        raise_for_status = getattr(response, "raise_for_status", None)
        if callable(raise_for_status):
            raise_for_status()
        payload = response.json() if hasattr(response, "json") else response
        if not isinstance(payload, list):
            raise RuntimeError("Coinbase REST candle response must be a list.")
        return payload

    @staticmethod
    def _parse_row(row):
        if not isinstance(row, (list, tuple)) or len(row) < 6:
            raise RuntimeError("Coinbase REST candle row is invalid.")
        # Exchange REST shape: [time, low, high, open, close, volume].
        ts = pd.Timestamp(int(row[0]), unit="s", tz="UTC")
        low, high, open_, close, volume = map(float, row[1:6])
        return CoinbaseCompletedBar(ts, open_, high, low, close, volume)

    def fetch_range(self, start, end):
        """Return completed 1m bars for [start, end), chunking under REST limits."""
        start = pd.Timestamp(start)
        end = pd.Timestamp(end)
        if pd.isna(start) or pd.isna(end) or end <= start:
            return tuple()
        if start.tzinfo is None:
            start = start.tz_localize("UTC")
        if end.tzinfo is None:
            end = end.tz_localize("UTC")
        cursor = start.floor("min")
        end = end.floor("min")
        bars = {}
        # Coinbase Exchange REST allows at most 300 candles per request. Use a
        # smaller 299-minute window to keep inclusive endpoint semantics harmless.
        while cursor < end:
            chunk_end = min(cursor + pd.Timedelta(minutes=299), end)
            payload = self._get(cursor, chunk_end)
            for row in payload:
                bar = self._parse_row(row)
                if cursor <= bar.timestamp < end:
                    bars[bar.timestamp] = bar
            cursor = chunk_end
        return tuple(bars[key] for key in sorted(bars))


class CoinbaseHybridGapRecovery:
    """Recover exact missing 1m continuity with public REST candles.

    Recovery is fail-closed: every expected missing minute must be present exactly
    once. Historical bars are returned for state catch-up only; callers must not
    retroactively execute orders from them.
    """

    def __init__(self, rest_client=None, max_backfill_minutes=300,
                 max_startup_catchup_minutes=10080, max_attempts=3,
                 retry_backoff_seconds=2.0, sleep_fn=None):
        if not isinstance(max_backfill_minutes, int) or max_backfill_minutes <= 0:
            raise ValueError("max_backfill_minutes must be a positive integer.")
        if not isinstance(max_startup_catchup_minutes, int) or max_startup_catchup_minutes <= 0:
            raise ValueError("max_startup_catchup_minutes must be a positive integer.")
        if max_startup_catchup_minutes < max_backfill_minutes:
            raise ValueError("max_startup_catchup_minutes cannot be smaller than max_backfill_minutes.")
        if not isinstance(max_attempts, int) or max_attempts <= 0:
            raise ValueError("max_attempts must be a positive integer.")
        if float(retry_backoff_seconds) < 0:
            raise ValueError("retry_backoff_seconds cannot be negative.")
        self.rest_client = rest_client or CoinbasePublicRestCandleClient()
        self.max_backfill_minutes = max_backfill_minutes
        self.max_startup_catchup_minutes = max_startup_catchup_minutes
        self.max_attempts = max_attempts
        self.retry_backoff_seconds = float(retry_backoff_seconds)
        self.sleep_fn = sleep_fn or time.sleep

    def recover(self, last_accepted_timestamp, next_live_timestamp):
        return self._recover_with_limit(
            last_accepted_timestamp, next_live_timestamp, self.max_backfill_minutes, "REST backfill"
        )

    def recover_startup(self, last_accepted_timestamp, next_live_timestamp):
        """Catch up a bounded long process-downtime gap without retroactive trading.

        The REST client already chunks requests below Coinbase's per-request candle
        limit. This larger boundary is deliberately startup-only; reconnect recovery
        keeps the tighter normal-session safety limit.
        """
        return self._recover_with_limit(
            last_accepted_timestamp, next_live_timestamp,
            self.max_startup_catchup_minutes, "Startup catch-up"
        )

    def _recover_with_limit(self, last_accepted_timestamp, next_live_timestamp, limit, label):
        if last_accepted_timestamp is None:
            return tuple()
        last_ts = pd.Timestamp(last_accepted_timestamp)
        next_ts = pd.Timestamp(next_live_timestamp)
        start = last_ts + pd.Timedelta(minutes=1)
        end = next_ts
        if end <= start:
            return tuple()
        expected = list(pd.date_range(start=start, end=end - pd.Timedelta(minutes=1), freq="1min"))
        if len(expected) > limit:
            raise RuntimeError(
                f"{label} gap of {len(expected)} minutes exceeds safety limit of {limit}."
            )
        last_error = None
        for attempt in range(1, self.max_attempts + 1):
            try:
                bars = self.rest_client.fetch_range(start, end)
                by_ts = {pd.Timestamp(bar.timestamp): bar for bar in bars}
                missing = [ts for ts in expected if ts not in by_ts]
                if not missing:
                    return tuple(by_ts[ts] for ts in expected)
                last_error = RuntimeError(
                    f"Coinbase REST backfill incomplete: missing {len(missing)} of "
                    f"{len(expected)} required one-minute bars."
                )
            except Exception as exc:
                last_error = exc
            if attempt < self.max_attempts and self.retry_backoff_seconds:
                self.sleep_fn(self.retry_backoff_seconds * attempt)
        raise RuntimeError(f"Coinbase REST backfill failed after {self.max_attempts} attempts: {last_error}")


class CoinbasePublicWebSocketTransport:
    """Small replaceable transport for Coinbase public market-data websocket.

    Network access occurs only when iterated. A websocket factory can be injected
    for deterministic tests. Reconnect attempts are bounded.
    """

    def __init__(self, product_id="BTC-USD", websocket_factory=None,
                 max_reconnect_attempts=3, backoff_seconds=5.0,
                 backoff_factor=2.0, max_backoff_seconds=30.0, sleep_fn=None,
                 socket_timeout_seconds=30.0, ping_interval_seconds=20.0,
                 monotonic_fn=None):
        if max_reconnect_attempts < 0:
            raise ValueError("max_reconnect_attempts cannot be negative.")
        if backoff_seconds < 0:
            raise ValueError("backoff_seconds cannot be negative.")
        if backoff_factor < 1:
            raise ValueError("backoff_factor must be at least 1.")
        if max_backoff_seconds < 0:
            raise ValueError("max_backoff_seconds cannot be negative.")
        if socket_timeout_seconds <= 0:
            raise ValueError("socket_timeout_seconds must be greater than zero.")
        if ping_interval_seconds < 0:
            raise ValueError("ping_interval_seconds cannot be negative.")
        self.product_id = str(product_id).upper()
        self.websocket_factory = websocket_factory
        self.max_reconnect_attempts = int(max_reconnect_attempts)
        self.backoff_seconds = float(backoff_seconds)
        self.backoff_factor = float(backoff_factor)
        self.max_backoff_seconds = float(max_backoff_seconds)
        self.sleep_fn = sleep_fn or time.sleep
        self.socket_timeout_seconds = float(socket_timeout_seconds)
        self.ping_interval_seconds = float(ping_interval_seconds)
        self.monotonic_fn = monotonic_fn or time.monotonic

    def _backoff_for_attempt(self, attempt):
        delay = self.backoff_seconds * (self.backoff_factor ** max(0, attempt - 1))
        return min(delay, self.max_backoff_seconds)

    @property
    def subscription_messages(self):
        return (
            {"type": "subscribe", "product_ids": [self.product_id], "channel": "market_trades"},
            {"type": "subscribe", "channel": "heartbeats"},
        )

    @staticmethod
    def _failure_kind(exc):
        text = str(exc).lower()
        name = type(exc).__name__.lower()
        if isinstance(exc, socket.gaierror) or "getaddrinfo" in text or "address" in name:
            return "DNS"
        if isinstance(exc, ConnectionResetError) or "10054" in text or "forcibly closed" in text or "reset" in name:
            return "RESET"
        if isinstance(exc, TimeoutError) or "timeout" in name or "timed out" in text:
            return "TIMEOUT"
        if isinstance(exc, ConnectionError) or "closed" in text:
            return "CLOSED"
        return "OTHER"

    def _connect(self):
        if self.websocket_factory is not None:
            return self.websocket_factory(COINBASE_WS_URL)
        try:
            from websocket import create_connection
        except ImportError as exc:
            raise RuntimeError("websocket-client is required for Coinbase transport.") from exc
        return create_connection(COINBASE_WS_URL, timeout=self.socket_timeout_seconds)

    def _maybe_ping(self, ws, last_ping_at):
        if self.ping_interval_seconds <= 0:
            return last_ping_at
        now = self.monotonic_fn()
        if now - last_ping_at < self.ping_interval_seconds:
            return last_ping_at
        ping = getattr(ws, "ping", None)
        if callable(ping):
            ping("ai-quant-keepalive")
        return now

    def __iter__(self):
        consecutive_failures = 0
        reconnect_count = 0
        reconnect_pending = False
        outage_started_at = None
        while True:
            ws = None
            try:
                ws = self._connect()
                for payload in self.subscription_messages:
                    ws.send(json.dumps(payload))
                last_ping_at = self.monotonic_fn()
                while True:
                    last_ping_at = self._maybe_ping(ws, last_ping_at)
                    raw = ws.recv()
                    if raw is None or raw == "":
                        raise ConnectionError("Coinbase websocket closed.")
                    message = json.loads(raw) if isinstance(raw, str) else raw
                    if reconnect_pending:
                        reconnect_count += 1
                        consecutive_failures = 0
                        reconnect_pending = False
                        outage_seconds = None
                        if outage_started_at is not None:
                            outage_seconds = max(0.0, self.monotonic_fn() - outage_started_at)
                        outage_started_at = None
                        yield {
                            "channel": "_coinbase_transport",
                            "event": "RECONNECTED",
                            "reconnect_count": reconnect_count,
                            "outage_seconds": outage_seconds,
                        }
                    yield message
            except GeneratorExit:
                raise
            except Exception as exc:
                consecutive_failures += 1
                reason = f"{type(exc).__name__}: {exc}"
                failure_kind = self._failure_kind(exc)
                if outage_started_at is None:
                    outage_started_at = self.monotonic_fn()
                if consecutive_failures > self.max_reconnect_attempts:
                    yield {
                        "channel": "_coinbase_transport",
                        "event": "RECONNECT_EXHAUSTED",
                        "attempt": consecutive_failures,
                        "reason": reason,
                        "failure_kind": failure_kind,
                        "outage_seconds": max(0.0, self.monotonic_fn() - outage_started_at),
                    }
                    return
                reconnect_pending = True
                yield {
                    "channel": "_coinbase_transport",
                    "event": "DISCONNECTED",
                    "attempt": consecutive_failures,
                    "reason": reason,
                    "failure_kind": failure_kind,
                }
                delay = self._backoff_for_attempt(consecutive_failures)
                if delay:
                    self.sleep_fn(delay)
            finally:
                if ws is not None:
                    try:
                        ws.close()
                    except Exception:
                        pass
