import pytest

from src.paper_broker import PaperBroker


def test_broker_starts_with_clean_account_state():
    broker = PaperBroker(initial_cash=5000.0)

    snapshot = broker.account_snapshot()

    assert snapshot["cash"] == pytest.approx(5000.0)
    assert snapshot["position_quantity"] == 0.0
    assert snapshot["realized_pnl"] == 0.0
    assert snapshot["equity"] == pytest.approx(5000.0)


def test_market_order_is_submitted_with_deterministic_id():
    broker = PaperBroker()

    first = broker.submit_market_order("buy", 2)
    second = broker.submit_market_order("SELL", 1)

    assert first.order_id == "PB-000001"
    assert second.order_id == "PB-000002"
    assert first.status == "SUBMITTED"
    assert second.status == "SUBMITTED"


def test_buy_market_order_fills_and_updates_account_state():
    broker = PaperBroker(initial_cash=1000.0)
    order = broker.submit_market_order("BUY", 5)

    result = broker.execute_order(order.order_id, market_price=100.0)
    snapshot = broker.account_snapshot(mark_price=100.0)

    assert result.status == "FILLED"
    assert result.fill_price == pytest.approx(100.0)
    assert snapshot["cash"] == pytest.approx(500.0)
    assert snapshot["position_quantity"] == pytest.approx(5.0)
    assert snapshot["average_entry_price"] == pytest.approx(100.0)
    assert snapshot["equity"] == pytest.approx(1000.0)


def test_execution_models_commission_slippage_and_spread():
    broker = PaperBroker(
        initial_cash=2000.0,
        commission_rate=0.01,
        slippage_rate=0.01,
        spread_rate=0.02,
    )
    order = broker.submit_market_order("BUY", 10)

    result = broker.execute_order(order.order_id, market_price=100.0)

    assert result.fill_price == pytest.approx(102.0)
    assert result.commission == pytest.approx(10.2)
    assert broker.cash == pytest.approx(969.8)


def test_insufficient_cash_rejects_buy_without_mutating_position():
    broker = PaperBroker(initial_cash=100.0)
    order = broker.submit_market_order("BUY", 2)

    result = broker.execute_order(order.order_id, market_price=100.0)
    snapshot = broker.account_snapshot(mark_price=100.0)

    assert result.status == "REJECTED"
    assert result.reason == "INSUFFICIENT_CASH"
    assert snapshot["cash"] == pytest.approx(100.0)
    assert snapshot["position_quantity"] == 0.0


def test_sell_market_order_realizes_pnl_and_reduces_position():
    broker = PaperBroker(initial_cash=2000.0)
    buy = broker.submit_market_order("BUY", 10)
    broker.execute_order(buy.order_id, market_price=100.0)
    sell = broker.submit_market_order("SELL", 4)

    result = broker.execute_order(sell.order_id, market_price=110.0)
    snapshot = broker.account_snapshot(mark_price=110.0)

    assert result.status == "FILLED"
    assert snapshot["position_quantity"] == pytest.approx(6.0)
    assert snapshot["realized_pnl"] == pytest.approx(40.0)
    assert snapshot["equity"] == pytest.approx(2100.0)


def test_sell_more_than_position_is_rejected():
    broker = PaperBroker(initial_cash=1000.0)
    buy = broker.submit_market_order("BUY", 2)
    broker.execute_order(buy.order_id, market_price=100.0)
    sell = broker.submit_market_order("SELL", 3)

    result = broker.execute_order(sell.order_id, market_price=100.0)

    assert result.status == "REJECTED"
    assert result.reason == "INSUFFICIENT_POSITION"
    assert broker.position_quantity == pytest.approx(2.0)


def test_submitted_order_can_be_cancelled_before_execution():
    broker = PaperBroker()
    order = broker.submit_market_order("BUY", 1, timestamp="t0")

    result = broker.cancel_order(order.order_id, timestamp="t1")

    assert result.status == "CANCELLED"
    assert result.cancelled_at == "t1"
    with pytest.raises(ValueError):
        broker.execute_order(order.order_id, market_price=100.0)


def test_filled_order_cannot_be_cancelled_or_executed_twice():
    broker = PaperBroker()
    order = broker.submit_market_order("BUY", 1)
    broker.execute_order(order.order_id, market_price=100.0)

    with pytest.raises(ValueError):
        broker.cancel_order(order.order_id)
    with pytest.raises(ValueError):
        broker.execute_order(order.order_id, market_price=101.0)


def test_multiple_buys_use_weighted_average_entry_price():
    broker = PaperBroker(initial_cash=5000.0)
    first = broker.submit_market_order("BUY", 2)
    broker.execute_order(first.order_id, market_price=100.0)
    second = broker.submit_market_order("BUY", 2)
    broker.execute_order(second.order_id, market_price=120.0)

    snapshot = broker.account_snapshot(mark_price=120.0)

    assert snapshot["position_quantity"] == pytest.approx(4.0)
    assert snapshot["average_entry_price"] == pytest.approx(110.0)


def test_order_history_preserves_lifecycle_evidence():
    broker = PaperBroker(initial_cash=1000.0)
    order = broker.submit_market_order("BUY", 1, timestamp="submit")
    broker.execute_order(order.order_id, market_price=100.0, timestamp="fill")

    history = broker.order_history

    assert len(history) == 1
    assert history[0].submitted_at == "submit"
    assert history[0].filled_at == "fill"
    assert history[0].status == "FILLED"


def test_invalid_constructor_and_order_inputs_fail_fast():
    with pytest.raises(ValueError):
        PaperBroker(initial_cash=0)
    with pytest.raises(ValueError):
        PaperBroker(commission_rate=-0.1)

    broker = PaperBroker()
    with pytest.raises(ValueError):
        broker.submit_market_order("HOLD", 1)
    with pytest.raises(ValueError):
        broker.submit_market_order("BUY", 0)
    order = broker.submit_market_order("BUY", 1)
    with pytest.raises(ValueError):
        broker.execute_order(order.order_id, market_price=0)
