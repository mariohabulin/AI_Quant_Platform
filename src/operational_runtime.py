from dataclasses import asdict, dataclass
from datetime import date
import json
from pathlib import Path
import time

import pandas as pd

from src.realtime_market_data import FeedHealthError


@dataclass(frozen=True)
class RuntimeHealth:
    status: str
    processed_events: int
    rejected_events: int
    consecutive_failures: int
    last_heartbeat_at: object = None
    last_event_at: object = None
    reason: str = ""


class JsonCheckpointStore:
    """Minimal durable state store for one paper-trading runtime.

    Checkpoints intentionally contain account, risk-protection and session/feed
    continuity state only. Strategy models and configuration remain code/config
    concerns and are rebuilt before restore.
    """

    VERSION = 1

    def __init__(self, path):
        self.path = Path(path)

    def save(self, runtime):
        payload = runtime.export_checkpoint()
        self.path.parent.mkdir(parents=True, exist_ok=True)
        temporary = self.path.with_suffix(self.path.suffix + ".tmp")
        temporary.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
        temporary.replace(self.path)
        return self.path

    def load(self):
        if not self.path.exists():
            return None
        try:
            payload = json.loads(self.path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            raise RuntimeError("Checkpoint cannot be read safely.") from exc
        if payload.get("version") != self.VERSION:
            raise RuntimeError("Unsupported checkpoint version.")
        return payload


class PaperOperationalRuntime:
    """Fail-safe operational boundary for controlled real-time paper trading.

    The runtime owns transport/event handling, heartbeat, exception isolation,
    checkpointing and shutdown. It never creates strategy signals or risk rules.
    Unhealthy market data is rejected before PaperTradingSession is invoked.
    """

    def __init__(
        self,
        realtime_feed,
        session,
        checkpoint_store=None,
        heartbeat_interval=30.0,
        checkpoint_every=1,
        max_consecutive_failures=3,
        clock=None,
    ):
        if realtime_feed is None or session is None:
            raise ValueError("realtime_feed and session are required.")
        if heartbeat_interval <= 0:
            raise ValueError("heartbeat_interval must be positive.")
        if not isinstance(checkpoint_every, int) or checkpoint_every <= 0:
            raise ValueError("checkpoint_every must be a positive integer.")
        if not isinstance(max_consecutive_failures, int) or max_consecutive_failures <= 0:
            raise ValueError("max_consecutive_failures must be a positive integer.")
        self.realtime_feed = realtime_feed
        self.session = session
        self.checkpoint_store = checkpoint_store
        self.heartbeat_interval = float(heartbeat_interval)
        self.checkpoint_every = checkpoint_every
        self.max_consecutive_failures = max_consecutive_failures
        self.clock = clock or (lambda: pd.Timestamp.now(tz="UTC"))
        self._processed = 0
        self._rejected = 0
        self._failures = 0
        self._stop_requested = False
        self._last_event_at = None
        self._last_heartbeat_at = None
        self._health = RuntimeHealth("STARTING", 0, 0, 0, reason="Runtime initialized.")

    @property
    def health(self):
        return self._health

    @property
    def stop_requested(self):
        return self._stop_requested

    def _now(self):
        ts = pd.Timestamp(self.clock())
        if pd.isna(ts):
            raise ValueError("Runtime clock returned an invalid timestamp.")
        return ts

    def heartbeat(self, reason="Runtime healthy."):
        now = self._now()
        self._last_heartbeat_at = now
        self._health = RuntimeHealth(
            "STOPPING" if self._stop_requested else "HEALTHY",
            self._processed, self._rejected, self._failures,
            now, self._last_event_at, reason,
        )
        return self._health

    def request_shutdown(self, reason="Graceful shutdown requested."):
        self._stop_requested = True
        if self.checkpoint_store is not None:
            self.checkpoint_store.save(self)
        self.heartbeat(reason)
        return self._health

    def process_provider_message(self, provider_message, stop_price=None, target_price=None, received_at=None, reconcile_long_exit=False):
        if self._stop_requested:
            raise RuntimeError("Runtime is stopping and cannot accept new market data.")
        received = pd.Timestamp(received_at) if received_at is not None else self._now()
        try:
            market_event = self.realtime_feed.ingest(provider_message, received_at=received)
            snapshot = self.session.process(
                market_event.data,
                stop_price=stop_price,
                target_price=target_price,
                timestamp=market_event.timestamp,
                reconcile_long_exit=reconcile_long_exit,
            )
        except FeedHealthError as exc:
            self._rejected += 1
            self._failures += 1
            status = "HALTED" if self._failures >= self.max_consecutive_failures else "DEGRADED"
            if status == "HALTED":
                self._stop_requested = True
            self._health = RuntimeHealth(
                status, self._processed, self._rejected, self._failures,
                self._last_heartbeat_at, self._last_event_at, str(exc),
            )
            if self.checkpoint_store is not None:
                self.checkpoint_store.save(self)
            return None
        except Exception as exc:
            # Unknown strategy/risk/execution failures are fail-closed: stop rather
            # than silently continuing with potentially corrupted trading state.
            self._rejected += 1
            self._failures += 1
            self._stop_requested = True
            self._health = RuntimeHealth(
                "HALTED", self._processed, self._rejected, self._failures,
                self._last_heartbeat_at, self._last_event_at,
                f"Unhandled processing error: {type(exc).__name__}: {exc}",
            )
            if self.checkpoint_store is not None:
                self.checkpoint_store.save(self)
            return None

        self._processed += 1
        self._failures = 0
        self._last_event_at = market_event.timestamp
        self.heartbeat("Market event processed safely.")
        if self.checkpoint_store is not None and self._processed % self.checkpoint_every == 0:
            self.checkpoint_store.save(self)
        return snapshot

    def run(self, transport, stop_policy=None, target_policy=None):
        """Consume provider messages from any iterable transport.

        Network/WebSocket ownership stays replaceable: a transport only needs to
        yield provider messages. Policies may be callables returning a price.
        """
        if transport is None:
            raise ValueError("transport is required.")
        self.heartbeat("Runtime started.")
        for message in transport:
            if self._stop_requested:
                break
            stop = stop_policy(message) if callable(stop_policy) else stop_policy
            target = target_policy(message) if callable(target_policy) else target_policy
            self.process_provider_message(message, stop_price=stop, target_price=target)
        if not self._stop_requested:
            self.request_shutdown("Transport ended; graceful shutdown completed.")
        return self.health

    @staticmethod
    def _serialize_timestamp(value):
        return None if value is None else pd.Timestamp(value).isoformat()

    def export_checkpoint(self):
        broker = self.session.engine.paper_broker
        risk = self.session.engine.risk_engine
        feed = self.realtime_feed
        return {
            "version": JsonCheckpointStore.VERSION,
            "runtime": {
                "processed_events": self._processed,
                "rejected_events": self._rejected,
                "consecutive_failures": self._failures,
                "last_event_at": self._serialize_timestamp(self._last_event_at),
            },
            "broker": {
                "cash": broker.cash,
                "position_quantity": broker.position_quantity,
                "average_entry_price": broker.average_entry_price,
                "position_cost_basis": broker.position_cost_basis,
                "realized_pnl": broker.realized_pnl,
                "last_market_price": broker.last_market_price,
                "next_order_number": broker._next_order_number,
            },
            "risk": {
                "peak_equity": risk.peak_equity,
                "day_key": None if risk.day_key is None else risk.day_key.isoformat(),
                "day_start_equity": risk.day_start_equity,
                "week_key": None if risk.week_key is None else list(risk.week_key),
                "week_start_equity": risk.week_start_equity,
                "kill_switch_active": risk.kill_switch_active,
                "kill_switch_reason": risk.kill_switch_reason,
            },
            "session": {"last_timestamp": self._serialize_timestamp(self.session._last_timestamp)},
            "feed": {
                "last_timestamp": self._serialize_timestamp(feed._last_timestamp),
                "accepted_events": feed._accepted,
            },
        }

    def restore(self, payload=None):
        if payload is None:
            if self.checkpoint_store is None:
                raise ValueError("No checkpoint payload or store is available.")
            payload = self.checkpoint_store.load()
        if payload is None:
            return False
        if payload.get("version") != JsonCheckpointStore.VERSION:
            raise RuntimeError("Unsupported checkpoint version.")

        broker = self.session.engine.paper_broker
        b = payload["broker"]
        for name in ("cash", "position_quantity", "average_entry_price", "position_cost_basis", "realized_pnl"):
            value = float(b[name])
            if value < 0 and name != "realized_pnl":
                raise RuntimeError("Checkpoint contains invalid broker state.")
            setattr(broker, name, value)
        broker.last_market_price = b.get("last_market_price")
        broker._next_order_number = int(b["next_order_number"])

        risk = self.session.engine.risk_engine
        r = payload["risk"]
        risk.peak_equity = r.get("peak_equity")
        risk.day_key = date.fromisoformat(r["day_key"]) if r.get("day_key") else None
        risk.day_start_equity = r.get("day_start_equity")
        risk.week_key = tuple(r["week_key"]) if r.get("week_key") else None
        risk.week_start_equity = r.get("week_start_equity")
        risk.kill_switch_active = bool(r.get("kill_switch_active", False))
        risk.kill_switch_reason = r.get("kill_switch_reason")

        session_ts = payload.get("session", {}).get("last_timestamp")
        self.session._last_timestamp = pd.Timestamp(session_ts) if session_ts else None
        feed_state = payload.get("feed", {})
        feed_ts = feed_state.get("last_timestamp")
        self.realtime_feed._last_timestamp = pd.Timestamp(feed_ts) if feed_ts else None
        self.realtime_feed._accepted = int(feed_state.get("accepted_events", 0))

        runtime = payload.get("runtime", {})
        self._processed = int(runtime.get("processed_events", 0))
        self._rejected = int(runtime.get("rejected_events", 0))
        self._failures = 0
        last_event = runtime.get("last_event_at")
        self._last_event_at = pd.Timestamp(last_event) if last_event else None
        self._stop_requested = False
        self.heartbeat("Runtime restored from checkpoint.")
        return True

class AlpacaWebSocketTransport:
    """Small authenticated Alpaca websocket transport with bounded reconnect.

    ``websocket_factory`` is injected so the operational core has no hard
    dependency on a websocket library and remains deterministic in tests. The
    factory receives ``url`` and returns an object with send/recv/close.
    """

    def __init__(self, websocket_factory, api_key, api_secret, symbol="BTC/USD",
                 url="wss://stream.data.alpaca.markets/v1beta3/crypto/us",
                 max_reconnects=3, backoff_seconds=1.0, sleeper=None):
        if websocket_factory is None:
            raise ValueError("websocket_factory is required.")
        if not api_key or not api_secret:
            raise ValueError("Alpaca API credentials are required.")
        if not isinstance(max_reconnects, int) or max_reconnects < 0:
            raise ValueError("max_reconnects must be a non-negative integer.")
        if backoff_seconds < 0:
            raise ValueError("backoff_seconds cannot be negative.")
        self.websocket_factory = websocket_factory
        self.api_key = api_key
        self.api_secret = api_secret
        self.symbol = symbol
        self.url = url
        self.max_reconnects = max_reconnects
        self.backoff_seconds = float(backoff_seconds)
        self.sleeper = sleeper or time.sleep
        self.reconnects = 0
        self._socket = None

    def _connect(self):
        ws = self.websocket_factory(self.url)
        ws.send(json.dumps({"action": "auth", "key": self.api_key, "secret": self.api_secret}))
        ws.send(json.dumps({"action": "subscribe", "bars": [self.symbol]}))
        self._socket = ws
        return ws

    def __iter__(self):
        attempts = 0
        while True:
            try:
                ws = self._connect()
                while True:
                    raw = ws.recv()
                    if raw is None:
                        return
                    messages = json.loads(raw) if isinstance(raw, str) else raw
                    if isinstance(messages, dict):
                        messages = [messages]
                    if not isinstance(messages, list):
                        continue
                    for message in messages:
                        if isinstance(message, dict) and message.get("T") == "b":
                            yield message
            except (OSError, ConnectionError, json.JSONDecodeError):
                attempts += 1
                self.reconnects += 1
                if attempts > self.max_reconnects:
                    raise RuntimeError("Alpaca websocket reconnect budget exhausted.")
                self.sleeper(self.backoff_seconds * attempts)
            finally:
                if self._socket is not None:
                    try:
                        self._socket.close()
                    except Exception:
                        pass
                    self._socket = None
