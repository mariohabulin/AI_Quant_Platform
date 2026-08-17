import json

import pandas as pd
import pytest

import src.forward_paper_session as forward_paper_session_module
from src.coinbase_market_data import CoinbaseTradeOrderingError
from src.forward_paper_session import JsonlForwardAudit, run_forward_paper


def trade_message(ts, price="100", size="1"):
    return {
        "channel": "market_trades",
        "events": [{"trades": [{"product_id": "BTC-USD", "price": price, "size": size, "time": ts}]}],
    }


def provider_update_message(sequence_num, message_timestamp, *trades):
    return {
        "channel": "market_trades",
        "sequence_num": sequence_num,
        "timestamp": message_timestamp,
        "events": [{"type": "update", "trades": list(trades)}],
    }


def provider_trade(trade_id, timestamp, price="100", size="1"):
    if isinstance(timestamp, pd.Timestamp):
        timestamp = timestamp.isoformat()
    return {
        "trade_id": str(trade_id),
        "product_id": "BTC-USD",
        "price": price,
        "size": size,
        "time": timestamp,
    }


class FakeGapRecovery:
    def __init__(self, fail=False):
        self.calls = []
        self.fail = fail

    def recover(self, last_accepted, next_live):
        from src.coinbase_market_data import CoinbaseCompletedBar
        self.calls.append((pd.Timestamp(last_accepted), pd.Timestamp(next_live)))
        if self.fail:
            raise RuntimeError("simulated REST backfill failure")
        start = pd.Timestamp(last_accepted) + pd.Timedelta(minutes=1)
        end = pd.Timestamp(next_live)
        return tuple(
            CoinbaseCompletedBar(ts, 100.0, 100.0, 100.0, 100.0, 1.0)
            for ts in pd.date_range(start=start, end=end - pd.Timedelta(minutes=1), freq="1min")
        )


def test_jsonl_audit_appends_parseable_records(tmp_path):
    path = tmp_path / "audit.jsonl"
    audit = JsonlForwardAudit(
        path, clock=lambda: pd.Timestamp("2026-08-11T10:00:00Z")
    )
    audit.append({"type": "TEST", "at": pd.Timestamp("2026-08-08T18:00:00Z")})
    audit.append({"type": "TEST2", "value": 2})
    rows = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]
    assert [row["type"] for row in rows] == ["TEST", "TEST2"]
    assert rows[0]["at"] == "2026-08-08T18:00:00+00:00"
    assert rows[0]["recorded_at"] == "2026-08-11T10:00:00+00:00"
    assert rows[1]["recorded_at"] == "2026-08-11T10:00:00+00:00"


def test_forward_runner_is_bounded_and_audited(tmp_path):
    messages = [
        trade_message("2026-08-08T18:00:10Z", "100"),
        trade_message("2026-08-08T18:01:10Z", "101"),
        trade_message("2026-08-08T18:02:10Z", "102"),
    ]
    audit_path = tmp_path / "forward.jsonl"
    output = []
    result = run_forward_paper(
        transport=messages,
        max_processed_bars=1,
        audit_path=audit_path,
        output=output.append,
        now_fn=lambda: pd.Timestamp("2026-08-08T18:01:20Z"),
        state_path=tmp_path / "state.json",
    )
    assert result.processed_events == 1
    assert result.paper_orders == 0
    assert result.final_equity == pytest.approx(5000)
    rows = [json.loads(line) for line in audit_path.read_text(encoding="utf-8").splitlines()]
    assert [row["type"] for row in rows] == ["SESSION_START", "PAPER_EVENT", "SESSION_END"]
    assert rows[-1]["real_orders"] == 0
    assert "REAL orders=IMPOSSIBLE" in output[0]


def test_forward_runner_rejects_invalid_bound(tmp_path):
    with pytest.raises(ValueError, match="positive integer"):
        run_forward_paper(transport=[], max_processed_bars=0, audit_path=tmp_path / "x.jsonl")


def test_controlled_operator_stop_closes_audit_and_preserves_continuity(tmp_path):
    def interrupted_transport():
        yield trade_message("2026-08-08T18:00:10Z", "100")
        yield trade_message("2026-08-08T18:01:10Z", "101")
        raise KeyboardInterrupt()

    audit = tmp_path / "operator_stop.jsonl"
    state = tmp_path / "state.json"

    with pytest.raises(KeyboardInterrupt):
        run_forward_paper(
            transport=interrupted_transport(),
            max_processed_bars=10,
            audit_path=audit,
            output=lambda _: None,
            now_fn=lambda: pd.Timestamp("2026-08-08T18:01:20Z"),
            state_path=state,
            resume=False,
        )

    rows = [json.loads(line) for line in audit.read_text(encoding="utf-8").splitlines()]
    assert [row["type"] for row in rows] == [
        "SESSION_START", "PAPER_EVENT", "SESSION_END"
    ]
    assert rows[-1]["reason"] == "OPERATOR_STOP"
    assert rows[-1]["processed_events"] == 1
    assert rows[-1]["rejected_events"] == 0
    assert rows[-1]["real_orders"] == 0
    assert state.exists()


def test_interrupt_before_new_session_does_not_relabel_previous_open_attempt(
    monkeypatch, tmp_path
):
    audit = tmp_path / "previous_open.jsonl"
    audit.write_text(
        json.dumps({"type": "SESSION_START", "at": "2026-08-08T17:00:00Z"})
        + "\n",
        encoding="utf-8",
    )

    def interrupt_before_start(**kwargs):
        raise KeyboardInterrupt()

    monkeypatch.setattr(
        forward_paper_session_module,
        "_run_forward_paper_once",
        interrupt_before_start,
    )
    with pytest.raises(KeyboardInterrupt):
        forward_paper_session_module.run_forward_paper(
            audit_path=audit,
            state_path=tmp_path / "state.json",
        )

    rows = [json.loads(line) for line in audit.read_text(encoding="utf-8").splitlines()]
    assert rows == [{"type": "SESSION_START", "at": "2026-08-08T17:00:00Z"}]


