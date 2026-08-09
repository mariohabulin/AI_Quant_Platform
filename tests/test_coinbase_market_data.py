import json

import pandas as pd
import pytest

from src.coinbase_market_data import (
    COINBASE_WS_URL,
    CoinbaseOneMinuteBarAdapter,
    CoinbaseOneMinuteTradeAggregator,
    CoinbasePublicWebSocketTransport,
)
from src.realtime_market_data import FeedHealthError, RealTimeMarketDataFeed


def trade(time, price, size="0.1", product_id="BTC-USD"):
    return {"time": time, "price": str(price), "size": str(size), "product_id": product_id}


def test_aggregator_emits_only_completed_minute():
    agg = CoinbaseOneMinuteTradeAggregator()
    assert agg.ingest_trade(trade("2026-08-08T12:00:05Z", 100)) is None
    assert agg.ingest_trade(trade("2026-08-08T12:00:40Z", 110, "0.2")) is None
    bar = agg.ingest_trade(trade("2026-08-08T12:01:01Z", 105))
    assert bar.timestamp == pd.Timestamp("2026-08-08T12:00:00Z")
    assert (bar.open, bar.high, bar.low, bar.close, bar.volume) == pytest.approx((100, 110, 100, 110, 0.3))


def test_aggregator_rejects_wrong_product_and_out_of_order_trade():
    agg = CoinbaseOneMinuteTradeAggregator()
    with pytest.raises(ValueError):
        agg.ingest_trade(trade("2026-08-08T12:00:01Z", 100, product_id="ETH-USD"))
    agg.ingest_trade(trade("2026-08-08T12:01:01Z", 100))
    with pytest.raises(ValueError):
        agg.ingest_trade(trade("2026-08-08T12:00:59Z", 99))


def test_market_trades_message_can_emit_completed_bar():
    agg = CoinbaseOneMinuteTradeAggregator()
    first = {"channel": "market_trades", "events": [{"trades": [trade("2026-08-08T12:00:10Z", 100)]}]}
    second = {"channel": "market_trades", "events": [{"trades": [trade("2026-08-08T12:01:01Z", 101)]}]}
    assert agg.ingest_message(first) == []
    assert agg.ingest_message(second) == []
    third = {"channel": "market_trades", "events": [{"trades": [trade("2026-08-08T12:01:03Z", 102)]}]}
    bars = agg.ingest_message(third)
    assert len(bars) == 1 and bars[0].close == 100
    assert agg.ingest_message({"channel": "heartbeats", "events": []}) == []


def test_completed_bar_adapter_integrates_with_existing_feed_health():
    agg = CoinbaseOneMinuteTradeAggregator()
    agg.ingest_trade(trade("2026-08-08T12:00:10Z", 100))
    bar = agg.ingest_trade(trade("2026-08-08T12:01:01Z", 101))
    feed = RealTimeMarketDataFeed(CoinbaseOneMinuteBarAdapter(), stale_after="2min", max_gap="2min")
    event = feed.ingest(bar, received_at="2026-08-08T12:01:05Z")
    assert event.timestamp == pd.Timestamp("2026-08-08T12:00:00Z")
    assert event.data.iloc[-1]["Close"] == 100
    assert feed.health.status == "HEALTHY"


def test_completed_bar_freshness_is_measured_from_interval_close():
    feed = RealTimeMarketDataFeed(
        CoinbaseOneMinuteBarAdapter(), stale_after="10s", max_gap="2min"
    )
    completed = {
        "timestamp": "2026-08-08T12:00:00Z", "open": 100,
        "high": 101, "low": 99, "close": 100, "volume": 1,
    }
    event = feed.ingest(completed, received_at="2026-08-08T12:01:05Z")
    assert event.timestamp == pd.Timestamp("2026-08-08T12:00:00Z")
    assert feed.health.status == "HEALTHY"


def test_completed_bar_is_stale_after_close_plus_tolerance():
    feed = RealTimeMarketDataFeed(
        CoinbaseOneMinuteBarAdapter(), stale_after="10s", max_gap="2min"
    )
    completed = {
        "timestamp": "2026-08-08T12:00:00Z", "open": 100,
        "high": 101, "low": 99, "close": 100, "volume": 1,
    }
    with pytest.raises(FeedHealthError, match="stale"):
        feed.ingest(completed, received_at="2026-08-08T12:01:11Z")


