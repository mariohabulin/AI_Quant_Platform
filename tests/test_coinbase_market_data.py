import json

import pandas as pd
import pytest

from src.coinbase_market_data import (
    COINBASE_WS_URL,
    CoinbaseOneMinuteBarAdapter,
    CoinbaseOneMinuteTradeAggregator,
    CoinbasePublicWebSocketTransport,
)
from src.realtime_market_data import RealTimeMarketDataFeed


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
    bars = agg.ingest_message(second)
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
