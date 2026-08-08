import pandas as pd
import pytest

from src.market_data_feed import HistoricalReplayFeed, MarketDataEvent
from src.paper_broker import PaperBroker
from src.paper_trading import PaperTradingEngine, PaperTradingSession
from src.risk_engine import RiskEngine


class HoldStrategy:
    def run(self, data):
        result = data.copy()
        result["Signal"] = 0
        return result


def bars():
    return pd.DataFrame(
        {
            "Open": [100, 101, 102],
            "High": [101, 102, 103],
            "Low": [99, 100, 101],
            "Close": [100.5, 101.5, 102.5],
            "Volume": [1000, 1100, 1200],
        },
        index=pd.to_datetime(["2026-08-08 10:00", "2026-08-08 11:00", "2026-08-08 12:00"]),
    )


def test_replay_requires_dataframe():
    with pytest.raises(TypeError, match="DataFrame"):
        HistoricalReplayFeed([])


def test_replay_rejects_empty_data():
    with pytest.raises(ValueError, match="cannot be empty"):
        HistoricalReplayFeed(pd.DataFrame())


def test_replay_requires_complete_ohlcv_contract():
    with pytest.raises(ValueError, match="required OHLCV"):
        HistoricalReplayFeed(bars().drop(columns=["Volume"]))


def test_replay_rejects_duplicate_timestamps():
    data = bars()
    data.index = [data.index[0], data.index[0], data.index[2]]
    with pytest.raises(ValueError, match="unique"):
        HistoricalReplayFeed(data)


def test_replay_rejects_out_of_order_timestamps():
    data = bars().iloc[[1, 0, 2]]
    with pytest.raises(ValueError, match="strictly increasing"):
        HistoricalReplayFeed(data)


def test_replay_rejects_invalid_price_geometry():
    data = bars()
    data.loc[data.index[0], "High"] = 98
    with pytest.raises(ValueError, match="High"):
        HistoricalReplayFeed(data)


def test_replay_rejects_negative_volume():
    data = bars()
    data.loc[data.index[0], "Volume"] = -1
    with pytest.raises(ValueError, match="Volume"):
        HistoricalReplayFeed(data)


def test_replay_emits_normalized_events_in_order():
    events = tuple(HistoricalReplayFeed(bars()))
    assert all(isinstance(event, MarketDataEvent) for event in events)
    assert [event.sequence for event in events] == [1, 2, 3]
    assert [event.timestamp for event in events] == list(bars().index)


def test_replay_event_contains_only_data_available_so_far():
    events = tuple(HistoricalReplayFeed(bars()))
    assert [len(event.data) for event in events] == [1, 2, 3]
    assert events[0].data["Close"].tolist() == [100.5]
    assert events[1].data["Close"].tolist() == [100.5, 101.5]


def test_replay_event_bar_is_latest_normalized_bar():
    event = tuple(HistoricalReplayFeed(bars()))[1]
    assert event.bar["Close"] == pytest.approx(101.5)
    assert event.bar["Volume"] == pytest.approx(1100)


def test_replay_is_repeatable_and_consumer_mutation_cannot_corrupt_feed():
    feed = HistoricalReplayFeed(bars())
    first = tuple(feed)
    first[0].data.loc[first[0].timestamp, "Close"] = 999
    second = tuple(feed)
    assert second[0].data.loc[second[0].timestamp, "Close"] == pytest.approx(100.5)


def test_replay_events_drive_paper_session_without_future_leakage():
    feed = HistoricalReplayFeed(bars())
    engine = PaperTradingEngine(HoldStrategy(), RiskEngine(), PaperBroker(initial_cash=10000))
    session = PaperTradingSession(engine)
    snapshots = tuple(session.process(event.data, timestamp=event.timestamp) for event in feed)
    assert len(snapshots) == 3
    assert [snapshot.market_price for snapshot in snapshots] == pytest.approx([100.5, 101.5, 102.5])
    assert [snapshot.sequence for snapshot in snapshots] == [1, 2, 3]
    assert all(snapshot.equity == pytest.approx(10000.0) for snapshot in snapshots)