def test_adapter_rejects_invalid_completed_bar_geometry():
    adapter = CoinbaseOneMinuteBarAdapter()
    with pytest.raises(ValueError):
        adapter.normalize({
            "timestamp": "2026-08-08T12:00:00Z", "open": 100,
            "high": 99, "low": 98, "close": 100, "volume": 1,
        })


def test_transport_builds_public_market_trades_and_heartbeat_subscriptions():
    transport = CoinbasePublicWebSocketTransport()
    assert transport.product_id == "BTC-USD"
    assert transport.subscription_messages == (
        {"type": "subscribe", "product_ids": ["BTC-USD"], "channel": "market_trades"},
        {"type": "subscribe", "channel": "heartbeats"},
    )
    assert COINBASE_WS_URL.startswith("wss://")


def test_transport_uses_injected_websocket_without_credentials():
    class FakeSocket:
        def __init__(self):
            self.sent = []
            self.messages = [json.dumps({"channel": "heartbeats", "events": []})]
        def send(self, payload): self.sent.append(json.loads(payload))
        def recv(self):
            if self.messages:
                return self.messages.pop(0)
            raise KeyboardInterrupt()
        def close(self): pass

    sock = FakeSocket()
    transport = CoinbasePublicWebSocketTransport(websocket_factory=lambda url: sock, max_reconnect_attempts=0)
    iterator = iter(transport)
    assert next(iterator)["channel"] == "heartbeats"
    assert sock.sent == list(transport.subscription_messages)


def test_market_trades_batch_is_normalized_chronologically_across_minute_boundary():
    aggregator = CoinbaseOneMinuteTradeAggregator(product_id="BTC-USD")
    message = {
        "channel": "market_trades",
        "events": [
            {
                "type": "update",
                "trades": [
                    {"product_id": "BTC-USD", "price": "101", "size": "0.2", "time": "2026-08-08T12:01:00.100Z"},
                    {"product_id": "BTC-USD", "price": "100", "size": "0.1", "time": "2026-08-08T12:00:59.900Z"},
                ],
            }
        ],
    }

    assert aggregator.ingest_message(message) == []
    bars = aggregator.ingest_message({
        "channel": "market_trades",
        "events": [{"trades": [trade("2026-08-08T12:01:03Z", 102)]}],
    })

    assert len(bars) == 1
    assert bars[0].timestamp == pd.Timestamp("2026-08-08T12:00:00Z")
    assert bars[0].open == 100.0
    assert bars[0].close == 100.0
    assert bars[0].volume == 0.1


def test_cross_message_late_trade_is_reordered_before_minute_is_finalized():
    aggregator = CoinbaseOneMinuteTradeAggregator(product_id="BTC-USD", reorder_window="2s")
    messages = [
        {"channel": "market_trades", "events": [{"trades": [trade("2026-08-08T12:00:59.900Z", 100, "0.1")]}]},
        {"channel": "market_trades", "events": [{"trades": [trade("2026-08-08T12:01:00.150Z", 101, "0.2")]}]},
        {"channel": "market_trades", "events": [{"trades": [trade("2026-08-08T12:00:59.950Z", 102, "0.3")]}]},
        {"channel": "market_trades", "events": [{"trades": [trade("2026-08-08T12:01:03.000Z", 103, "0.4")]}]},
    ]
    bars = []
    for message in messages:
        bars.extend(aggregator.ingest_message(message))
    assert len(bars) == 1
    assert bars[0].timestamp == pd.Timestamp("2026-08-08T12:00:00Z")
    assert (bars[0].open, bars[0].high, bars[0].low, bars[0].close, bars[0].volume) == pytest.approx((100, 102, 100, 102, 0.4))


def test_reorder_buffer_state_round_trips_without_losing_pending_trade():
    aggregator = CoinbaseOneMinuteTradeAggregator(reorder_window="2s")
    aggregator.ingest_message({"channel": "market_trades", "events": [{"trades": [trade("2026-08-08T12:00:59.900Z", 100)]}]})
    state = aggregator.export_state()
    restored = CoinbaseOneMinuteTradeAggregator(reorder_window="2s")
    restored.restore_state(state)
    bars = restored.ingest_message({"channel": "market_trades", "events": [{"trades": [trade("2026-08-08T12:01:03.000Z", 101)]}]})
    assert len(bars) == 1
    assert bars[0].timestamp == pd.Timestamp("2026-08-08T12:00:00Z")
    assert bars[0].close == pytest.approx(100.0)