def test_late_trade_failure_records_diagnostics_and_terminal_boundary(tmp_path):
    messages = [
        trade_message("2026-08-08T18:00:10Z", "100"),
        trade_message("2026-08-08T18:01:10Z", "101"),
        trade_message("2026-08-08T18:01:13Z", "102"),
        trade_message("2026-08-08T18:00:59Z", "99"),
    ]
    audit = tmp_path / "ordering_fatal.jsonl"
    state = tmp_path / "state.json"

    with pytest.raises(CoinbaseTradeOrderingError):
        run_forward_paper(
            transport=messages,
            max_processed_bars=10,
            audit_path=audit,
            output=lambda _: None,
            now_fn=lambda: pd.Timestamp("2026-08-08T18:01:20Z"),
            state_path=state,
            resume=False,
        )

    rows = [json.loads(line) for line in audit.read_text(encoding="utf-8").splitlines()]
    assert [row["type"] for row in rows] == [
        "SESSION_START", "PAPER_EVENT", "LATE_TRADE_REJECTED", "SESSION_END"
    ]
    diagnostic = rows[-2]
    assert diagnostic["trade_timestamp"] == "2026-08-08T18:00:59+00:00"
    assert diagnostic["active_bucket"] == "2026-08-08T18:01:00+00:00"
    assert diagnostic["latest_seen_timestamp"] == "2026-08-08T18:01:13+00:00"
    assert diagnostic["watermark_timestamp"] == "2026-08-08T18:01:11+00:00"
    assert diagnostic["reorder_window_seconds"] == pytest.approx(2.0)
    assert diagnostic["lateness_seconds"] == pytest.approx(12.0)
    assert diagnostic["real_orders"] == 0
    assert rows[-1]["reason"] == "ORDERING_FATAL"
    assert rows[-1]["processed_events"] == 1
    assert rows[-1]["real_orders"] == 0
    assert state.exists()


def test_provider_message_replay_is_audited_without_reaching_trading(tmp_path):
    messages = [
        {
            "channel": "_coinbase_transport",
            "event": "PROVIDER_MESSAGE_REPLAY_DROPPED",
            "failure_kind": "PROVIDER_SEQUENCE_REPLAY",
            "provider_channel": "market_trades",
            "previous_sequence_num": 80,
            "observed_sequence_num": 79,
            "message_timestamp": "2026-08-08T18:00:09Z",
            "trade_count": 2,
            "first_trade_id": "7001",
            "last_trade_id": "7002",
        },
        trade_message("2026-08-08T18:00:10Z", "100"),
        trade_message("2026-08-08T18:01:10Z", "101"),
        trade_message("2026-08-08T18:02:10Z", "102"),
    ]
    audit = tmp_path / "provider_message_replay.jsonl"

    result = run_forward_paper(
        transport=messages,
        max_processed_bars=1,
        audit_path=audit,
        output=lambda _: None,
        now_fn=lambda: pd.Timestamp("2026-08-08T18:01:20Z"),
        state_path=tmp_path / "state.json",
        resume=False,
    )

    rows = [json.loads(line) for line in audit.read_text(encoding="utf-8").splitlines()]
    replay = next(
        row for row in rows if row["type"] == "PROVIDER_MESSAGE_REPLAY_DROPPED"
    )
    assert result.processed_events == 1
    assert replay["previous_sequence_num"] == 80
    assert replay["provider_channel"] == "market_trades"
    assert replay["observed_sequence_num"] == 79
    assert replay["trade_count"] == 2
    assert replay["first_trade_id"] == "7001"
    assert replay["last_trade_id"] == "7002"
    assert replay["real_orders"] == 0
    assert rows[-1]["reason"] == "MAX_BARS"


def test_snapshot_boundary_discards_history_and_recovers_partial_minute(tmp_path):
    from src.coinbase_live_paper import build_live_paper_runtime
    from src.coinbase_market_data import CoinbaseOneMinuteTradeAggregator
    from src.forward_paper_session import ForwardContinuityStore

    state = tmp_path / "state.json"
    runtime = build_live_paper_runtime()
    runtime.realtime_feed._last_timestamp = pd.Timestamp(
        "2026-08-16T05:12:00Z"
    )
    runtime.realtime_feed._accepted = 1
    runtime.session.session._last_timestamp = pd.Timestamp(
        "2026-08-16T05:12:00Z"
    )
    runtime._processed = 1
    runtime._last_event_at = pd.Timestamp("2026-08-16T05:12:00Z")
    ForwardContinuityStore(state).save(
        runtime, CoinbaseOneMinuteTradeAggregator()
    )

    messages = [
        {
            "channel": "_coinbase_transport",
            "event": "PROVIDER_SNAPSHOT_BOUNDARY",
            "provider_channel": "market_trades",
            "message_sequence_num": 102964,
            "message_timestamp": "2026-08-16T05:13:56.580642159Z",
            "snapshot_event_count": 1,
            "trade_count": 100,
            "first_trade_id": "newest",
            "last_trade_id": "1070883132",
            "oldest_trade_timestamp": "2026-08-16T05:12:54.738994Z",
            "newest_trade_timestamp": "2026-08-16T05:13:55.651086Z",
        },
        provider_update_message(
            102965,
            "2026-08-16T05:13:56.700000Z",
            provider_trade(
                "1070883132", "2026-08-16T05:12:54.738994Z", "99"
            ),
            provider_trade("101", "2026-08-16T05:13:57Z", "101"),
        ),
        trade_message("2026-08-16T05:14:01Z", "102"),
        trade_message("2026-08-16T05:14:03Z", "103"),
        trade_message("2026-08-16T05:15:01Z", "104"),
        trade_message("2026-08-16T05:15:03Z", "105"),
    ]
    class SnapshotStartupRecovery(FakeGapRecovery):
        def recover_startup(self, last_accepted, next_live):
            bars = super().recover(last_accepted, next_live)
            self.calls[-1] = (*self.calls[-1], "startup")
            return bars

    recovery = SnapshotStartupRecovery()
    audit = tmp_path / "snapshot_boundary.jsonl"

    result = run_forward_paper(
        transport=messages,
        max_processed_bars=1,
        audit_path=audit,
        output=lambda _: None,
        now_fn=lambda: pd.Timestamp("2026-08-16T05:15:10Z"),
        state_path=state,
        gap_recovery=recovery,
    )

    rows = [
        json.loads(line)
        for line in audit.read_text(encoding="utf-8").splitlines()
    ]
    snapshot = next(
        row for row in rows if row["type"] == "PROVIDER_SNAPSHOT_BOUNDARY"
    )
    boundary_drops = [
        row
        for row in rows
        if row["type"] == "PROVIDER_SNAPSHOT_BOUNDARY_BAR_DROPPED"
    ]
    quarantine = [
        row
        for row in rows
        if row["type"] == "PROVIDER_SNAPSHOT_QUARANTINE_TRADES_DROPPED"
    ]
    catchup = [row for row in rows if row["type"] == "STARTUP_CATCHUP_BAR"]
    paper = [row for row in rows if row["type"] == "PAPER_EVENT"]

    assert snapshot["message_sequence_num"] == 102964
    assert snapshot["trade_count"] == 100
    assert snapshot["oldest_trade_timestamp"] == (
        "2026-08-16T05:12:54.738994Z"
    )
    assert snapshot["real_orders"] == 0
    assert [row["timestamp"] for row in boundary_drops] == [
        "2026-08-16T05:13:00+00:00"
    ]
    assert boundary_drops[0]["trusted_live_bucket"] == (
        "2026-08-16T05:14:00+00:00"
    )
    assert len(quarantine) == 1
    assert quarantine[0]["trade_count"] == 2
    assert quarantine[0]["first_trade_id"] == "1070883132"
    assert quarantine[0]["last_trade_id"] == "101"
    assert quarantine[0]["message_sequence_num"] == 102965
    assert quarantine[0]["trusted_live_bucket"] == (
        "2026-08-16T05:14:00+00:00"
    )
    assert quarantine[0]["real_orders"] == 0
    assert recovery.calls == [(
        pd.Timestamp("2026-08-16T05:12:00Z"),
        pd.Timestamp("2026-08-16T05:14:00Z"),
        "startup",
    )]
    assert [row["timestamp"] for row in catchup] == [
        "2026-08-16T05:13:00+00:00"
    ]
    assert catchup[0]["boundary_kind"] == "RESTART"
    assert paper[0]["snapshot"]["timestamp"] == (
        "2026-08-16T05:14:00+00:00"
    )
    assert not any(row["type"] == "LATE_TRADE_REJECTED" for row in rows)
    assert result.processed_events == 1
    assert result.rejected_events == 0


