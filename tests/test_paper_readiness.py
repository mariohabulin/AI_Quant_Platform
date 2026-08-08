import pandas as pd
import pytest

from src.backtest import BacktestingEngine
from src.paper_broker import PaperBroker
from src.paper_readiness import PaperReadinessGate, ReadinessScenario
from src.paper_trading import PaperTradingEngine, PaperTradingSession
from src.replay_consistency import ReplayConsistencyValidator
from src.risk_engine import RiskEngine


class LengthSignalStrategy:
    def __init__(self, signals):
        self.signals = tuple(signals)

    def run(self, data):
        result = data.copy()
        result["Signal"] = list(self.signals[:len(result)])
        result["Stop"] = result["Close"] - 2.0
        return result


def bars():
    index = pd.date_range("2026-08-01", periods=4, freq="h")
    close = [100.0, 105.0, 110.0, 108.0]
    return pd.DataFrame({
        "Open": close, "High": close, "Low": close, "Close": close,
        "Volume": [1000.0] * 4,
    }, index=index)


def stop(event):
    return float(event.bar["Close"]) - 2.0


def validator(signals=(1, 0, -1, 0), paper_slippage=0.0):
    backtest = BacktestingEngine(
        LengthSignalStrategy(signals),
        risk_engine=RiskEngine(risk_per_trade=0.01, max_position_fraction=1.0),
    )
    broker = PaperBroker(initial_cash=10000.0, slippage_rate=paper_slippage)
    paper = PaperTradingEngine(
        LengthSignalStrategy(signals),
        RiskEngine(risk_per_trade=0.01, max_position_fraction=1.0),
        broker,
    )
    return ReplayConsistencyValidator(backtest, PaperTradingSession(paper))


def scenario(name="round_trip", **kwargs):
    return ReadinessScenario(name=name, validator=validator(), data=bars(), stop_resolver=stop, **kwargs)


def test_gate_requires_at_least_one_scenario():
    with pytest.raises(ValueError, match="At least one"):
        PaperReadinessGate([])


def test_scenario_names_must_be_non_empty_and_unique():
    with pytest.raises(ValueError, match="non-empty"):
        PaperReadinessGate([scenario(name="")])
    with pytest.raises(ValueError, match="unique"):
        PaperReadinessGate([scenario(name="x"), scenario(name="x")])


def test_invalid_divergence_classification_is_rejected():
    with pytest.raises(ValueError, match="Invalid divergence"):
        PaperReadinessGate([scenario(divergence_classification="MAYBE")])


def test_consistent_representative_scenario_passes_as_match():
    report = PaperReadinessGate([scenario()]).run()
    assert report.status == "READY"
    assert report.is_ready
    assert report.evidence[0].classification == "MATCH"
    assert report.evidence[0].gate_passed


def test_unexpected_execution_drift_blocks_gate():
    drift = ReadinessScenario(
        name="execution_drift", validator=validator(paper_slippage=0.01),
        data=bars(), stop_resolver=stop,
        divergence_classification="DEFECT",
    )
    report = PaperReadinessGate([drift]).run()
    assert report.status == "BLOCKED"
    assert report.blocking_evidence
    assert "trade_1.entry_fill_price" in report.evidence[0].unexpected_difference_fields


def test_known_forced_close_semantics_can_be_classified_as_intended():
    open_position = ReadinessScenario(
        name="forced_close_semantics", validator=validator(signals=(1, 0, 0, 0)),
        data=bars(), stop_resolver=stop,
        expected_difference_fields=("trade_count", "open_position_state"),
        divergence_classification="INTENDED",
    )
    report = PaperReadinessGate([open_position]).run()
    assert report.is_ready
    assert report.evidence[0].classification == "INTENDED"
    assert report.evidence[0].unexpected_difference_fields == ()


def test_intended_classification_does_not_hide_unexpected_difference():
    item = ReadinessScenario(
        name="bad_allowlist", validator=validator(paper_slippage=0.01),
        data=bars(), stop_resolver=stop,
        expected_difference_fields=("trade_1.entry_fill_price",),
        divergence_classification="INTENDED",
    )
    report = PaperReadinessGate([item]).run()
    assert not report.is_ready
    assert report.evidence[0].unexpected_difference_fields


def test_configuration_mismatch_is_blocking_even_when_fields_are_expected():
    probe = validator(paper_slippage=0.01).run(bars(), stop_resolver=stop)
    expected = tuple(d.field for d in probe.differences)
    item = ReadinessScenario(
        name="config_mismatch", validator=validator(paper_slippage=0.01),
        data=bars(), stop_resolver=stop,
        expected_difference_fields=expected,
        divergence_classification="CONFIGURATION_MISMATCH",
    )
    report = PaperReadinessGate([item]).run()
    assert report.status == "BLOCKED"
    assert report.evidence[0].classification == "CONFIGURATION_MISMATCH"


def test_expected_divergence_missing_from_consistent_run_blocks_stale_allowlist():
    item = scenario(expected_difference_fields=("trade_count",), divergence_classification="INTENDED")
    report = PaperReadinessGate([item]).run()
    assert report.status == "BLOCKED"


def test_gate_aggregates_multiple_representative_scenarios():
    normal = scenario(name="normal_round_trip")
    forced = ReadinessScenario(
        name="forced_close", validator=validator(signals=(1, 0, 0, 0)),
        data=bars(), stop_resolver=stop,
        expected_difference_fields=("trade_count", "open_position_state"),
        divergence_classification="INTENDED",
    )
    report = PaperReadinessGate([normal, forced]).run()
    assert report.is_ready
    assert [item.classification for item in report.evidence] == ["MATCH", "INTENDED"]