def test_transport_reconnect_budget_resets_after_successful_reconnect():
    class FakeSocket:
        def __init__(self, messages):
            self.messages = list(messages)
            self.sent = []
        def send(self, payload):
            self.sent.append(json.loads(payload))
        def recv(self):
            if not self.messages:
                raise ConnectionError("simulated disconnect")
            item = self.messages.pop(0)
            if isinstance(item, Exception):
                raise item
            return json.dumps(item)
        def close(self):
            pass

    sockets = [
        FakeSocket([{"channel": "heartbeats", "events": []}]),
        FakeSocket([{"channel": "heartbeats", "events": []}]),
        FakeSocket([{"channel": "heartbeats", "events": []}]),
    ]
    calls = []
    def factory(url):
        calls.append(url)
        return sockets[len(calls) - 1]

    transport = CoinbasePublicWebSocketTransport(
        websocket_factory=factory,
        max_reconnect_attempts=1,
        backoff_seconds=0,
    )
    iterator = iter(transport)
    sequence = [next(iterator) for _ in range(7)]
    assert [item.get("event") for item in sequence if item.get("channel") == "_coinbase_transport"] == [
        "DISCONNECTED", "RECONNECTED", "DISCONNECTED", "RECONNECTED"
    ]
    assert sum(item.get("channel") == "heartbeats" for item in sequence) == 3
    assert len(calls) == 3
    assert all(sock.sent == list(transport.subscription_messages) for sock in sockets)


def test_aggregator_reset_stream_boundary_discards_partial_and_pending_state():
    aggregator = CoinbaseOneMinuteTradeAggregator(reorder_window="2s")
    aggregator.ingest_message({
        "channel": "market_trades",
        "events": [{"trades": [trade("2026-08-08T12:00:59.900Z", 100)]}],
    })
    assert aggregator.export_state()["pending_trades"]
    aggregator.reset_stream_boundary()
    state = aggregator.export_state()
    assert state["bucket"] is None
    assert state["ohlcv"] is None
    assert state["pending_trades"] == []
    assert state["latest_seen_ts"] is None


def test_transport_uses_bounded_exponential_backoff_for_consecutive_failures():
    sleeps = []
    def failing_factory(url):
        raise OSError("dns unavailable")

    transport = CoinbasePublicWebSocketTransport(
        websocket_factory=failing_factory,
        max_reconnect_attempts=3,
        backoff_seconds=5,
        backoff_factor=2,
        max_backoff_seconds=12,
        sleep_fn=sleeps.append,
    )
    iterator = iter(transport)
    assert next(iterator)["event"] == "DISCONNECTED"
    assert next(iterator)["event"] == "DISCONNECTED"
    assert next(iterator)["event"] == "DISCONNECTED"
    assert next(iterator)["event"] == "RECONNECT_EXHAUSTED"
    assert sleeps == [5.0, 10.0, 12.0]


def test_transport_classifies_failure_and_reports_outage_duration_on_reconnect():
    class Clock:
        def __init__(self):
            self.value = 100.0

        def __call__(self):
            return self.value

    clock = Clock()

    class FakeSocket:
        def __init__(self, items):
            self.items = list(items)
            self.sent = []

        def send(self, payload):
            self.sent.append(json.loads(payload))

        def recv(self):
            item = self.items.pop(0)
            if isinstance(item, Exception):
                clock.value += 3.0
                raise item
            clock.value += 2.0
            return json.dumps(item)

        def close(self):
            pass

    sockets = [
        FakeSocket([ConnectionResetError(10054, "forcibly closed")]),
        FakeSocket([{"channel": "heartbeats", "events": []}]),
    ]
    calls = []

    def factory(url):
        index = len(calls)
        calls.append(url)
        return sockets[index]

    transport = CoinbasePublicWebSocketTransport(
        websocket_factory=factory,
        max_reconnect_attempts=2,
        backoff_seconds=0,
        monotonic_fn=clock,
    )
    iterator = iter(transport)
    disconnected = next(iterator)
    reconnected = next(iterator)
    heartbeat = next(iterator)

    assert disconnected["event"] == "DISCONNECTED"
    assert disconnected["failure_kind"] == "RESET"
    assert reconnected["event"] == "RECONNECTED"
    assert reconnected["outage_seconds"] == pytest.approx(2.0)
    assert heartbeat["channel"] == "heartbeats"