@pytest.mark.parametrize(
    (
        "snapshot_sequence",
        "update_sequence",
        "message_timestamp",
        "late_trade_timestamp",
        "late_trade_id",
        "trusted_live_bucket",
    ),
    [
        (
            10784,
            10786,
            "2026-08-16T21:34:51.524555043Z",
            "2026-08-16T21:33:09.501792Z",
            "1071015409",
            "2026-08-16T21:35:00Z",
        ),
        (
            7423,
            7425,
            "2026-08-16T22:03:14.943949939Z",
            "2026-08-16T22:02:55.664795Z",
            "1071026960",
            "2026-08-16T22:04:00Z",
        ),
    ],
)
def test_cloud_post_snapshot_history_is_quarantined_without_ordering_fatal(
    tmp_path,
    snapshot_sequence,
    update_sequence,
    message_timestamp,
    late_trade_timestamp,
    late_trade_id,
    trusted_live_bucket,
):
    trusted = pd.Timestamp(trusted_live_bucket)
    messages = [
        {
            "channel": "_coinbase_transport",
            "event": "PROVIDER_SNAPSHOT_BOUNDARY",
            "provider_channel": "market_trades",
            "message_sequence_num": snapshot_sequence,
            "message_timestamp": message_timestamp,
            "snapshot_event_count": 1,
            "trade_count": 100,
            "first_trade_id": "snapshot-newest",
            "last_trade_id": late_trade_id,
            "oldest_trade_timestamp": late_trade_timestamp,
            "newest_trade_timestamp": message_timestamp,
        },
        provider_update_message(
            update_sequence,
            message_timestamp,
            provider_trade(late_trade_id, late_trade_timestamp, "99"),
        ),
        provider_update_message(
            update_sequence + 1,
            (trusted + pd.Timedelta(seconds=1)).isoformat(),
            provider_trade("trusted-1", trusted + pd.Timedelta(seconds=1)),
        ),
        provider_update_message(
            update_sequence + 2,
            (trusted + pd.Timedelta(seconds=4)).isoformat(),
            provider_trade("trusted-2", trusted + pd.Timedelta(seconds=4)),
        ),
        provider_update_message(
            update_sequence + 3,
            (trusted + pd.Timedelta(minutes=1, seconds=1)).isoformat(),
            provider_trade(
                "next-1", trusted + pd.Timedelta(minutes=1, seconds=1)
            ),
        ),
        provider_update_message(
            update_sequence + 4,
            (trusted + pd.Timedelta(minutes=1, seconds=4)).isoformat(),
            provider_trade(
                "next-2", trusted + pd.Timedelta(minutes=1, seconds=4)
            ),
        ),
        # The quarantine floor remains active after PAPER processing resumes.
        provider_update_message(
            update_sequence + 5,
            (trusted + pd.Timedelta(minutes=1, seconds=5)).isoformat(),
            provider_trade(
                f"{late_trade_id}-replay", late_trade_timestamp, "98"
            ),
        ),
        provider_update_message(
            update_sequence + 6,
            (trusted + pd.Timedelta(minutes=2, seconds=1)).isoformat(),
            provider_trade(
                "later-1", trusted + pd.Timedelta(minutes=2, seconds=1)
            ),
        ),
        provider_update_message(
            update_sequence + 7,
            (trusted + pd.Timedelta(minutes=2, seconds=4)).isoformat(),
            provider_trade(
                "later-2", trusted + pd.Timedelta(minutes=2, seconds=4)
            ),
        ),
    ]
    audit = tmp_path / f"post_snapshot_{snapshot_sequence}.jsonl"

    result = run_forward_paper(
        transport=messages,
        max_processed_bars=2,
        audit_path=audit,
        output=lambda _: None,
        now_fn=lambda: trusted + pd.Timedelta(minutes=2, seconds=10),
        state_path=tmp_path / f"post_snapshot_{snapshot_sequence}.json",
        resume=False,
    )

    rows = [
        json.loads(line)
        for line in audit.read_text(encoding="utf-8").splitlines()
    ]
    quarantines = [
        row
        for row in rows
        if row["type"] == "PROVIDER_SNAPSHOT_QUARANTINE_TRADES_DROPPED"
    ]
    paper = [row for row in rows if row["type"] == "PAPER_EVENT"]

    assert result.processed_events == 2
    assert sum(row["trade_count"] for row in quarantines) == 2
    assert quarantines[0]["snapshot_message_sequence_num"] == (
        snapshot_sequence
    )
    assert quarantines[0]["message_sequence_num"] == update_sequence
    assert quarantines[0]["first_trade_id"] == late_trade_id
    assert quarantines[0]["trusted_live_bucket"] == trusted.isoformat()
    assert all(row["real_orders"] == 0 for row in quarantines)
    assert [row["snapshot"]["timestamp"] for row in paper] == [
        trusted.isoformat(),
        (trusted + pd.Timedelta(minutes=1)).isoformat(),
    ]
    assert not any(row["type"] == "LATE_TRADE_REJECTED" for row in rows)
    assert rows[-1]["type"] == "SESSION_END"
    assert rows[-1]["reason"] == "MAX_BARS"
    assert rows[-1]["real_orders"] == 0


