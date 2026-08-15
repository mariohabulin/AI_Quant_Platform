import json

import pandas as pd
import pytest

from src.coinbase_market_data import (
    COINBASE_WS_URL,
    CoinbaseMessageSequenceError,
    CoinbaseMessageSequenceTracker,
    CoinbaseOneMinuteBarAdapter,
    CoinbaseOneMinuteTradeAggregator,
    CoinbasePublicWebSocketTransport,
    CoinbaseTradeOrderingError,
)
from src.realtime_market_data import FeedHealthError, RealTimeMarketDataFeed


def trade(time, price, size="0.1", product_id="BTC-USD"):
    return {"time": time, "price": str(price), "size": str(size), "product_id": product_id}


def sequenced_trade_message(sequence_num, time, price, *, trade_id, message_time=None):
    return {
        "channel": "market_trades",
        "timestamp": message_time or time,
        "sequence_num": sequence_num,
        "events": [{
            "type": "update",
            "trades": [{
                **trade(time, price),
                "trade_id": str(trade_id),
            }],
        }],
    }


def sequenced_control_message(channel, sequence_num, timestamp):
    return {
        "channel": channel,
        "timestamp": timestamp,
        "sequence_num": sequence_num,
        "events": [{}],
    }


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


def test_trade_beyond_reorder_window_fails_with_actionable_timing_evidence():
    aggregator = CoinbaseOneMinuteTradeAggregator(
        product_id="BTC-USD", reorder_window="2s"
    )
    aggregator.ingest_message({
        "channel": "market_trades",
        "events": [{"trades": [trade("2026-08-08T12:01:00.100Z", 101)]}],
    })
    aggregator.ingest_message({
        "channel": "market_trades",
        "events": [{"trades": [trade("2026-08-08T12:01:03.000Z", 103)]}],
    })

    with pytest.raises(CoinbaseTradeOrderingError) as captured:
        aggregator.ingest_message({
            "channel": "market_trades",
            "events": [{"trades": [trade("2026-08-08T12:00:59.000Z", 99)]}],
        })

    error = captured.value
    assert error.trade_timestamp == pd.Timestamp("2026-08-08T12:00:59Z")
    assert error.trade_bucket == pd.Timestamp("2026-08-08T12:00:00Z")
    assert error.active_bucket == pd.Timestamp("2026-08-08T12:01:00Z")
    assert error.latest_seen_timestamp == pd.Timestamp("2026-08-08T12:01:03Z")
    assert error.watermark_timestamp == pd.Timestamp("2026-08-08T12:01:01Z")
    assert error.reorder_window_seconds == pytest.approx(2.0)
    assert error.lateness_seconds == pytest.approx(2.0)
    assert "lateness_seconds=2.000" in str(error)


def test_genuine_late_trade_retains_provider_sequence_and_trade_identity():
    aggregator = CoinbaseOneMinuteTradeAggregator(
        product_id="BTC-USD", reorder_window="2s"
    )
    aggregator.ingest_message(sequenced_trade_message(
        80, "2026-08-08T12:01:00.100Z", 101,
        trade_id="9001", message_time="2026-08-08T12:01:00.200Z",
    ))
    aggregator.ingest_message(sequenced_trade_message(
        81, "2026-08-08T12:01:03.000Z", 103,
        trade_id="9002", message_time="2026-08-08T12:01:03.100Z",
    ))

    with pytest.raises(CoinbaseTradeOrderingError) as captured:
        aggregator.ingest_message(sequenced_trade_message(
            82, "2026-08-08T12:00:59.000Z", 99,
            trade_id="9003", message_time="2026-08-08T12:01:03.200Z",
        ))

    diagnostics = captured.value.diagnostics()
    assert diagnostics["trade_id"] == "9003"
    assert diagnostics["message_sequence_num"] == 82
    assert diagnostics["message_timestamp"] == pd.Timestamp(
        "2026-08-08T12:01:03.200Z"
    )
    assert diagnostics["event_type"] == "update"


