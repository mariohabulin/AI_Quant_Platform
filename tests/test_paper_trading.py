import pandas as pd
import pytest

from src.paper_broker import PaperBroker
from src.paper_trading import PaperTradingEngine
from src.risk_engine import RiskEngine


class StubStrategyEngine:
    def __init__(self, signal):
        self.signal = signal
        self.calls = 0

    def run(self, data):
        self.calls += 1
        result = data.copy()
        result["Signal"] = 0
        result.iloc[-1, result.columns.get_loc("Signal")] = self.signal
        return result


def market_data(price=100.0, timestamp="2026-08-08 10:00"):
    return pd.DataFrame(
        {"Open": [price], "High": [price], "Low": [price], "Close": [price], "Volume": [1000]},
        index=pd.to_datetime([timestamp]),
    )


def make_engine(signal, cash=10000.0, **risk_kwargs):
    return PaperTradingEngine(
        StubStrategyEngine(signal),
        RiskEngine(**risk_kwargs),
        PaperBroker(initial_cash=cash),
    )


def test_requires_all_orchestration_dependencies():
    with pytest.raises(ValueError, match="strategy_engine"):
        PaperTradingEngine(None, RiskEngine(), PaperBroker())
    with pytest.raises(ValueError, match="risk_engine"):
        PaperTradingEngine(StubStrategyEngine(0), None, PaperBroker())
    with pytest.raises(ValueError, match="paper_broker"):
        PaperTradingEngine(StubStrategyEngine(0), RiskEngine(), None)


def test_hold_signal_creates_no_order_and_audit_event():
    engine = make_engine(0)
    event = engine.process_market_event(market_data())
    assert event.status == "NO_ACTION"
    assert event.signal == 0
    assert len(engine.paper_broker.order_history) == 0
    assert len(engine.event_history) == 1


def test_buy_signal_is_risk_sized_then_filled_by_broker():
    engine = make_engine(1, risk_per_trade=0.01)
    event = engine.process_market_event(market_data(), stop_price=98.0)
    assert event.status == "FILLED"
    assert event.risk_status == "ALLOW"
    assert event.quantity == pytest.approx(50.0)
    assert engine.paper_broker.position_quantity == pytest.approx(50.0)


def test_exposure_cap_reduction_is_preserved_in_audit_event():
    engine = make_engine(1, risk_per_trade=0.10, max_position_fraction=0.20)
    event = engine.process_market_event(market_data(), stop_price=99.0)
    assert event.status == "FILLED"
    assert event.risk_status == "REDUCE"
    assert event.quantity == pytest.approx(20.0)


def test_buy_requires_stop_before_risk_authorization():
    engine = make_engine(1)
    with pytest.raises(ValueError, match="requires stop_price"):
        engine.process_market_event(market_data())
    assert len(engine.paper_broker.order_history) == 0


def test_reward_risk_policy_can_reject_before_order_submission():
    engine = make_engine(1, min_reward_risk=3.0)
    event = engine.process_market_event(market_data(), stop_price=98.0, target_price=104.0)
    assert event.status == "REJECTED"
    assert event.risk_status == "REJECT"
    assert len(engine.paper_broker.order_history) == 0


def test_protection_guard_rejects_new_risk_before_order_submission():
    engine = make_engine(1, max_drawdown_fraction=0.05)
    engine.risk_engine.observe_equity(10000, "2026-08-07")
    engine.risk_engine.observe_equity(9000, "2026-08-08")
    event = engine.process_market_event(market_data(timestamp="2026-08-08 10:00"), stop_price=98.0)
    assert event.status == "REJECTED"
    assert "drawdown" in event.reason.lower()
    assert len(engine.paper_broker.order_history) == 0


def test_repeated_buy_does_not_pyramid_existing_long_position():
    engine = make_engine(1)
    engine.process_market_event(market_data(), stop_price=98.0)
    event = engine.process_market_event(market_data(101, "2026-08-08 11:00"), stop_price=99.0)
    assert event.status == "NO_ACTION"
    assert "already open" in event.reason
    assert len(engine.paper_broker.order_history) == 1