def test_snapshot_quarantine_does_not_mutate_or_hide_invalid_trade_time():
    message = provider_update_message(
        9002,
        "2026-08-16T20:00:10Z",
        provider_trade("history", "2026-08-16T19:59:59Z"),
        provider_trade("trusted", "2026-08-16T20:00:01Z"),
        provider_trade("invalid", "not-a-timestamp"),
    )

    filtered, summary = (
        forward_paper_session_module
        ._quarantine_pre_snapshot_boundary_trades(
            message, pd.Timestamp("2026-08-16T20:00:00Z")
        )
    )

    assert [
        trade["trade_id"] for trade in message["events"][0]["trades"]
    ] == ["history", "trusted", "invalid"]
    assert [
        trade["trade_id"] for trade in filtered["events"][0]["trades"]
    ] == ["trusted", "invalid"]
    assert summary["trade_count"] == 1
    assert summary["first_trade_id"] == "history"


def test_true_post_boundary_late_trade_remains_fatal(tmp_path):
    trusted = pd.Timestamp("2026-08-16T18:01:00Z")
    messages = [
        {
            "channel": "_coinbase_transport",
            "event": "PROVIDER_SNAPSHOT_BOUNDARY",
            "provider_channel": "market_trades",
            "message_sequence_num": 7000,
            "message_timestamp": "2026-08-16T18:00:45Z",
            "snapshot_event_count": 1,
            "trade_count": 100,
            "oldest_trade_timestamp": "2026-08-16T17:59:01Z",
            "newest_trade_timestamp": "2026-08-16T18:00:44Z",
        },
        provider_update_message(
            7001,
            "2026-08-16T18:00:46Z",
            provider_trade("snapshot-history", "2026-08-16T17:59:59Z"),
        ),
        provider_update_message(
            7002,
            "2026-08-16T18:01:01Z",
            provider_trade("trusted-1", "2026-08-16T18:01:01Z"),
        ),
        provider_update_message(
            7003,
            "2026-08-16T18:01:04Z",
            provider_trade("trusted-2", "2026-08-16T18:01:04Z"),
        ),
        provider_update_message(
            7004,
            "2026-08-16T18:02:01Z",
            provider_trade("next-1", "2026-08-16T18:02:01Z"),
        ),
        provider_update_message(
            7005,
            "2026-08-16T18:02:04Z",
            provider_trade("next-2", "2026-08-16T18:02:04Z"),
        ),
        provider_update_message(
            7006,
            "2026-08-16T18:02:05Z",
            provider_trade("true-late", "2026-08-16T18:01:30Z"),
        ),
    ]
    audit = tmp_path / "post_boundary_ordering_fatal.jsonl"

    with pytest.raises(CoinbaseTradeOrderingError):
        run_forward_paper(
            transport=messages,
            max_processed_bars=10,
            audit_path=audit,
            output=lambda _: None,
            now_fn=lambda: trusted + pd.Timedelta(minutes=1, seconds=10),
            state_path=tmp_path / "post_boundary_ordering_fatal.json",
            resume=False,
        )

    rows = [
        json.loads(line)
        for line in audit.read_text(encoding="utf-8").splitlines()
    ]
    quarantine = [
        row
        for row in rows
        if row["type"] == "PROVIDER_SNAPSHOT_QUARANTINE_TRADES_DROPPED"
    ]
    fatal = next(row for row in rows if row["type"] == "LATE_TRADE_REJECTED")

    assert sum(row["trade_count"] for row in quarantine) == 1
    assert fatal["trade_id"] == "true-late"
    assert fatal["trade_timestamp"] == "2026-08-16T18:01:30+00:00"
    assert fatal["active_bucket"] == "2026-08-16T18:02:00+00:00"
    assert rows[-1]["reason"] == "ORDERING_FATAL"
    assert rows[-1]["real_orders"] == 0


def test_continuity_store_round_trip_preserves_position_history_and_bucket(tmp_path):
    from src.coinbase_live_paper import build_live_paper_runtime
    from src.coinbase_market_data import CoinbaseOneMinuteTradeAggregator
    from src.forward_paper_session import ForwardContinuityStore

    runtime = build_live_paper_runtime()
    broker = runtime.session.engine.paper_broker
    broker.cash = 3750.0
    broker.position_quantity = 0.02
    broker.average_entry_price = 62500.0
    broker.position_cost_basis = 1250.0
    runtime.session._history = pd.DataFrame(
        [{"Open": 62500.0, "High": 62500.0, "Low": 62500.0, "Close": 62500.0, "Volume": 1.0}],
        index=pd.DatetimeIndex([pd.Timestamp("2026-08-08T19:24:00Z")]),
    )
    aggregator = CoinbaseOneMinuteTradeAggregator()
    aggregator.ingest_trade({"product_id": "BTC-USD", "price": "62501", "size": "0.1", "time": "2026-08-08T19:25:10Z"})

    store = ForwardContinuityStore(
        tmp_path / "state.json",
        clock=lambda: pd.Timestamp("2026-08-11T10:00:00Z"),
    )
    store.save(runtime, aggregator)
    payload = json.loads((tmp_path / "state.json").read_text(encoding="utf-8"))
    assert payload["saved_at"] == "2026-08-11T10:00:00+00:00"
    restored = build_live_paper_runtime()
    restored_agg = CoinbaseOneMinuteTradeAggregator()
    assert store.load_into(restored, restored_agg) is True
    assert restored.session.engine.paper_broker.cash == pytest.approx(3750.0)
    assert restored.session.engine.paper_broker.position_quantity == pytest.approx(0.02)
    assert restored.session._history.iloc[-1]["Close"] == pytest.approx(62500.0)
    assert restored_agg._bucket == pd.Timestamp("2026-08-08T19:25:00Z")


def test_bootstrap_continuity_from_v1_audit_preserves_open_position(tmp_path):
    from src.forward_paper_session import ForwardContinuityStore, bootstrap_continuity_from_audit
    from src.coinbase_live_paper import build_live_paper_runtime
    from src.coinbase_market_data import CoinbaseOneMinuteTradeAggregator

    audit = tmp_path / "audit.jsonl"
    records = [
        {"type":"PAPER_EVENT","paper_orders":0,"snapshot":{"timestamp":"2026-08-08T19:23:00+00:00","market_price":64970.01,"cash":5000.0,"position_quantity":0.0,"average_entry_price":0.0,"realized_pnl":0.0,"equity":5000.0}},
        {"type":"PAPER_EVENT","paper_orders":1,"snapshot":{"timestamp":"2026-08-08T19:24:00+00:00","market_price":64972.84,"cash":3750.0,"position_quantity":0.019238808092735364,"average_entry_price":64972.84,"realized_pnl":0.0,"equity":5000.0}},
        {"type":"PAPER_EVENT","paper_orders":1,"snapshot":{"timestamp":"2026-08-08T19:25:00+00:00","market_price":64972.53,"cash":3750.0,"position_quantity":0.019238808092735364,"average_entry_price":64972.84,"realized_pnl":0.0,"equity":4999.994035969491}},
    ]
    audit.write_text("\n".join(json.dumps(x) for x in records)+"\n", encoding="utf-8")
    state = tmp_path / "state.json"
    account = bootstrap_continuity_from_audit(audit, state)
    assert account["cash"] == pytest.approx(3750.0)
    assert account["position_quantity"] == pytest.approx(0.019238808092735364)

    runtime = build_live_paper_runtime()
    agg = CoinbaseOneMinuteTradeAggregator()
    assert ForwardContinuityStore(state).load_into(runtime, agg)
    assert runtime.session.engine.paper_broker._next_order_number == 2
    assert runtime.session.session._last_timestamp == pd.Timestamp("2026-08-08T19:25:00Z")
    assert len(runtime.session._history) == 3


