# Strategy Evaluation Protocol v1

## Purpose

This protocol decides whether one pre-registered strategy has enough research
evidence to become a candidate for a later bounded forward-PAPER test. It does
not authorize live execution, and it does not replace the separate cloud
infrastructure gates.

## Activation boundary

The three-day cloud PAPER soak and protocol cloud integration are closed as
PASS. Offline pre-registration and evaluation of the first real candidate are
therefore authorized. A `PAPER_CANDIDATE` result authorizes only a separately
reviewed bounded forward-PAPER experiment.

## Pre-registration

Freeze these fields before inspecting final evaluation results:

- unique candidate ID
- exact Strategy Engine name
- falsifiable written hypothesis
- parameter-set ID or immutable parameter fingerprint
- dataset version
- timeframe
- exact named-asset scope
- chronological train/test/window configuration and random seed
- reviewed nonzero venue-cost assumptions and a harsher stress profile

Changing one of these fields creates a new candidate. It is not a continuation
of the old experiment.

## Execution timing integrity

Protocol v1 freezes these attainable execution semantics:

- a signal may observe a completed bar only after its close
- the signal executes, if actionable, at the following bar's open
- trade evidence retains both the signal-bar index and execution-bar index
- a signal from the final dataset bar is not executed because no following open
  exists
- an open terminal position is force-closed at the final bar's close for
  deterministic reporting, without inventing an exit signal
- buy-and-hold enters at the first bar's open and exits at the final close

The lower-level Backtesting Engine retains its legacy same-close default for
backward compatibility. The Strategy Evaluation configuration rejects that
mode: baseline and stressed evidence must both use `next_bar_open`, propagated
unchanged through OOS, walk-forward, pipeline and multi-asset evaluation.

## Initial promotion gates

| Gate | v1 requirement |
| --- | --- |
| Baseline evidence | Multi-asset `VALIDATED` |
| Cost-stress evidence | Multi-asset `VALIDATED` |
| Walk-forward coverage | At least 5 non-overlapping test windows per asset |
| Unseen trade evidence | At least 30 completed test trades per asset |
| Unseen OOS drawdown | At most 20% under either cost profile |
| Live authorization | Always `False` |

The numerical thresholds are configurable but versioned. Changing a threshold
after seeing a candidate result requires a new protocol version or an explicit
new evaluation; it must never silently turn a failure into a pass.

## Outcomes

- `PAPER_CANDIDATE`: every promotion gate passed; next stage is bounded
  forward PAPER after the infrastructure prerequisite is satisfied.
- `RESEARCH_HOLD`: the edge was not hard-rejected, but the evidence volume,
  persistence, cost stress or drawdown gate is incomplete.
- `REJECTED`: baseline/stress edge evidence failed, or frozen strategy/scope
  integrity was violated.

Every report includes the candidate declaration, complete frozen configuration,
failed gates, per-asset evidence and both underlying validation results.

## Example construction

```python
from strategy_evaluation_protocol import (
    ExecutionCostProfile,
    StrategyCandidate,
    StrategyEvaluationConfig,
    StrategyEvaluationProtocol,
)

candidate = StrategyCandidate(
    candidate_id="ema-20-50-v1",
    strategy_name="EMA_20_50",
    hypothesis="A persistent trend survives unseen windows and costs.",
    parameter_set_id="fast=20;slow=50",
    data_version="reviewed-dataset-v1",
    timeframe="1h",
    assets=("BTC-USD", "ETH-USD"),
)

configuration = StrategyEvaluationConfig(
    train_size=2160,
    test_size=720,
    baseline_costs=ExecutionCostProfile(
        "reviewed_baseline",
        commission_rate=0.001,
        slippage_rate=0.0005,
        spread_rate=0.001,
    ),
    stressed_costs=ExecutionCostProfile(
        "two_x_stress",
        commission_rate=0.002,
        slippage_rate=0.001,
        spread_rate=0.002,
    ),
    execution_timing="next_bar_open",
    terminal_position_policy="force_close_at_final_close",
)

report = StrategyEvaluationProtocol(
    strategy_engine,
    candidate,
    configuration,
).run({"BTC-USD": btc_data, "ETH-USD": eth_data})
```

The values above illustrate the API; dataset resolution, assets and venue costs
must be reviewed for the actual experiment before pre-registration.
