import pandas as pd
import pytest

from src.market_data_feed import MarketDataEvent
from src.realtime_market_data import (
    AlpacaCryptoBarAdapter,
    FeedHealthError,
    RealTimeMarketDataFeed,
)


def bar(ts="2026-08-08T10:00:00Z", symbol="BTC/USD", **overrides):
    message = {
        "T": "b", "S": symbol, "t": ts,
        "o": 60000, "h": 60100, "l": 59900, "c": 60050, "v": 12.5,
    }
    message.update(overrides)
    return message


def feed(**kwargs):
    return RealTimeMarketDataFeed(AlpacaCryptoBarAdapter("BTC/USD"), **kwargs)


def test_alpaca_adapter_requires_dict_message():
    with pytest.raises(TypeError, match="dict"):
        AlpacaCryptoBarAdapter().normalize([])


def test_alpaca_adapter_rejects_non_bar_event():
    with pytest.raises(ValueError, match="bar event"):
        AlpacaCryptoBarAdapter().normalize({"T": "t", "S": "BTC/USD"})


def test_alpaca_adapter_rejects_wrong_symbol():
    with pytest.raises(ValueError, match="BTC/USD"):
        AlpacaCryptoBarAdapter().normalize(bar(symbol="ETH/USD"))


def test_alpaca_adapter_rejects_missing_provider_fields():
    message = bar()
    del message["v"]
    with pytest.raises(ValueError, match="required fields"):
        AlpacaCryptoBarAdapter().normalize(message)


def test_alpaca_adapter_rejects_invalid_price_geometry():
    with pytest.raises(ValueError, match="High"):
        AlpacaCryptoBarAdapter().normalize(bar(h=59000))


def test_feed_emits_existing_market_data_event_contract():
    event = feed().ingest(bar(), received_at="2026-08-08T10:00:30Z")
    assert isinstance(event, MarketDataEvent)
    assert event.sequence == 1
    assert event.timestamp == pd.Timestamp("2026-08-08T10:00:00Z")
    assert event.bar["Close"] == pytest.approx(60050)


def test_feed_accumulates_only_accepted_history():
    f = feed()
    first = f.ingest(bar(), received_at="2026-08-08T10:00:20Z")
    second = f.ingest(bar("2026-08-08T10:01:00Z", c=60100), received_at="2026-08-08T10:01:20Z")
    assert len(first.data) == 1
    assert len(second.data) == 2
    assert second.data["Close"].tolist() == pytest.approx([60050, 60100])


def test_feed_rejects_duplicate_bar_and_marks_unhealthy():
    f = feed()
    f.ingest(bar(), received_at="2026-08-08T10:00:20Z")
    with pytest.raises(FeedHealthError, match="Duplicate"):
        f.ingest(bar(), received_at="2026-08-08T10:00:30Z")
    assert f.health.status == "UNHEALTHY"
    assert f.health.accepted_events == 1


def test_feed_rejects_out_of_order_bar():
    f = feed()
    f.ingest(bar("2026-08-08T10:01:00Z"), received_at="2026-08-08T10:01:20Z")
    with pytest.raises(FeedHealthError, match="Out-of-order"):
        f.ingest(bar("2026-08-08T10:00:00Z"), received_at="2026-08-08T10:01:30Z")


def test_feed_rejects_stale_bar():
    f = feed(stale_after="90s")
    with pytest.raises(FeedHealthError, match="stale"):
        f.ingest(bar(), received_at="2026-08-08T10:02:00Z")


def test_feed_rejects_future_timestamp():
    f = feed()
    with pytest.raises(FeedHealthError, match="future"):
        f.ingest(bar("2026-08-08T10:01:00Z"), received_at="2026-08-08T10:00:59Z")


def test_feed_rejects_missing_bar_gap():
    f = feed(max_gap="2min")
    f.ingest(bar(), received_at="2026-08-08T10:00:20Z")
    with pytest.raises(FeedHealthError, match="Missing-bar"):
        f.ingest(bar("2026-08-08T10:03:00Z"), received_at="2026-08-08T10:03:20Z")


def test_feed_health_becomes_healthy_after_accepted_event():
    f = feed()
    assert f.health.status == "WAITING"
    f.ingest(bar(), received_at="2026-08-08T10:00:20Z")
    assert f.health.status == "HEALTHY"
    assert f.health.accepted_events == 1
    assert f.health.reason == "Feed healthy."


def test_consumer_mutation_cannot_corrupt_realtime_history():
    f = feed()
    event = f.ingest(bar(), received_at="2026-08-08T10:00:20Z")
    event.data.loc[event.timestamp, "Close"] = 1
    assert f.history.loc[event.timestamp, "Close"] == pytest.approx(60050)


def test_restart_reconcile_rebases_large_forward_gap_without_emitting_bar():
    f = feed(max_gap="2min")
    f.ingest(bar("2026-08-08T10:00:00Z"), received_at="2026-08-08T10:00:20Z")

    assert f.reconcile_after_restart(
        bar("2026-08-08T10:30:00Z"), received_at="2026-08-08T10:30:20Z"
    ) is True
    assert f.health.status == "HEALTHY"
    assert f.health.accepted_events == 1
    assert len(f.history) == 1

    event = f.ingest(bar("2026-08-08T10:31:00Z"), received_at="2026-08-08T10:31:20Z")
    assert event.sequence == 2
    assert event.timestamp == pd.Timestamp("2026-08-08T10:31:00Z")


def test_restart_reconcile_does_not_weaken_stale_bar_guard():
    f = feed(max_gap="2min", stale_after="2min")
    f.ingest(bar("2026-08-08T10:00:00Z"), received_at="2026-08-08T10:00:20Z")
    with pytest.raises(FeedHealthError, match="stale"):
        f.reconcile_after_restart(
            bar("2026-08-08T10:30:00Z"), received_at="2026-08-08T10:40:00Z"
        )