def test_cli_bootstrap_uses_evidence_audit_by_default(monkeypatch, tmp_path, capsys):
    import src.forward_paper_session as module

    seen = {}

    def fake_bootstrap(audit_path, state_path):
        seen["audit"] = str(audit_path)
        seen["state"] = str(state_path)
        return {"cash": 3750.0, "position_quantity": 0.019238808, "equity": 4999.99}

    monkeypatch.setattr(module, "bootstrap_continuity_from_audit", fake_bootstrap)
    state = tmp_path / "state.json"
    assert module.main(["--bootstrap-from-audit", "--state", str(state)]) == 0
    assert seen["audit"] == module.DEFAULT_BOOTSTRAP_AUDIT
    assert seen["state"] == str(state)
    assert "Continuity bootstrap complete" in capsys.readouterr().out


def test_cli_bootstrap_keeps_legacy_explicit_audit_override(monkeypatch, tmp_path):
    import src.forward_paper_session as module

    seen = {}

    def fake_bootstrap(audit_path, state_path):
        seen["audit"] = str(audit_path)
        return {"cash": 3750.0, "position_quantity": 0.019238808, "equity": 4999.99}

    monkeypatch.setattr(module, "bootstrap_continuity_from_audit", fake_bootstrap)
    audit = tmp_path / "legacy.jsonl"
    state = tmp_path / "state.json"
    assert module.main(["--bootstrap-from-audit", "--audit", str(audit), "--state", str(state)]) == 0
    assert seen["audit"] == str(audit)


def test_resumed_forward_session_rebases_gap_without_trading_boundary_bar(tmp_path):
    from src.coinbase_live_paper import build_live_paper_runtime
    from src.coinbase_market_data import CoinbaseOneMinuteTradeAggregator
    from src.forward_paper_session import ForwardContinuityStore

    state = tmp_path / "state.json"
    runtime = build_live_paper_runtime()
    broker = runtime.session.engine.paper_broker
    broker.cash = 3750.0
    broker.position_quantity = 0.02
    broker.average_entry_price = 62500.0
    broker.position_cost_basis = 1250.0
    runtime.session._history = pd.DataFrame(
        [{"Open": 62500.0, "High": 62500.0, "Low": 62500.0, "Close": 62500.0, "Volume": 1.0}],
        index=pd.DatetimeIndex([pd.Timestamp("2026-08-08T19:25:00Z")]),
    )
    runtime.session.session._last_timestamp = pd.Timestamp("2026-08-08T19:25:00Z")
    runtime.realtime_feed._last_timestamp = pd.Timestamp("2026-08-08T19:25:00Z")
    runtime.realtime_feed._accepted = 1
    runtime._processed = 1
    runtime._last_event_at = pd.Timestamp("2026-08-08T19:25:00Z")
    ForwardContinuityStore(state).save(runtime, CoinbaseOneMinuteTradeAggregator())

    messages = [
        trade_message("2026-08-08T19:52:10Z", "62600"),
        trade_message("2026-08-08T19:53:10Z", "62601"),
        trade_message("2026-08-08T19:54:10Z", "62602"),
        trade_message("2026-08-08T19:55:10Z", "62603"),
    ]
    audit = tmp_path / "resume.jsonl"
    output = []
    clock = iter([
        pd.Timestamp("2026-08-08T19:52:20Z"),
        pd.Timestamp("2026-08-08T19:53:20Z"),
        pd.Timestamp("2026-08-08T19:54:20Z"),
        pd.Timestamp("2026-08-08T19:55:20Z"),
    ])
    recovery = FakeGapRecovery()
    result = run_forward_paper(
        transport=messages,
        max_processed_bars=2,
        audit_path=audit,
        output=output.append,
        now_fn=lambda: next(clock),
        state_path=state,
        gap_recovery=recovery,
    )

    rows = [json.loads(line) for line in audit.read_text(encoding="utf-8").splitlines()]
    backfill = [row for row in rows if row["type"] == "REST_BACKFILL_BAR"]
    completed = [row for row in rows if row["type"] == "REST_BACKFILL_COMPLETE"]
    paper = [row for row in rows if row["type"] == "PAPER_EVENT"]
    assert len(backfill) == 26
    assert len(completed) == 1
    assert len(paper) == 2
    assert result.processed_events == 2
    assert result.rejected_events == 0
    # The synthetic recovery collapses price from 62500 to 100, producing a
    # bearish recovery crossover. The new lifecycle contract preserves the
    # position during backfill, then closes it on the first fresh live bar.
    assert result.final_position == pytest.approx(0.0)
    assert any(row["type"] == "RECOVERY_CROSSOVER_DETECTED" for row in rows)
    assert any(row["type"] == "POST_RECOVERY_RECONCILIATION" for row in rows)
    assert any(line.startswith("REST_BACKFILL 26 bars") for line in output)
    assert paper[0]["snapshot"]["timestamp"] == "2026-08-08T19:52:00+00:00"
    assert paper[0]["event"]["signal"] == -1