def test_transport_sends_protocol_ping_on_long_lived_connection():
    class Clock:
        def __init__(self):
            self.value = 0.0

        def __call__(self):
            return self.value

    clock = Clock()

    class FakeSocket:
        def __init__(self):
            self.sent = []
            self.pings = []
            self.reads = 0

        def send(self, payload):
            self.sent.append(json.loads(payload))

        def ping(self, payload):
            self.pings.append(payload)

        def recv(self):
            self.reads += 1
            clock.value += 6.0
            if self.reads <= 3:
                return json.dumps({"channel": "heartbeats", "events": []})
            raise KeyboardInterrupt()

        def close(self):
            pass

    sock = FakeSocket()
    transport = CoinbasePublicWebSocketTransport(
        websocket_factory=lambda url: sock,
        max_reconnect_attempts=0,
        ping_interval_seconds=5,
        monotonic_fn=clock,
    )
    iterator = iter(transport)

    assert next(iterator)["channel"] == "heartbeats"
    assert next(iterator)["channel"] == "heartbeats"
    assert next(iterator)["channel"] == "heartbeats"
    assert sock.pings == ["ai-quant-keepalive", "ai-quant-keepalive"]


def test_public_rest_candle_client_parses_and_sorts_one_minute_candles():
    from src.coinbase_market_data import CoinbasePublicRestCandleClient

    class Response:
        def raise_for_status(self):
            return None
        def json(self):
            return [
                [1786276920, "99", "103", "100", "102", "2.5"],
                [1786276860, "98", "102", "99", "101", "1.5"],
            ]

    calls = []
    def request(url, params, timeout):
        calls.append((url, params, timeout))
        return Response()

    client = CoinbasePublicRestCandleClient(request_fn=request)
    bars = client.fetch_range("2026-08-09T12:01:00Z", "2026-08-09T12:03:00Z")
    assert [bar.timestamp for bar in bars] == [
        pd.Timestamp("2026-08-09T12:01:00Z"),
        pd.Timestamp("2026-08-09T12:02:00Z"),
    ]
    assert bars[0].open == pytest.approx(99.0)
    assert bars[0].high == pytest.approx(102.0)
    assert bars[0].low == pytest.approx(98.0)
    assert bars[0].close == pytest.approx(101.0)
    assert calls[0][1]["granularity"] == 60


def test_hybrid_gap_recovery_requires_exact_minute_coverage():
    from src.coinbase_market_data import CoinbaseCompletedBar, CoinbaseHybridGapRecovery

    class Rest:
        def fetch_range(self, start, end):
            return (
                CoinbaseCompletedBar(pd.Timestamp("2026-08-09T12:01:00Z"), 1, 1, 1, 1, 1),
                CoinbaseCompletedBar(pd.Timestamp("2026-08-09T12:03:00Z"), 1, 1, 1, 1, 1),
            )

    recovery = CoinbaseHybridGapRecovery(rest_client=Rest(), max_attempts=1, sleep_fn=lambda _: None)
    with pytest.raises(RuntimeError, match="incomplete"):
        recovery.recover("2026-08-09T12:00:00Z", "2026-08-09T12:04:00Z")


def test_hybrid_gap_recovery_returns_exact_missing_minutes_in_order():
    from src.coinbase_market_data import CoinbaseCompletedBar, CoinbaseHybridGapRecovery

    class Rest:
        def fetch_range(self, start, end):
            return tuple(
                CoinbaseCompletedBar(ts, 1, 1, 1, 1, 1)
                for ts in [
                    pd.Timestamp("2026-08-09T12:03:00Z"),
                    pd.Timestamp("2026-08-09T12:01:00Z"),
                    pd.Timestamp("2026-08-09T12:02:00Z"),
                ]
            )

    recovery = CoinbaseHybridGapRecovery(rest_client=Rest())
    bars = recovery.recover("2026-08-09T12:00:00Z", "2026-08-09T12:04:00Z")
    assert [bar.timestamp for bar in bars] == list(pd.date_range("2026-08-09T12:01:00Z", periods=3, freq="1min"))
