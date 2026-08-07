# CURRENT MISSION — Phase 3 Statistical Falsification

## Objective

Build a reproducible statistical robustness layer that actively attempts to falsify apparent strategy edge after realistic execution, benchmark, out-of-sample and walk-forward validation.

## Current Priorities

- bootstrap confidence intervals for net trade expectancy
- Monte Carlo trade-order stress testing for drawdown risk
- permutation testing against a zero-edge null hypothesis
- deterministic experiments through explicit random seeds
- fail-fast validation of research inputs
- preserve Strategy Library Version 1 and existing execution contracts
- keep all automated tests passing

## Architectural Rule

The falsification layer consumes completed trade history. It must not generate signals, optimize parameters, alter execution assumptions or mutate strategy logic.

## Completion Criteria

The milestone is complete when:

- bootstrap expectancy intervals are reproducible
- Monte Carlo drawdown distributions are reproducible
- permutation p-values are reproducible
- malformed or empty trade histories fail fast
- a conservative combined statistical-falsification result is exposed
- the complete automated test suite passes locally

## Next Mission

After statistical falsification is validated, build multi-asset strategy validation and formal strategy classification (`VALIDATED`, `CONDITIONAL`, `REJECTED`). Market-regime detection, Risk Engine, paper trading and live trading remain later phases.

Do not introduce the Strategy Optimizer yet.

## Relationship to Other Documents

`VISION.md` defines why the platform exists. `ROADMAP.md` defines long-term development. `ARCHITECTURE.md` defines permanent design principles. `LOG.md` records completed development history.