def test_forward_session_audits_reconnect_and_rebases_without_trading_boundary_bar(tmp_path):
    state = tmp_path / "state.json"
    audit = tmp_path / "audit.jsonl"
    messages = [
        trade_message("2026-08-09T08:00:10Z", "100"),
        trade_message("2026-08-09T08:01:10Z", "101"),
        trade_message("2026-08-09T08:02:10Z", "102"),
        {
            "channel": "_coinbase_transport",
            "event": "DISCONNECTED",
            "attempt": 1,
            "reason": "provider sequence gap",
            "failure_kind": "PROVIDER_SEQUENCE_GAP",
            "provider_channel": "heartbeats",
            "previous_sequence_num": 100,
            "expected_sequence_num": 101,
            "observed_sequence_num": 102,
            "message_timestamp": "2026-08-09T08:02:11Z",
        },
        {
            "channel": "_coinbase_transport",
            "event": "RECONNECTED",
            "reconnect_count": 1,
            "message_timestamp": "2026-08-09T08:09:20Z",
        },
        trade_message("2026-08-09T08:10:10Z", "110"),
        trade_message("2026-08-09T08:11:10Z", "111"),
        trade_message("2026-08-09T08:12:10Z", "112"),
        trade_message("2026-08-09T08:13:10Z", "113"),
    ]
    times = iter([
        pd.Timestamp("2026-08-09T08:00:00Z"),  # SESSION_START
        pd.Timestamp("2026-08-09T08:01:20Z"),
        pd.Timestamp("2026-08-09T08:02:20Z"),
        pd.Timestamp("2026-08-09T08:11:20Z"),
        pd.Timestamp("2026-08-09T08:12:20Z"),
    ])
    output = []
    recovery = FakeGapRecovery()
    result = run_forward_paper(
        transport=messages,
        max_processed_bars=3,
        audit_path=audit,
        output=output.append,
        now_fn=lambda: next(times),
        state_path=state,
        resume=False,
        gap_recovery=recovery,
    )
    rows = [json.loads(line) for line in audit.read_text(encoding="utf-8").splitlines()]
    transport_events = [row for row in rows if row["type"] == "TRANSPORT_EVENT"]
    backfill = [row for row in rows if row["type"] == "REST_BACKFILL_BAR"]
    paper = [row for row in rows if row["type"] == "PAPER_EVENT"]
    assert [row["event"] for row in transport_events] == ["DISCONNECTED", "RECONNECTED"]
    assert transport_events[0]["failure_kind"] == "PROVIDER_SEQUENCE_GAP"
    assert transport_events[0]["provider_channel"] == "heartbeats"
    assert transport_events[0]["previous_sequence_num"] == 100
    assert transport_events[0]["expected_sequence_num"] == 101
    assert transport_events[0]["observed_sequence_num"] == 102
    assert transport_events[0]["message_timestamp"] == "2026-08-09T08:02:11Z"
    assert len(backfill) == 8
    assert len(paper) == 3
    assert result.processed_events == 3
    assert result.rejected_events == 0
    assert any(line.startswith("TRANSPORT DISCONNECTED") for line in output)
    assert any(line.startswith("REST_BACKFILL 8 bars") for line in output)


def test_forward_session_labels_runtime_health_halt_instead_of_transport_end(tmp_path):
    messages = [
        trade_message("2026-08-09T08:00:10Z", "100"),
        trade_message("2026-08-09T08:01:10Z", "101"),
        trade_message("2026-08-09T08:02:10Z", "102"),
        trade_message("2026-08-09T08:03:10Z", "103"),
    ]
    audit = tmp_path / "halt.jsonl"
    run_forward_paper(
        transport=messages,
        max_processed_bars=10,
        audit_path=audit,
        now_fn=lambda: pd.Timestamp("2026-08-09T10:00:00Z"),
        state_path=tmp_path / "state.json",
        resume=False,
    )
    rows = [json.loads(line) for line in audit.read_text(encoding="utf-8").splitlines()]
    assert rows[-1]["type"] == "SESSION_END"
    assert rows[-1]["reason"] == "RUNTIME_HALTED"
    assert rows[-1]["rejected_events"] == 3


def test_forward_session_closes_audit_on_reconnect_exhaustion(tmp_path):
    messages = [
        trade_message("2026-08-09T08:00:10Z", "100"),
        trade_message("2026-08-09T08:01:10Z", "101"),
        trade_message("2026-08-09T08:02:10Z", "102"),
        {"channel": "_coinbase_transport", "event": "DISCONNECTED", "attempt": 1, "reason": "dns unavailable"},
        {"channel": "_coinbase_transport", "event": "RECONNECT_EXHAUSTED", "attempt": 4, "reason": "dns unavailable"},
    ]
    audit = tmp_path / "fatal.jsonl"
    state = tmp_path / "state.json"
    result = run_forward_paper(
        transport=messages,
        max_processed_bars=10,
        audit_path=audit,
        now_fn=lambda: pd.Timestamp("2026-08-09T08:02:20Z"),
        state_path=state,
        resume=False,
    )
    rows = [json.loads(line) for line in audit.read_text(encoding="utf-8").splitlines()]
    assert rows[-1]["type"] == "SESSION_END"
    assert rows[-1]["reason"] == "TRANSPORT_FATAL"
    assert rows[-1]["real_orders"] == 0
    assert any(row.get("event") == "RECONNECT_EXHAUSTED" for row in rows)
    assert state.exists()
    assert result.audit_path == str(audit)



def test_completed_provider_replay_classifier_uses_accepted_feed_watermark():
    from src.coinbase_live_paper import build_live_paper_runtime
    from src.coinbase_market_data import CoinbaseCompletedBar
    from src.forward_paper_session import _is_completed_provider_replay

    runtime = build_live_paper_runtime()
    runtime.realtime_feed._last_timestamp = pd.Timestamp("2026-08-09T10:25:00Z")

    def bar(ts):
        return CoinbaseCompletedBar(pd.Timestamp(ts), 100.0, 101.0, 99.0, 100.0, 1.0)

    assert _is_completed_provider_replay(runtime, bar("2026-08-09T10:25:00Z"))
    assert _is_completed_provider_replay(runtime, bar("2026-08-09T10:23:00Z"))
    assert _is_completed_provider_replay(runtime, bar("2026-08-09T10:24:00Z"))
    assert not _is_completed_provider_replay(runtime, bar("2026-08-09T10:26:00Z"))


def test_replay_classifier_does_not_mutate_runtime_health():
    from src.coinbase_live_paper import build_live_paper_runtime
    from src.coinbase_market_data import CoinbaseCompletedBar
    from src.forward_paper_session import _is_completed_provider_replay

    runtime = build_live_paper_runtime()
    runtime.realtime_feed._last_timestamp = pd.Timestamp("2026-08-09T10:25:00Z")
    before = runtime.health
    replay = CoinbaseCompletedBar(pd.Timestamp("2026-08-09T10:24:00Z"), 100.0, 101.0, 99.0, 100.0, 1.0)

    assert _is_completed_provider_replay(runtime, replay)
    after = runtime.health
    assert after.rejected_events == before.rejected_events
    assert after.consecutive_failures == before.consecutive_failures



