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
