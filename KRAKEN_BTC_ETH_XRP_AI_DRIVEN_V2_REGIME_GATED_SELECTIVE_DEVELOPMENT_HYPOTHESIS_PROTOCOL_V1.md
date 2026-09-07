# Kraken BTC/ETH/XRP AI-Driven V2 Regime-Gated Selective Development Hypothesis V1

## Purpose and prior evidence

Protocol ID:
`kraken-btc-eth-xrp-ai-v2-regime-gated-selective-development-hypothesis-v1`.

The bidirectional 12h hypothesis is closed `HOLD_CASH`. Its read-only forensic
review proved correct action and label polarity, but positive SHORT scores were
dominated by false positives and every direction/variant top-decile mean was
negative. This protocol permits one materially different Development question:
can an explicit causal spot regime, a directional derivatives confirmation and
a calibrated profitable-outcome probability isolate a small stable opportunity
set?

This is a pre-registration only. It opens no archive, dataset value, evidence
artifact, Calibration or Evaluation row and trains no model.

## Frozen causal information and regime

No new indicator is created. Both variants reuse the exact sixteen spot
features and asset identity. The context variant also reuses the exact nine
funding, open-interest and basis features. All rows remain restricted to the
existing context-complete interval and three 30-day-purged outer folds.

The direction gate is determined before model scoring:

- `LONG_REGIME`: `return_14`, `ema_12_48_spread` and `ema_180_distance` are all
  strictly positive;
- `SHORT_REGIME`: the same three values are all strictly negative;
- every mixed or zero-sign state is `NEUTRAL` and must return `HOLD_CASH`.

The control uses this spot regime without derivatives confirmation. The context
variant additionally requires six-bar open-interest log change above zero and
basis change aligned with direction. To avoid joining an already crowded move,
funding z-score must be at most `+1.0` for LONG and at least `-1.0` for SHORT.
These are frozen semantic zero/one-standard-deviation boundaries, not values
selected from Development outcomes.

## Frozen target, learner and economic threshold

For each regime-eligible direction, the binary target is whether the existing
cost-aware directional `outcome_net_r` is strictly positive. Entry, 60-bar
horizon, `1.5 ATR` risk unit, `3R` target, `1R` stop, adverse costs, gap handling
and same-bar stop-first behavior do not change.

Exactly two variants are allowed:

1. `SPOT_REGIME_CALIBRATED_LOGISTIC_CONTROL`;
2. `SPOT_CONTEXT_REGIME_CALIBRATED_LOGISTIC`.

Each direction and outer fold receives one natural-frequency regularized
logistic base model. The earlier 75% of eligible outer-training rows fits the
base model; the later 25% fits one sigmoid calibrator. Validation never fits a
model, calibrator, payoff mean or threshold. The maximum budget is twelve base
models and twelve calibrators. Missing positive/nonpositive class support fails
the affected fold closed.

The base-fit region alone supplies mean positive and mean nonpositive net R.
Their implied break-even probability is
`-mean_nonpositive / (mean_positive - mean_nonpositive)`. The required
calibrated probability is that break-even value plus an immutable `0.05`
absolute safety buffer, capped at `1.0`. Equality never trades. Context failure,
neutral regime or an insufficient probability returns `HOLD_CASH`.

There is no class weighting, direct-net-R regression, feature search,
hyperparameter sweep, threshold sweep, top-k rule or automatic winner.

## Frozen evidence gates

Each variant must have at least 30 raw and ten chronological non-overlapping
selections in every fold, positive non-overlapping mean and cumulative net R in
every fold and overall, and positive net R on at least two assets. In addition,
each direction's calibrated probabilities must beat the corresponding
outer-training prevalence forecast by Brier score in every supported fold.

The context variant must also beat the matched spot control in overall mean net
R, worst-fold mean net R and at least two fold means. The control can establish
absolute Development evidence but can never prove the incremental context
claim. No model is promoted automatically; any passer requires human review and
separate Calibration authorization.

## Terminal research stop

Exactly one economic Development execution of these two variants is permitted
after a separate runner, static review, preflight and operator authorization. If
neither variant passes every applicable frozen gate, the terminal status is
`KRAKEN_AI_V2_REGIME_GATED_SELECTIVE_NO_VIABLE_HYPOTHESIS_STOP_KRAKEN_12H_RESEARCH`.
The Kraken BTC/ETH/XRP 12h research branch then closes. There is no threshold
relaxation, indicator addition, recovery experiment or automatic successor.

A technical recovery may only reproduce the identical frozen computation after
a fail-closed implementation or transport incident that produced no valid
economic result. It cannot change any hypothesis field.

Calibration, Evaluation, Candidate v2, PAPER, cloud, real orders and live
execution remain unauthorized.