def test_reconnect_boundary_recovers_exactly_one_missing_minute(tmp_path):
    """A 2-minute live timestamp jump means one full 1m bar is missing."""
    from src.coinbase_live_paper import build_live_paper_runtime
    from src.coinbase_market_data import CoinbaseOneMinuteTradeAggregator
    from src.forward_paper_session import ForwardContinuityStore

    state = tmp_path / "state.json"
    runtime = build_live_paper_runtime()
    runtime.realtime_feed._last_timestamp = pd.Timestamp("2026-08-10T11:33:00Z")
    runtime.realtime_feed._accepted = 1
    runtime.session.session._last_timestamp = pd.Timestamp("2026-08-10T11:33:00Z")
    runtime._processed = 1
    runtime._last_event_at = pd.Timestamp("2026-08-10T11:33:00Z")
    ForwardContinuityStore(state).save(runtime, CoinbaseOneMinuteTradeAggregator())

    messages = [
        {"channel": "_coinbase_transport", "event": "DISCONNECTED", "attempt": 1, "reason": "test"},
        {"channel": "_coinbase_transport", "event": "RECONNECTED", "reconnect_count": 1},
        trade_message("2026-08-10T11:35:10Z", "100"),
        trade_message("2026-08-10T11:36:10Z", "101"),
        trade_message("2026-08-10T11:37:10Z", "102"),
    ]
    recovery = FakeGapRecovery()
    audit = tmp_path / "one_minute_gap.jsonl"
    result = run_forward_paper(
        transport=messages,
        max_processed_bars=1,
        audit_path=audit,
        output=lambda _: None,
        now_fn=lambda: pd.Timestamp("2026-08-10T11:36:20Z"),
        state_path=state,
        gap_recovery=recovery,
    )

    rows = [json.loads(line) for line in audit.read_text(encoding="utf-8").splitlines()]
    backfill = [row for row in rows if row["type"] == "REST_BACKFILL_BAR"]
    paper = [row for row in rows if row["type"] == "PAPER_EVENT"]

    assert recovery.calls == [(
        pd.Timestamp("2026-08-10T11:33:00Z"),
        pd.Timestamp("2026-08-10T11:35:00Z"),
    )]
    assert [row["timestamp"] for row in backfill] == ["2026-08-10T11:34:00+00:00"]
    assert paper[0]["snapshot"]["timestamp"] == "2026-08-10T11:35:00+00:00"
    assert result.processed_events == 1
    assert result.rejected_events == 0
    assert result.paper_orders == 0


@pytest.mark.parametrize(
    "reconnect_message_timestamp",
    ["2026-08-10T12:01:20Z", "2026-08-10T12:01:20", None],
)
def test_sequence_gap_discards_partial_reconnect_minute_before_exact_recovery(
    tmp_path, reconnect_message_timestamp,
):
    from src.coinbase_live_paper import build_live_paper_runtime
    from src.coinbase_market_data import CoinbaseOneMinuteTradeAggregator
    from src.forward_paper_session import ForwardContinuityStore

    state = tmp_path / "state.json"
    runtime = build_live_paper_runtime()
    runtime.realtime_feed._last_timestamp = pd.Timestamp(
        "2026-08-10T12:00:00Z"
    )
    runtime.realtime_feed._accepted = 1
    runtime.session.session._last_timestamp = pd.Timestamp(
        "2026-08-10T12:00:00Z"
    )
    runtime._processed = 1
    runtime._last_event_at = pd.Timestamp("2026-08-10T12:00:00Z")
    ForwardContinuityStore(state).save(
        runtime, CoinbaseOneMinuteTradeAggregator()
    )

    messages = [
        {
            "channel": "_coinbase_transport",
            "event": "DISCONNECTED",
            "failure_kind": "PROVIDER_SEQUENCE_GAP",
            "previous_sequence_num": 100,
            "expected_sequence_num": 101,
            "observed_sequence_num": 102,
        },
        {
            "channel": "_coinbase_transport",
            "event": "RECONNECTED",
            "message_timestamp": reconnect_message_timestamp,
        },
        trade_message("2026-08-10T12:01:30Z", "101"),
        trade_message("2026-08-10T12:02:10Z", "102"),
        trade_message("2026-08-10T12:03:10Z", "103"),
    ]
    recovery = FakeGapRecovery()
    audit = tmp_path / "sequence_gap_boundary.jsonl"

    result = run_forward_paper(
        transport=messages,
        max_processed_bars=1,
        audit_path=audit,
        output=lambda _: None,
        now_fn=lambda: pd.Timestamp("2026-08-10T12:03:20Z"),
        state_path=state,
        gap_recovery=recovery,
    )

    rows = [
        json.loads(line)
        for line in audit.read_text(encoding="utf-8").splitlines()
    ]
    boundary_drops = [
        row
        for row in rows
        if row["type"] == "PROVIDER_SEQUENCE_BOUNDARY_BAR_DROPPED"
    ]
    backfill = [row for row in rows if row["type"] == "REST_BACKFILL_BAR"]
    paper = [row for row in rows if row["type"] == "PAPER_EVENT"]

    assert recovery.calls == [(
        pd.Timestamp("2026-08-10T12:00:00Z"),
        pd.Timestamp("2026-08-10T12:02:00Z"),
    )]
    assert [row["timestamp"] for row in boundary_drops] == [
        "2026-08-10T12:01:00+00:00"
    ]
    assert boundary_drops[0]["trusted_live_bucket"] == (
        "2026-08-10T12:02:00+00:00"
    )
    assert [row["timestamp"] for row in backfill] == [
        "2026-08-10T12:01:00+00:00"
    ]
    assert paper[0]["snapshot"]["timestamp"] == "2026-08-10T12:02:00+00:00"
    assert result.processed_events == 1
    assert result.rejected_events == 0


def test_forward_session_fails_closed_when_rest_backfill_is_incomplete(tmp_path):
    audit = tmp_path / "backfill_fatal.jsonl"
    messages = [
        trade_message("2026-08-09T08:00:10Z", "100"),
        trade_message("2026-08-09T08:01:10Z", "101"),
        trade_message("2026-08-09T08:02:10Z", "102"),
        {"channel": "_coinbase_transport", "event": "DISCONNECTED", "attempt": 1, "reason": "reset"},
        {"channel": "_coinbase_transport", "event": "RECONNECTED", "reconnect_count": 1},
        trade_message("2026-08-09T08:10:10Z", "110"),
        trade_message("2026-08-09T08:11:10Z", "111"),
    ]
    times = iter([
        pd.Timestamp("2026-08-09T08:00:00Z"),
        pd.Timestamp("2026-08-09T08:01:20Z"),
        pd.Timestamp("2026-08-09T08:02:20Z"),
        pd.Timestamp("2026-08-09T08:11:20Z"),
    ])
    result = run_forward_paper(
        transport=messages,
        max_processed_bars=10,
        audit_path=audit,
        now_fn=lambda: next(times),
        state_path=tmp_path / "state.json",
        resume=False,
        gap_recovery=FakeGapRecovery(fail=True),
    )
    rows = [json.loads(line) for line in audit.read_text(encoding="utf-8").splitlines()]
    assert any(row["type"] == "REST_BACKFILL_FAILED" for row in rows)
    assert rows[-1]["type"] == "SESSION_END"
    assert rows[-1]["reason"] == "BACKFILL_FATAL"
    assert rows[-1]["real_orders"] == 0
    assert result.processed_events == 2


