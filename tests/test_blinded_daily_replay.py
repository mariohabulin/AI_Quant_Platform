import os
import sys

import pandas as pd
import pytest

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src")))

from blinded_daily_replay import (
    BlindedDailyReplaySession,
    find_missing_daily_timestamps,
    split_continuous_daily_segments,
)


def market_frame(rows=36, start="2024-01-01T00:00:00Z"):
    index = pd.date_range(start, periods=rows, freq="D", tz="UTC")
    close = pd.Series([100.0 + value for value in range(rows)], index=index)
    return pd.DataFrame(
        {
            "Open": close - 0.5,
            "High": close + 1.0,
            "Low": close - 1.0,
            "Close": close,
            "Volume": 1000.0 + pd.Series(range(rows), index=index),
        },
        index=index,
    )


def test_replay_starts_with_exact_trailing_context_and_no_future_metadata():
    frame = market_frame()
    session = BlindedDailyReplaySession("BTC-USD", frame, context_bars=30)

    view = session.current_view()

    assert view.asset == "BTC-USD"
    assert view.sequence == 0
    assert view.timestamp == frame.index[29]
    assert view.position_state == "FLAT"
    pd.testing.assert_frame_equal(view.bars, frame.iloc[:30], check_freq=False)
    assert not hasattr(view, "remaining_bars")
    assert not hasattr(view, "future_end")
    assert frame.index[30] not in view.bars.index


def test_view_is_copy_and_cannot_mutate_private_replay_state():
    session = BlindedDailyReplaySession("ETH-USD", market_frame())
    first = session.current_view()
    first.bars.iloc[-1, first.bars.columns.get_loc("Close")] = -999.0

    second = session.current_view()

    assert second.bars.iloc[-1]["Close"] == 129.0


def test_decision_is_required_before_next_bar_is_revealed():
    session = BlindedDailyReplaySession("BTC-USD", market_frame())

    with pytest.raises(RuntimeError, match="record a decision"):
        session.advance()

    decision = session.record_decision("SKIP", "No confirmed reversal.")
    next_view = session.advance()

    assert decision.position_before == "FLAT"
    assert decision.position_after == "FLAT"
    assert decision.reason == "No confirmed reversal."
    assert next_view.timestamp == pd.Timestamp("2024-01-31T00:00:00Z")
    assert len(next_view.bars) == 30
    assert next_view.bars.index[0] == pd.Timestamp("2024-01-02T00:00:00Z")


def test_position_state_limits_actions_and_records_transitions():
    session = BlindedDailyReplaySession("XRP-USD", market_frame())

    with pytest.raises(ValueError, match="FLAT"):
        session.record_decision("EXIT", "Invalid exit.")

    entered = session.record_decision("ENTER", "Stabilization confirmed.")
    assert entered.position_after == "LONG"
    session.advance()

    with pytest.raises(ValueError, match="LONG"):
        session.record_decision("SKIP", "Invalid skip.")

    held = session.record_decision("HOLD", "No exit condition.")
    assert held.position_before == held.position_after == "LONG"
    session.advance()
    exited = session.record_decision("EXIT", "Bearish distribution volume.")
    assert exited.position_before == "LONG"
    assert exited.position_after == "FLAT"


@pytest.mark.parametrize("action", ["", "BUY", "enter", None])
def test_unknown_or_noncanonical_action_is_rejected(action):
    session = BlindedDailyReplaySession("BTC-USD", market_frame())
    with pytest.raises((TypeError, ValueError), match="action"):
        session.record_decision(action, "Reason")


@pytest.mark.parametrize("reason", ["", "   ", None])
def test_decision_requires_precommitted_reason(reason):
    session = BlindedDailyReplaySession("BTC-USD", market_frame())
    with pytest.raises((TypeError, ValueError), match="reason"):
        session.record_decision("SKIP", reason)


def test_current_timestamp_accepts_only_one_decision():
    session = BlindedDailyReplaySession("BTC-USD", market_frame())
    session.record_decision("SKIP", "No setup.")

    with pytest.raises(RuntimeError, match="already recorded"):
        session.record_decision("ENTER", "Hindsight mutation.")


def test_visible_frame_hash_is_bound_to_each_decision():
    session = BlindedDailyReplaySession("BTC-USD", market_frame())
    first = session.record_decision("SKIP", "No setup.")
    session.advance()
    second = session.record_decision("SKIP", "Still no setup.")

    assert len(first.visible_bars_sha256) == 64
    assert first.visible_bars_sha256 != second.visible_bars_sha256
    assert session.decisions[0] == first
    assert session.decisions[1] == second


def test_completion_requires_final_decision_and_summary_has_no_performance():
    frame = market_frame(rows=32)
    session = BlindedDailyReplaySession("ETH-USD", frame, context_bars=30)

    session.record_decision("SKIP", "No setup.")
    session.advance()
    session.record_decision("SKIP", "No setup.")
    session.advance()
    session.record_decision("SKIP", "No setup.")
    assert session.advance() is None

    summary = session.summary()
    serialized = str(summary).lower()
    assert summary["status"] == "BLINDED_DAILY_REPLAY_COMPLETED"
    assert summary["decision_count"] == 3
    assert summary["performance_evaluation_executed"] is False
    assert summary["strategy_selection_executed"] is False
    assert "return" not in serialized
    assert "profit" not in serialized
    with pytest.raises(RuntimeError, match="complete"):
        session.current_view()


@pytest.mark.parametrize(
    "mutator, error",
    [
        (lambda frame: frame.drop(columns=["Volume"]), "OHLCV"),
        (lambda frame: frame.tz_localize(None), "timezone-aware"),
        (lambda frame: frame.iloc[::-1], "monotonic"),
        (lambda frame: pd.concat([frame, frame.iloc[[-1]]]), "duplicates"),
        (lambda frame: frame.drop(frame.index[10]), "continuous daily"),
        (lambda frame: frame.set_axis(frame.index + pd.Timedelta(hours=1)), "midnight"),
    ],
)
def test_replay_rejects_invalid_or_noncausal_daily_grid(mutator, error):
    with pytest.raises(ValueError, match=error):
        BlindedDailyReplaySession("BTC-USD", mutator(market_frame()))


def test_replay_rejects_invalid_geometry_nonfinite_volume_and_short_history():
    invalid_geometry = market_frame()
    invalid_geometry.loc[invalid_geometry.index[0], "High"] = 1.0
    with pytest.raises(ValueError, match="price geometry"):
        BlindedDailyReplaySession("BTC-USD", invalid_geometry)

    invalid_volume = market_frame()
    invalid_volume.loc[invalid_volume.index[0], "Volume"] = float("nan")
    with pytest.raises(ValueError, match="finite"):
        BlindedDailyReplaySession("BTC-USD", invalid_volume)

    with pytest.raises(ValueError, match="more rows than context_bars"):
        BlindedDailyReplaySession("BTC-USD", market_frame(rows=30))


def test_missing_intervals_are_reported_and_split_without_synthetic_fill():
    original = market_frame(rows=36)
    sparse = original.drop([original.index[10], original.index[11], original.index[25]])

    missing = find_missing_daily_timestamps(sparse)
    segments = split_continuous_daily_segments(sparse)

    assert missing == (
        pd.Timestamp("2024-01-11T00:00:00Z"),
        pd.Timestamp("2024-01-12T00:00:00Z"),
        pd.Timestamp("2024-01-26T00:00:00Z"),
    )
    assert [len(segment) for segment in segments] == [10, 13, 10]
    assert sum(len(segment) for segment in segments) == len(sparse)