@pytest.mark.parametrize("observed", [39, 40])
def test_transport_drops_out_of_order_or_duplicate_message_before_aggregation(
    observed,
):
    class FakeSocket:
        def __init__(self):
            self.sent = []
            self.messages = [
                sequenced_trade_message(
                    40, "2026-08-08T12:01:03Z", 103, trade_id="first"
                ),
                sequenced_trade_message(
                    observed, "2026-08-08T12:00:59Z", 99, trade_id="replay"
                ),
                sequenced_trade_message(
                    41, "2026-08-08T12:01:04Z", 104, trade_id="next"
                ),
            ]

        def send(self, payload):
            self.sent.append(json.loads(payload))

        def recv(self):
            return json.dumps(self.messages.pop(0))

        def close(self):
            pass

    transport = CoinbasePublicWebSocketTransport(
        websocket_factory=lambda _: FakeSocket(),
        max_reconnect_attempts=0,
        ping_interval_seconds=0,
    )
    iterator = iter(transport)

    first = next(iterator)
    replay = next(iterator)
    following = next(iterator)

    assert first["sequence_num"] == 40
    assert replay == {
        "channel": "_coinbase_transport",
        "event": "PROVIDER_MESSAGE_REPLAY_DROPPED",
        "failure_kind": "PROVIDER_SEQUENCE_REPLAY",
        "provider_channel": "market_trades",
        "previous_sequence_num": 40,
        "observed_sequence_num": observed,
        "message_timestamp": "2026-08-08T12:00:59Z",
        "trade_count": 1,
        "first_trade_id": "replay",
        "last_trade_id": "replay",
    }
    assert following["sequence_num"] == 41

    aggregator = CoinbaseOneMinuteTradeAggregator(reorder_window="2s")
    assert aggregator.ingest_message(first) == []
    assert aggregator.ingest_message(following) == []


def test_transport_turns_sequence_gap_into_reconnect_before_yielding_gap_message():
    class FakeSocket:
        def __init__(self, messages):
            self.sent = []
            self.messages = list(messages)

        def send(self, payload):
            self.sent.append(json.loads(payload))

        def recv(self):
            return json.dumps(self.messages.pop(0))

        def close(self):
            pass

    sockets = [
        FakeSocket([
            sequenced_trade_message(
                100, "2026-08-08T12:00:10Z", 100, trade_id="100"
            ),
            sequenced_trade_message(
                102, "2026-08-08T12:00:20Z", 102, trade_id="102"
            ),
        ]),
        FakeSocket([
            sequenced_trade_message(
                7, "2026-08-08T12:01:10Z", 103, trade_id="new-connection"
            ),
        ]),
    ]
    calls = []

    def factory(_):
        calls.append(True)
        return sockets[len(calls) - 1]

    transport = CoinbasePublicWebSocketTransport(
        websocket_factory=factory,
        max_reconnect_attempts=1,
        backoff_seconds=0,
        ping_interval_seconds=0,
    )
    iterator = iter(transport)

    assert next(iterator)["sequence_num"] == 100
    disconnected = next(iterator)
    assert disconnected["event"] == "DISCONNECTED"
    assert disconnected["failure_kind"] == "PROVIDER_SEQUENCE_GAP"
    assert disconnected["provider_channel"] == "market_trades"
    assert disconnected["previous_sequence_num"] == 100
    assert disconnected["expected_sequence_num"] == 101
    assert disconnected["observed_sequence_num"] == 102
    assert disconnected["message_timestamp"] == "2026-08-08T12:00:20Z"
    assert "expected_sequence_num=101" in disconnected["reason"]

    assert next(iterator)["event"] == "RECONNECTED"
    assert next(iterator)["sequence_num"] == 7
    assert len(calls) == 2


def test_transport_tracks_one_sequence_across_all_subscribed_channels():
    """Mirror the exact envelope ordering observed by the cloud probe."""

    class FakeSocket:
        def __init__(self):
            self.messages = [
                sequenced_trade_message(
                    0, "2026-08-15T17:39:50.500Z", 100, trade_id="snapshot"
                ),
                sequenced_control_message(
                    "subscriptions", 1, "2026-08-15T17:39:50.544801046Z"
                ),
                sequenced_control_message(
                    "subscriptions", 2, "2026-08-15T17:39:50.544834060Z"
                ),
                sequenced_trade_message(
                    3, "2026-08-15T17:39:50.620Z", 101, trade_id="update-1"
                ),
                sequenced_control_message(
                    "heartbeats", 4, "2026-08-15T17:39:50.635873127Z"
                ),
                sequenced_trade_message(
                    5, "2026-08-15T17:39:51.220Z", 102, trade_id="update-2"
                ),
            ]

        def send(self, _):
            pass

        def recv(self):
            return json.dumps(self.messages.pop(0))

        def close(self):
            pass

    iterator = iter(CoinbasePublicWebSocketTransport(
        websocket_factory=lambda _: FakeSocket(),
        max_reconnect_attempts=0,
        ping_interval_seconds=0,
    ))

    messages = [next(iterator) for _ in range(6)]

    assert [message["sequence_num"] for message in messages] == list(range(6))
    assert [message["channel"] for message in messages] == [
        "market_trades",
        "subscriptions",
        "subscriptions",
        "market_trades",
        "heartbeats",
        "market_trades",
    ]


