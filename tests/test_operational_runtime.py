import json

import pandas as pd
import pytest

from src.operational_runtime import JsonCheckpointStore, PaperOperationalRuntime
from src.paper_broker import PaperBroker
from src.paper_trading import PaperTradingEngine, PaperTradingSession
from src.realtime_market_data import AlpacaCryptoBarAdapter, RealTimeMarketDataFeed
from src.risk_engine import RiskEngine


class SignalStrategy:
    def __init__(self, signal=0):
        self.signal = signal

    def run(self, data):
        result = data.copy()
        result["Signal"] = self.signal
        return result


def bar(ts="2026-08-08T10:00:00Z", close=100.0):
    return {"T": "b", "S": "BTC/USD", "t": ts, "o": close, "h": close + 1,
            "l": close - 1, "c": close, "v": 5}


def make_runtime(tmp_path, signal=0, checkpoint=True, max_failures=3):
    broker = PaperBroker(initial_cash=10000)
    risk = RiskEngine(risk_per_trade=0.01, max_position_fraction=0.5, max_drawdown_fraction=0.2)
    engine = PaperTradingEngine(SignalStrategy(signal), risk, broker)
    session = PaperTradingSession(engine)
    feed = RealTimeMarketDataFeed(AlpacaCryptoBarAdapter(), stale_after="2min", max_gap="2min")
    store = JsonCheckpointStore(tmp_path / "runtime.json") if checkpoint else None
    runtime = PaperOperationalRuntime(feed, session, store, checkpoint_every=1,
                                      max_consecutive_failures=max_failures,
                                      clock=lambda: pd.Timestamp("2026-08-08T10:00:30Z"))
    return runtime


def test_runtime_processes_healthy_event(tmp_path):
    runtime = make_runtime(tmp_path)
    snapshot = runtime.process_provider_message(bar(), received_at="2026-08-08T10:00:30Z")
    assert snapshot.sequence == 1
    assert runtime.health.status == "HEALTHY"
    assert runtime.health.processed_events == 1


def test_unhealthy_feed_is_fail_closed_before_session(tmp_path):
    runtime = make_runtime(tmp_path)
    assert runtime.process_provider_message(bar("2026-08-08T09:00:00Z"), received_at="2026-08-08T10:00:30Z") is None
    assert runtime.health.status == "DEGRADED"
    assert runtime.health.processed_events == 0
    assert runtime.health.rejected_events == 1
    assert runtime.session.snapshot_history == ()


def test_repeated_feed_failures_halt_runtime(tmp_path):
    runtime = make_runtime(tmp_path, max_failures=2)
    runtime.process_provider_message(bar("2026-08-08T09:00:00Z"), received_at="2026-08-08T10:00:30Z")
    runtime.process_provider_message(bar("2026-08-08T09:01:00Z"), received_at="2026-08-08T10:00:30Z")
    assert runtime.health.status == "HALTED"
    assert runtime.stop_requested is True


def test_unknown_processing_error_halts_instead_of_continuing(tmp_path):
    runtime = make_runtime(tmp_path, signal=1)
    # BUY without a stop is a strategy/risk orchestration error and must halt.
    assert runtime.process_provider_message(bar(), received_at="2026-08-08T10:00:30Z") is None
    assert runtime.health.status == "HALTED"
    assert "ValueError" in runtime.health.reason


def test_checkpoint_is_written_atomically_after_event(tmp_path):
    runtime = make_runtime(tmp_path)
    runtime.process_provider_message(bar(), received_at="2026-08-08T10:00:30Z")
    payload = json.loads((tmp_path / "runtime.json").read_text())
    assert payload["version"] == 1
    assert payload["runtime"]["processed_events"] == 1
    assert not (tmp_path / "runtime.json.tmp").exists()


