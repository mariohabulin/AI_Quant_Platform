import json

import pandas as pd
import pytest

from src.forward_paper_session import JsonlForwardAudit, run_forward_paper


def trade_message(ts, price="100", size="1"):
    return {
        "channel": "market_trades",
        "events": [{"trades": [{"product_id": "BTC-USD", "price": price, "size": size, "time": ts}]}],
    }


def test_jsonl_audit_appends_parseable_records(tmp_path):
    path = tmp_path / "audit.jsonl"
    audit = JsonlForwardAudit(path)
    audit.append({"type": "TEST", "at": pd.Timestamp("2026-08-08T18:00:00Z")})
    audit.append({"type": "TEST2", "value": 2})
    rows = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]
    assert [row["type"] for row in rows] == ["TEST", "TEST2"]
    assert rows[0]["at"] == "2026-08-08T18:00:00+00:00"


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

    store = ForwardContinuityStore(tmp_path / "state.json")
    store.save(runtime, aggregator)
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
    result = run_forward_paper(
        transport=messages,
        max_processed_bars=2,
        audit_path=audit,
        output=output.append,
        now_fn=lambda: next(clock),
        state_path=state,
    )

    rows = [json.loads(line) for line in audit.read_text(encoding="utf-8").splitlines()]
    rebases = [row for row in rows if row["type"] == "RESTART_REBASE"]
    paper = [row for row in rows if row["type"] == "PAPER_EVENT"]
    assert len(rebases) == 1
    assert rebases[0]["timestamp"] == "2026-08-08T19:52:00+00:00"
    assert len(paper) == 2
    assert result.processed_events == 2
    assert result.rejected_events == 0
    assert result.final_position == pytest.approx(0.02)
    assert any(line.startswith("REBASE ") for line in output)
    assert paper[0]["snapshot"]["timestamp"] == "2026-08-08T19:53:00+00:00"


def test_forward_session_audits_reconnect_and_rebases_without_trading_boundary_bar(tmp_path):
    state = tmp_path / "state.json"
    audit = tmp_path / "audit.jsonl"
    messages = [
        trade_message("2026-08-09T08:00:10Z", "100"),
        trade_message("2026-08-09T08:01:10Z", "101"),
        trade_message("2026-08-09T08:02:10Z", "102"),
        {"channel": "_coinbase_transport", "event": "DISCONNECTED", "attempt": 1, "reason": "test"},
        {"channel": "_coinbase_transport", "event": "RECONNECTED", "reconnect_count": 1},
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
    result = run_forward_paper(
        transport=messages,
        max_processed_bars=3,
        audit_path=audit,
        output=output.append,
        now_fn=lambda: next(times),
        state_path=state,
        resume=False,
    )
    rows = [json.loads(line) for line in audit.read_text(encoding="utf-8").splitlines()]
    transport_events = [row for row in rows if row["type"] == "TRANSPORT_EVENT"]
    reconnect_rebases = [row for row in rows if row["type"] == "RECONNECT_REBASE"]
    paper = [row for row in rows if row["type"] == "PAPER_EVENT"]
    assert [row["event"] for row in transport_events] == ["DISCONNECTED", "RECONNECTED"]
    assert len(reconnect_rebases) == 1
    assert len(paper) == 3
    assert result.processed_events == 3
    assert result.rejected_events == 0
    assert any(line.startswith("TRANSPORT DISCONNECTED") for line in output)
    assert any("reconnect gap reconciled" in line for line in output)


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