def test_sell_signal_closes_entire_existing_long_position():
    strategy = StubStrategyEngine(1)
    engine = PaperTradingEngine(strategy, RiskEngine(), PaperBroker(initial_cash=10000))
    engine.process_market_event(market_data(), stop_price=98.0)
    strategy.signal = -1
    event = engine.process_market_event(market_data(105, "2026-08-08 11:00"))
    assert event.status == "FILLED"
    assert event.quantity == pytest.approx(50.0)
    assert engine.paper_broker.position_quantity == 0.0
    assert engine.paper_broker.realized_pnl == pytest.approx(250.0)


def test_sell_without_position_is_no_action():
    engine = make_engine(-1)
    event = engine.process_market_event(market_data())
    assert event.status == "NO_ACTION"
    assert len(engine.paper_broker.order_history) == 0


def test_broker_execution_costs_flow_through_orchestration():
    broker = PaperBroker(initial_cash=10000, commission_rate=0.001, slippage_rate=0.01, spread_rate=0.02)
    engine = PaperTradingEngine(StubStrategyEngine(1), RiskEngine(risk_per_trade=0.001), broker)
    event = engine.process_market_event(market_data(), stop_price=98.0)
    assert event.fill_price == pytest.approx(102.0)
    assert broker.order_history[0].commission > 0


def test_event_history_is_immutable_view_with_deterministic_sequence():
    engine = make_engine(0)
    first = engine.process_market_event(market_data())
    second = engine.process_market_event(market_data(101, "2026-08-08 11:00"))
    assert isinstance(engine.event_history, tuple)
    assert (first.sequence, second.sequence) == (1, 2)


def test_strategy_receives_only_data_supplied_for_current_event():
    strategy = StubStrategyEngine(0)
    engine = PaperTradingEngine(strategy, RiskEngine(), PaperBroker())
    data = pd.concat([market_data(100, "2026-08-08 10:00"), market_data(101, "2026-08-08 11:00")])
    engine.process_market_event(data.iloc[:1])
    assert strategy.calls == 1
    assert engine.event_history[-1].market_price == 100.0


from src.paper_trading import PaperTradingSession


def test_session_requires_paper_trading_engine():
    with pytest.raises(ValueError, match="engine is required"):
        PaperTradingSession(None)
    with pytest.raises(TypeError, match="PaperTradingEngine"):
        PaperTradingSession(object())


def test_session_records_mark_to_market_snapshot_for_hold():
    session = PaperTradingSession(make_engine(0))
    snapshot = session.process(market_data(100))
    assert snapshot.sequence == 1
    assert snapshot.equity == pytest.approx(10000.0)
    assert snapshot.position_quantity == 0.0
    assert snapshot.event_status == "NO_ACTION"


def test_session_carries_open_position_across_market_events():
    strategy = StubStrategyEngine(1)
    engine = PaperTradingEngine(strategy, RiskEngine(), PaperBroker(initial_cash=10000))
    session = PaperTradingSession(engine)
    first = session.process(market_data(100, "2026-08-08 10:00"), stop_price=98)
    strategy.signal = 0
    second = session.process(market_data(105, "2026-08-08 11:00"))
    assert first.position_quantity == pytest.approx(50.0)
    assert second.position_quantity == pytest.approx(50.0)
    assert second.equity == pytest.approx(10250.0)


def test_session_sell_realizes_pnl_and_closes_position():
    strategy = StubStrategyEngine(1)
    engine = PaperTradingEngine(strategy, RiskEngine(), PaperBroker(initial_cash=10000))
    session = PaperTradingSession(engine)
    session.process(market_data(100, "2026-08-08 10:00"), stop_price=98)
    strategy.signal = -1
    snapshot = session.process(market_data(105, "2026-08-08 11:00"))
    assert snapshot.position_quantity == 0.0
    assert snapshot.realized_pnl == pytest.approx(250.0)
    assert snapshot.equity == pytest.approx(10250.0)


