import json
import pandas as pd
import pytest

from src.coinbase_live_paper import AccumulatingPaperSession, run_coinbase_live_paper
from src.paper_broker import PaperBroker
from src.paper_trading import PaperTradingEngine, PaperTradingSession
from src.risk_engine import RiskEngine


class HoldStrategy:
    def run(self, data):
        result = data.copy()
        result["Signal"] = 0
        return result


def one_row(ts, close):
    return pd.DataFrame({"Open":[close],"High":[close],"Low":[close],"Close":[close],"Volume":[1.0]}, index=[pd.Timestamp(ts)])


def test_accumulating_session_preserves_history_and_paper_only_state():
    engine = PaperTradingEngine(HoldStrategy(), RiskEngine(), PaperBroker(initial_cash=5000))
    bridge = AccumulatingPaperSession(PaperTradingSession(engine))
    bridge.process(one_row("2026-08-08T18:00:00Z", 100), timestamp="2026-08-08T18:00:00Z")
    snap = bridge.process(one_row("2026-08-08T18:01:00Z", 101), timestamp="2026-08-08T18:01:00Z")
    assert len(bridge._history) == 2
    assert snap.equity == pytest.approx(5000)
    assert len(engine.paper_broker.order_history) == 0


def test_live_paper_runner_rejects_invalid_bound():
    with pytest.raises(ValueError, match="positive integer"):
        run_coinbase_live_paper(transport=[], max_processed_bars=0)


def test_strategy_engine_is_importable_as_src_package():
    from src.strategy_engine import StrategyEngine
    assert StrategyEngine is not None
