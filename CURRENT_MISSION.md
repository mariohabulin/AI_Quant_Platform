# CURRENT MISSION — Phase 3 Multi-Asset Validation

## Objective

Test whether a frozen strategy's validated edge generalizes across multiple independent assets rather than depending on one instrument.

## Current Priorities

- run the existing Strategy Validation Pipeline independently per asset
- preserve identical execution, OOS, walk-forward and falsification assumptions
- keep asset-level evidence visible and auditable
- summarize cross-asset OOS return, excess return and persistence
- classify cross-asset evidence with explicit configurable thresholds
- preserve deterministic results and full backward compatibility
- keep all automated tests passing

## Multi-Asset Policy v1

Default requirements:

- at least 2 assets
- `VALIDATED`: at least 60% of assets individually `VALIDATED` and at most 20% `REJECTED`
- `REJECTED`: more than 50% of assets individually `REJECTED`
- otherwise: `CONDITIONAL`

This policy measures breadth of evidence. It does not replace future market-regime analysis, portfolio correlation analysis or Risk Engine limits.

## Next Mission

After multi-asset validation is proven, add Market Regime Detection and regime-conditioned validation before Risk Engine and paper trading.

Do not introduce the Strategy Optimizer yet.