def test_session_snapshots_are_immutable_view_and_sequenced():
    session = PaperTradingSession(make_engine(0))
    session.process(market_data(100, "2026-08-08 10:00"))
    session.process(market_data(101, "2026-08-08 11:00"))
    assert isinstance(session.snapshot_history, tuple)
    assert [s.sequence for s in session.snapshot_history] == [1, 2]
    assert session.last_snapshot.sequence == 2


def test_session_rejects_non_increasing_timestamps():
    session = PaperTradingSession(make_engine(0))
    session.process(market_data(100, "2026-08-08 10:00"))
    with pytest.raises(ValueError, match="strictly increasing"):
        session.process(market_data(101, "2026-08-08 10:00"))


def test_session_rejects_empty_market_data():
    session = PaperTradingSession(make_engine(0))
    with pytest.raises(ValueError, match="cannot be empty"):
        session.process(pd.DataFrame())


def test_session_run_processes_ordered_event_sequence():
    session = PaperTradingSession(make_engine(0))
    snapshots = session.run([
        {"data": market_data(100, "2026-08-08 10:00")},
        {"data": market_data(101, "2026-08-08 11:00")},
        {"data": market_data(102, "2026-08-08 12:00")},
    ])
    assert isinstance(snapshots, tuple)
    assert len(snapshots) == 3
    assert snapshots[-1].market_price == 102.0


def test_session_run_requires_data_in_each_event():
    session = PaperTradingSession(make_engine(0))
    with pytest.raises(ValueError, match="containing data"):
        session.run([{"timestamp": "2026-08-08 10:00"}])


def test_session_preserves_risk_protection_state_across_events():
    strategy = StubStrategyEngine(0)
    risk = RiskEngine(max_drawdown_fraction=0.05)
    engine = PaperTradingEngine(strategy, risk, PaperBroker(initial_cash=10000))
    session = PaperTradingSession(engine)
    session.process(market_data(100, "2026-08-08 10:00"))
    engine.paper_broker.cash = 9000.0
    strategy.signal = 1
    snapshot = session.process(market_data(100, "2026-08-08 11:00"), stop_price=98)
    assert snapshot.event_status == "REJECTED"
    assert risk.kill_switch_active is True
    assert engine.paper_broker.position_quantity == 0.0


def test_session_uses_explicit_timestamp_for_ordered_clock():
    session = PaperTradingSession(make_engine(0))
    snapshot = session.process(
        market_data(100, "2026-08-08 09:00"),
        timestamp="2026-08-08 10:30",
    )
    assert snapshot.timestamp == pd.Timestamp("2026-08-08 10:30")


def test_session_does_not_reset_engine_or_broker_state_between_process_calls():
    strategy = StubStrategyEngine(1)
    engine = PaperTradingEngine(strategy, RiskEngine(), PaperBroker(initial_cash=10000))
    session = PaperTradingSession(engine)
    session.process(market_data(100, "2026-08-08 10:00"), stop_price=98)
    order_count = len(engine.paper_broker.order_history)
    session.process(market_data(101, "2026-08-08 11:00"), stop_price=99)
    assert len(engine.paper_broker.order_history) == order_count
    assert len(engine.event_history) == 2


def test_reconcile_long_exit_executes_at_current_bar_without_replaying_strategy_signal():
    from src.paper_broker import PaperBroker
    from src.paper_trading import PaperTradingEngine
    from src.risk_engine import RiskEngine

    class HoldStrategyEngine:
        def run(self, data):
            result = data.copy()
            result["Signal"] = 0
            return result

    broker = PaperBroker(initial_cash=5000.0)
    broker.position_quantity = 1.0
    broker.average_entry_price = 100.0
    broker.position_cost_basis = 100.0
    broker.cash = 4900.0
    engine = PaperTradingEngine(HoldStrategyEngine(), RiskEngine(), broker)
    now = pd.Timestamp("2026-08-10T13:00:00Z")
    data = pd.DataFrame({"Close": [95.0]}, index=[now])

    event = engine.reconcile_long_exit(data, timestamp=now)

    assert event.signal == -1
    assert event.status == "FILLED"
    assert event.timestamp == now
    assert event.fill_price == pytest.approx(95.0)
    assert broker.position_quantity == pytest.approx(0.0)