def test_tracker_reports_channel_where_connection_wide_gap_is_observed():
    tracker = CoinbaseMessageSequenceTracker()
    tracker.observe(sequenced_trade_message(
        0, "2026-08-15T17:39:50.500Z", 100, trade_id="snapshot"
    ))
    tracker.observe(sequenced_control_message(
        "subscriptions", 1, "2026-08-15T17:39:50.544801046Z"
    ))

    with pytest.raises(CoinbaseMessageSequenceError) as captured:
        tracker.observe(sequenced_control_message(
            "heartbeats", 3, "2026-08-15T17:39:50.635873127Z"
        ))

    assert captured.value.failure_kind == "PROVIDER_SEQUENCE_GAP"
    assert captured.value.provider_channel == "heartbeats"
    assert captured.value.previous_sequence_num == 1
    assert captured.value.expected_sequence_num == 2
    assert captured.value.observed_sequence_num == 3


def test_sequence_recovery_budget_is_not_reset_by_heartbeat_only_connection():
    class FakeSocket:
        def __init__(self, messages):
            self.messages = list(messages)

        def send(self, _):
            pass

        def recv(self):
            return json.dumps(self.messages.pop(0))

        def close(self):
            pass

    sockets = [
        FakeSocket([
            sequenced_trade_message(
                10, "2026-08-08T12:00:10Z", 100, trade_id="10"
            ),
            sequenced_trade_message(
                12, "2026-08-08T12:00:20Z", 102, trade_id="12"
            ),
        ]),
        FakeSocket([
            {
                "channel": "heartbeats",
                "timestamp": "2026-08-08T12:00:21Z",
                "sequence_num": 0,
                "events": [],
            },
            {
                "channel": "market_trades",
                "timestamp": "2026-08-08T12:00:22Z",
                "events": [],
            },
        ]),
    ]
    calls = []

    def factory(_):
        calls.append(True)
        return sockets[len(calls) - 1]

    iterator = iter(CoinbasePublicWebSocketTransport(
        websocket_factory=factory,
        max_reconnect_attempts=1,
        backoff_seconds=0,
        ping_interval_seconds=0,
    ))

    assert next(iterator)["sequence_num"] == 10
    assert next(iterator)["event"] == "DISCONNECTED"
    assert next(iterator)["channel"] == "heartbeats"
    exhausted = next(iterator)
    assert exhausted["event"] == "RECONNECT_EXHAUSTED"
    assert exhausted["attempt"] == 2
    assert exhausted["failure_kind"] == "PROVIDER_SEQUENCE_MISSING"
    assert len(calls) == 2


@pytest.mark.parametrize(
    "message,kind",
    [
        ({"channel": "market_trades", "events": []}, "PROVIDER_SEQUENCE_MISSING"),
        (
            {"channel": "market_trades", "sequence_num": "1", "events": []},
            "PROVIDER_SEQUENCE_INVALID",
        ),
    ],
)
def test_sequence_tracker_fails_closed_on_missing_or_invalid_sequence(message, kind):
    tracker = CoinbaseMessageSequenceTracker()

    with pytest.raises(CoinbaseMessageSequenceError) as captured:
        tracker.observe(message)

    assert captured.value.failure_kind == kind


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


def test_startup_catchup_allows_bounded_gap_larger_than_reconnect_limit():
    from src.coinbase_market_data import CoinbaseCompletedBar, CoinbaseHybridGapRecovery

    class Rest:
        def fetch_range(self, start, end):
            return tuple(
                CoinbaseCompletedBar(ts, 1, 1, 1, 1, 1)
                for ts in pd.date_range(start=start, end=pd.Timestamp(end) - pd.Timedelta(minutes=1), freq="1min")
            )

    recovery = CoinbaseHybridGapRecovery(
        rest_client=Rest(), max_backfill_minutes=300, max_startup_catchup_minutes=1000
    )
    with pytest.raises(RuntimeError, match="REST backfill gap of 896 minutes"):
        recovery.recover("2026-08-09T00:00:00Z", "2026-08-09T14:57:00Z")
    bars = recovery.recover_startup("2026-08-09T00:00:00Z", "2026-08-09T14:57:00Z")
    assert len(bars) == 896


def test_startup_catchup_remains_bounded():
    from src.coinbase_market_data import CoinbaseHybridGapRecovery
    recovery = CoinbaseHybridGapRecovery(max_startup_catchup_minutes=600)
    with pytest.raises(RuntimeError, match="Startup catch-up gap of 601 minutes"):
        recovery.recover_startup("2026-08-09T00:00:00Z", "2026-08-09T10:02:00Z")
