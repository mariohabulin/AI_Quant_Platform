import json

import pandas as pd
import pytest

from src.coinbase_dry_run import run_coinbase_dry_run


def message(*trades):
    return {"channel": "market_trades", "events": [{"trades": list(trades)}]}


def trade(time, price, size="0.1"):
    return {"time": time, "price": str(price), "size": str(size), "product_id": "BTC-USD"}


def test_dry_run_emits_one_health_gated_completed_bar_and_stops():
    transport = iter([
        {"channel": "heartbeats", "events": []},
        message(trade("2026-08-08T12:00:10Z", 100), trade("2026-08-08T12:00:40Z", 110, "0.2")),
        message(trade("2026-08-08T12:01:01Z", 105)),
        message(trade("2026-08-08T12:02:01Z", 106)),
    ])
    lines = []
    result = run_coinbase_dry_run(
        transport=transport, max_completed_bars=1, output=lines.append,
        now_fn=lambda: pd.Timestamp("2026-08-08T12:01:05Z"),
    )
    assert result.completed_bars == 1
    assert result.healthy_events == 1
    assert result.last_timestamp == pd.Timestamp("2026-08-08T12:00:00Z")
    assert any(line.startswith("HEALTHY BTC/USD 1m") for line in lines)
    assert all("order" not in line.lower() for line in lines)


def test_dry_run_rejects_stale_bar_fail_closed_and_can_accept_next_bar():
    transport = iter([
        message(trade("2026-08-08T12:00:10Z", 100)),
        message(trade("2026-08-08T12:01:01Z", 101)),
        message(trade("2026-08-08T12:02:01Z", 102)),
        message(trade("2026-08-08T12:03:01Z", 103)),
    ])
    times = iter([pd.Timestamp("2026-08-08T12:05:00Z"), pd.Timestamp("2026-08-08T12:02:05Z")])
    lines = []
    result = run_coinbase_dry_run(transport=transport, max_completed_bars=1, output=lines.append, now_fn=lambda: next(times))
    assert result.completed_bars == 2
    assert result.healthy_events == 1
    assert any(line.startswith("REJECTED") for line in lines)


def test_dry_run_requires_positive_bar_limit():
    with pytest.raises(ValueError):
        run_coinbase_dry_run(transport=iter([]), max_completed_bars=0)