def test_forward_session_uses_startup_catchup_without_retroactive_orders(tmp_path):
    from src.coinbase_market_data import CoinbaseCompletedBar
    from src.coinbase_live_paper import build_live_paper_runtime
    from src.forward_paper_session import ForwardContinuityStore
    from src.coinbase_market_data import CoinbaseOneMinuteTradeAggregator

    class StartupRecovery(FakeGapRecovery):
        def recover_startup(self, last_accepted, next_live):
            self.calls.append((pd.Timestamp(last_accepted), pd.Timestamp(next_live), "startup"))
            return tuple(
                CoinbaseCompletedBar(ts, 100, 100, 100, 100, 1)
                for ts in pd.date_range(
                    start=pd.Timestamp(last_accepted) + pd.Timedelta(minutes=1),
                    end=pd.Timestamp(next_live) - pd.Timedelta(minutes=1), freq="1min"
                )
            )

    state = tmp_path / "state.json"
    runtime = build_live_paper_runtime()
    runtime.realtime_feed._last_timestamp = pd.Timestamp("2026-08-09T00:00:00Z")
    runtime.realtime_feed._accepted = 1
    runtime._processed = 1
    runtime._last_event_at = pd.Timestamp("2026-08-09T00:00:00Z")
    ForwardContinuityStore(state).save(runtime, CoinbaseOneMinuteTradeAggregator())

    recovery = StartupRecovery()
    messages = [
        trade_message("2026-08-09T14:57:10Z", "100"),
        trade_message("2026-08-09T14:58:10Z", "101"),
        trade_message("2026-08-09T14:59:10Z", "102"),
    ]
    audit = tmp_path / "startup.jsonl"
    result = run_forward_paper(
        transport=messages, max_processed_bars=1, audit_path=audit,
        output=lambda _: None, now_fn=lambda: pd.Timestamp("2026-08-09T14:59:20Z"),
        state_path=state, gap_recovery=recovery,
    )
    rows = [json.loads(line) for line in audit.read_text(encoding="utf-8").splitlines()]
    catchup = [row for row in rows if row["type"] == "STARTUP_CATCHUP_BAR"]
    paper = [row for row in rows if row["type"] == "PAPER_EVENT"]
    assert len(catchup) == 896
    assert len(paper) == 1
    assert result.paper_orders == 0
    assert rows[-1]["real_orders"] == 0


def test_continuity_store_preserves_pending_post_recovery_reconciliation(tmp_path):
    from src.coinbase_live_paper import build_live_paper_runtime
    from src.coinbase_market_data import CoinbaseOneMinuteTradeAggregator
    from src.forward_paper_session import ForwardContinuityStore

    state = tmp_path / "state.json"
    runtime = build_live_paper_runtime()
    runtime._forward_pending_reconciliation = {
        "kind": "LONG_EXIT",
        "detected_at": "2026-08-10T12:27:00+00:00",
        "strategy": "ema_crossover",
        "boundary_kind": "RESTART",
    }
    ForwardContinuityStore(state).save(runtime, CoinbaseOneMinuteTradeAggregator())

    restored = build_live_paper_runtime()
    restored._forward_pending_reconciliation = None
    assert ForwardContinuityStore(state).load_into(restored, CoinbaseOneMinuteTradeAggregator())
    assert restored._forward_pending_reconciliation["kind"] == "LONG_EXIT"
    assert restored._forward_pending_reconciliation["detected_at"] == "2026-08-10T12:27:00+00:00"


def test_post_recovery_reconciliation_closes_long_on_first_fresh_live_bar(monkeypatch, tmp_path):
    from src.coinbase_live_paper import build_live_paper_runtime
    from src.coinbase_market_data import CoinbaseOneMinuteTradeAggregator
    from src.forward_paper_session import ForwardContinuityStore

    state = tmp_path / "state.json"
    runtime = build_live_paper_runtime()
    broker = runtime.session.engine.paper_broker
    broker.cash = 3750.0
    broker.position_quantity = 0.02
    broker.average_entry_price = 100.0
    broker.position_cost_basis = 2.0
    runtime.session._history = pd.DataFrame(
        [{"Open": 100.0, "High": 100.0, "Low": 100.0, "Close": 100.0, "Volume": 1.0}],
        index=pd.DatetimeIndex([pd.Timestamp("2026-08-10T12:00:00Z")]),
    )
    runtime.session.session._last_timestamp = pd.Timestamp("2026-08-10T12:00:00Z")
    runtime.realtime_feed._last_timestamp = pd.Timestamp("2026-08-10T12:00:00Z")
    runtime.realtime_feed._accepted = 1
    runtime._processed = 1
    runtime._last_event_at = pd.Timestamp("2026-08-10T12:00:00Z")
    ForwardContinuityStore(state).save(runtime, CoinbaseOneMinuteTradeAggregator())

    # Isolate the lifecycle contract: recovery observes a bearish strategy event,
    # but only the first fresh live bar is allowed to execute the exit.
    monkeypatch.setattr(
        "src.forward_paper_session._strategy_activity_diagnostics",
        lambda runtime: {"strategy": "ema_crossover", "signal": -1, "relation": "BELOW"},
    )
    messages = [
        trade_message("2026-08-10T12:05:10Z", "95"),
        trade_message("2026-08-10T12:06:10Z", "96"),
        trade_message("2026-08-10T12:07:10Z", "97"),
    ]
    audit = tmp_path / "reconcile.jsonl"
    result = run_forward_paper(
        transport=messages,
        max_processed_bars=1,
        audit_path=audit,
        output=lambda _: None,
        now_fn=lambda: pd.Timestamp("2026-08-10T12:06:20Z"),
        state_path=state,
        gap_recovery=FakeGapRecovery(),
    )

    rows = [json.loads(line) for line in audit.read_text(encoding="utf-8").splitlines()]
    detected = [row for row in rows if row["type"] == "RECOVERY_CROSSOVER_DETECTED"]
    reconciled = [row for row in rows if row["type"] == "POST_RECOVERY_RECONCILIATION"]
    paper = [row for row in rows if row["type"] == "PAPER_EVENT"]
    backfill = [row for row in rows if row["type"] == "REST_BACKFILL_BAR"]

    assert len(detected) == 1
    assert len(reconciled) == 1
    assert len(backfill) == 4
    assert all(row.get("real_orders") == 0 for row in backfill)
    assert paper[0]["event"]["signal"] == -1
    assert paper[0]["event"]["status"] == "FILLED"
    assert paper[0]["event"]["timestamp"] == "2026-08-10T12:05:00+00:00"
    assert reconciled[0]["executed_at"] == "2026-08-10T12:05:00+00:00"
    assert result.paper_orders == 1
    assert result.final_position == pytest.approx(0.0)
