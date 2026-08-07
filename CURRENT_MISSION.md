# CURRENT MISSION — Phase 3 Strategy Validation Pipeline v1

## Objective

Unify the completed Phase 3 validation components into one deterministic research pipeline with an explicit and inspectable strategy-classification policy.

## Current Priorities

- orchestrate OOS, walk-forward and statistical falsification without changing strategy logic
- use only unseen walk-forward test trades for statistical falsification
- expose one structured research result per strategy
- classify evidence as `VALIDATED`, `CONDITIONAL` or `REJECTED`
- keep classification thresholds explicit and configurable
- preserve realistic execution and benchmark assumptions throughout validation
- keep all automated tests passing

## Validation Policy v1

Hard gates:

- positive OOS strategy return
- positive OOS excess return versus buy-and-hold
- successful statistical falsification

Persistence gate:

- positive excess return in at least 60% of walk-forward test windows by default

Classification:

- any failed hard gate -> `REJECTED`
- hard gates pass but persistence gate fails -> `CONDITIONAL`
- all gates pass -> `VALIDATED`

Monte Carlo drawdown is reported but is not yet a classification gate. The future Risk Engine must define normalized drawdown tolerances before drawdown can safely determine approval status.

## Next Mission

After the single-strategy validation pipeline is proven, build multi-asset strategy validation. Market-regime detection, Risk Engine, paper trading and live trading remain later phases.

Do not introduce the Strategy Optimizer yet.