def test_checkpoint_restores_open_position_and_continuity(tmp_path):
    runtime = make_runtime(tmp_path, signal=1)
    runtime.process_provider_message(bar(), stop_price=95, received_at="2026-08-08T10:00:30Z")
    qty = runtime.session.engine.paper_broker.position_quantity
    assert qty > 0

    restored = make_runtime(tmp_path, signal=0)
    assert restored.restore() is True
    broker = restored.session.engine.paper_broker
    assert broker.position_quantity == pytest.approx(qty)
    assert restored.session._last_timestamp == pd.Timestamp("2026-08-08T10:00:00Z")
    assert restored.realtime_feed._last_timestamp == pd.Timestamp("2026-08-08T10:00:00Z")
    assert restored.health.status == "HEALTHY"


def test_restore_preserves_risk_kill_switch(tmp_path):
    runtime = make_runtime(tmp_path)
    risk = runtime.session.engine.risk_engine
    risk.kill_switch_active = True
    risk.kill_switch_reason = "Maximum drawdown limit reached."
    runtime.checkpoint_store.save(runtime)
    restored = make_runtime(tmp_path)
    restored.restore()
    assert restored.session.engine.risk_engine.kill_switch_active is True


def test_corrupt_checkpoint_fails_loudly(tmp_path):
    path = tmp_path / "runtime.json"
    path.write_text("{broken")
    store = JsonCheckpointStore(path)
    with pytest.raises(RuntimeError, match="cannot be read safely"):
        store.load()


def test_unsupported_checkpoint_version_is_rejected(tmp_path):
    path = tmp_path / "runtime.json"
    path.write_text('{"version": 999}')
    with pytest.raises(RuntimeError, match="Unsupported"):
        JsonCheckpointStore(path).load()


def test_graceful_shutdown_checkpoints_and_blocks_new_events(tmp_path):
    runtime = make_runtime(tmp_path)
    health = runtime.request_shutdown()
    assert health.status == "STOPPING"
    assert (tmp_path / "runtime.json").exists()
    with pytest.raises(RuntimeError, match="stopping"):
        runtime.process_provider_message(bar(), received_at="2026-08-08T10:00:30Z")


def test_run_consumes_transport_and_shuts_down_gracefully(tmp_path):
    runtime = make_runtime(tmp_path)
    health = runtime.run([bar()], stop_policy=None)
    assert health.status == "STOPPING"
    assert health.processed_events == 1
    assert runtime.stop_requested is True


def test_restore_without_existing_checkpoint_is_noop(tmp_path):
    runtime = make_runtime(tmp_path)
    assert runtime.restore() is False

from src.operational_runtime import AlpacaWebSocketTransport


class FakeSocket:
    def __init__(self, responses):
        self.responses = iter(responses)
        self.sent = []
        self.closed = False
    def send(self, value):
        self.sent.append(json.loads(value))
    def recv(self):
        return next(self.responses)
    def close(self):
        self.closed = True


def test_alpaca_transport_authenticates_subscribes_and_yields_bars():
    socket = FakeSocket([
        json.dumps([{"T": "success", "msg": "authenticated"}]),
        json.dumps([bar()]),
        None,
    ])
    transport = AlpacaWebSocketTransport(lambda url: socket, "key", "secret", sleeper=lambda _: None)
    messages = list(transport)
    assert messages == [bar()]
    assert socket.sent[0]["action"] == "auth"
    assert socket.sent[1] == {"action": "subscribe", "bars": ["BTC/USD"]}
    assert socket.closed is True


def test_alpaca_transport_reconnects_after_connection_failure():
    first = FakeSocket([])
    def fail_recv():
        raise ConnectionError("down")
    first.recv = fail_recv
    second = FakeSocket([json.dumps([bar()]), None])
    sockets = iter([first, second])
    transport = AlpacaWebSocketTransport(lambda url: next(sockets), "key", "secret",
                                         max_reconnects=1, sleeper=lambda _: None)
    assert list(transport) == [bar()]
    assert transport.reconnects == 1


def test_alpaca_transport_requires_credentials():
    with pytest.raises(ValueError, match="credentials"):
        AlpacaWebSocketTransport(lambda url: None, "", "secret")
