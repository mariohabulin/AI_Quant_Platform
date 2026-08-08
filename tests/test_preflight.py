import pandas as pd

from src.operational_runtime import JsonCheckpointStore, PaperOperationalRuntime
from src.paper_broker import PaperBroker
from src.paper_trading import PaperTradingEngine, PaperTradingSession
from src.preflight import PaperPreFlightGate
from src.realtime_market_data import AlpacaCryptoBarAdapter, RealTimeMarketDataFeed
from src.risk_engine import RiskEngine


class HoldStrategy:
    def run(self, data):
        out = data.copy()
        out["Signal"] = 0
        return out


def make_runtime(tmp_path, risk=None):
    feed = RealTimeMarketDataFeed(AlpacaCryptoBarAdapter("BTC/USD"), timeframe="1min")
    risk = risk or RiskEngine(
        risk_per_trade=0.01, max_position_fraction=0.5,
        max_drawdown_fraction=0.10, daily_loss_limit=0.03,
        weekly_loss_limit=0.06, min_reward_risk=3.0,
    )
    broker = PaperBroker(initial_cash=5000)
    engine = PaperTradingEngine(HoldStrategy(), risk, broker)
    session = PaperTradingSession(engine)
    return PaperOperationalRuntime(feed, session, JsonCheckpointStore(tmp_path / "state.json"))


def creds():
    return {"ALPACA_API_KEY": "test-key", "ALPACA_API_SECRET": "test-secret"}


def gate(tmp_path, **kwargs):
    runtime = kwargs.pop("runtime", make_runtime(tmp_path))
    return PaperPreFlightGate(runtime, credentials=kwargs.pop("credentials", creds()),
                              connectivity_probe=kwargs.pop("connectivity_probe", lambda: True), **kwargs)


def test_preflight_passes_with_safe_controlled_configuration(tmp_path):
    report = gate(tmp_path).run()
    assert report.passed
    assert all(c.status == "PASS" for c in report.checks)


def test_report_never_contains_credentials(tmp_path):
    report = gate(tmp_path).run()
    text = repr(report)
    assert "test-key" not in text and "test-secret" not in text


def test_missing_credentials_fail_closed(tmp_path):
    report = gate(tmp_path, credentials={}).run()
    assert not report.passed
    assert next(c for c in report.checks if c.name == "credentials").status == "FAIL"


def test_placeholder_credentials_fail_closed(tmp_path):
    report = gate(tmp_path, credentials={"ALPACA_API_KEY": "YOUR_API_KEY", "ALPACA_API_SECRET": "changeme"}).run()
    assert not report.passed


def test_wrong_symbol_fails_scope(tmp_path):
    runtime = make_runtime(tmp_path)
    runtime.realtime_feed.adapter.symbol = "ETH/USD"
    report = gate(tmp_path, runtime=runtime).run()
    assert next(c for c in report.checks if c.name == "market_scope").status == "FAIL"


def test_wrong_timeframe_fails_scope(tmp_path):
    runtime = make_runtime(tmp_path)
    runtime.realtime_feed.timeframe = pd.Timedelta("5min")
    assert not gate(tmp_path, runtime=runtime).run().passed


def test_missing_protection_guards_fail_risk_policy(tmp_path):
    runtime = make_runtime(tmp_path, RiskEngine(risk_per_trade=0.01))
    assert next(c for c in gate(tmp_path, runtime=runtime).run().checks if c.name == "risk_policy").status == "FAIL"


def test_risk_above_one_percent_fails_policy(tmp_path):
    risk = RiskEngine(risk_per_trade=0.02, max_drawdown_fraction=.1, daily_loss_limit=.03,
                      weekly_loss_limit=.06, min_reward_risk=3)
    assert not gate(tmp_path, runtime=make_runtime(tmp_path, risk)).run().passed


def test_unexpected_open_position_fails_account_check(tmp_path):
    runtime = make_runtime(tmp_path)
    runtime.session.engine.paper_broker.position_quantity = 1
    assert next(c for c in gate(tmp_path, runtime=runtime).run().checks if c.name == "paper_account").status == "FAIL"


def test_checkpoint_store_is_required(tmp_path):
    runtime = make_runtime(tmp_path)
    runtime.checkpoint_store = None
    assert next(c for c in gate(tmp_path, runtime=runtime).run().checks if c.name == "checkpoint").status == "FAIL"


def test_execution_must_be_hard_disabled(tmp_path):
    report = gate(tmp_path, execution_enabled=True).run()
    assert next(c for c in report.checks if c.name == "execution_lock").status == "FAIL"


def test_connectivity_probe_is_required(tmp_path):
    report = gate(tmp_path, connectivity_probe=None).run()
    assert next(c for c in report.checks if c.name == "connectivity").status == "FAIL"


def test_connectivity_probe_exception_fails_without_leaking_exception(tmp_path):
    def broken():
        raise RuntimeError("secret provider detail")
    report = gate(tmp_path, connectivity_probe=broken).run()
    check = next(c for c in report.checks if c.name == "connectivity")
    assert check.status == "FAIL" and "secret provider detail" not in check.reason


def test_halted_runtime_fails_preflight(tmp_path):
    runtime = make_runtime(tmp_path)
    runtime._stop_requested = True
    report = gate(tmp_path, runtime=runtime).run()
    assert next(c for c in report.checks if c.name == "runtime_state").status == "FAIL"
