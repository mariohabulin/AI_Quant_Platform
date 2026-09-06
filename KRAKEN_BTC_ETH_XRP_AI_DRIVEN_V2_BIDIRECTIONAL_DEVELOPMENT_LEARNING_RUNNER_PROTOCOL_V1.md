# Kraken BTC/ETH/XRP AI-Driven V2 Bidirectional Development Learning Runner V1

## Purpose and bindings

Protocol ID:
`kraken-btc-eth-xrp-ai-v2-bidirectional-development-learning-runner-v1`.

This runner implements only the hypothesis frozen at commit `82ea7f1`. It
binds the exact Kraken archive reader and Learning Core, the final derivatives
context Dataset Lock Attempt 4 manifest, the nine-feature context component,
the bidirectional protocol/component/review and the immutable long-only
forensic closure. Any byte change requires a new reviewed runner.

The common Development interval remains 2021-12-01 through 2024-04-01
exclusive. No network download is allowed. The locked Kraken archive and
derivatives dataset are read-only inputs outside the repository.

## Paired outcome table

Each causal decision row has exactly one shared next-open entry and both frozen
directional outcomes:

- LONG buys then sells;
- SHORT sells then buys to cover.

Both use 60 bars, `1.5 × ATR-14`, 3R target, 1R stop, adverse costs,
gap-open execution and stop-first same-bar ambiguity. A decision is retained
only when both directions are valid. Both outcomes must finish before a fold
boundary that trains on or validates the row. No missing context value is
filled. The spot-only control receives the same context-complete decisions as
the context variant.

## Frozen fitting and action

Exactly two variants execute in registered order:

1. `SPOT_ONLY_BIDIRECTIONAL_HIST_GBT_NET_R_CONTROL`;
2. `SPOT_CONTEXT_BIDIRECTIONAL_HIST_GBT_NET_R`.

For each of three expanding, 30-day-purged folds, each variant fits one frozen
histogram-gradient-boosting regressor for LONG net R and one for SHORT net R.
This is exactly twelve model fits. Preprocessing is fold-local. Validation fits
nothing.

The action is the strictly positive larger prediction. A nonpositive maximum
or exact positive LONG/SHORT tie is `HOLD_CASH`. There is no feature, learner,
hyperparameter or threshold sweep and no automatic model selection.

## Economic gates

Each variant must pass all absolute gates on chronological non-overlapping
selected events:

- at least 30 raw and 10 non-overlapping selections in every fold;
- positive mean and cumulative net R in every fold;
- positive cumulative net R on at least two assets;
- positive mean and cumulative net R overall; and
- exact row, direction and event identity validation.

The spot-only control may pass as independent Development evidence. The
context variant must also exceed the matched control in overall mean net R,
worst-fold mean net R and at least two of three fold means. Empty economic
views count as `0.0 R`; ties fail. Passing results request human review only.

## Evidence and safety

The runner atomically records canonical JSON report and OOF predictions,
binary-LF SHA-256 sidecars and twelve real model artifacts in one new external
directory. The independent reader hashes every artifact without unpickling.
Existing final or staging output blocks execution.

Real Development values, labels and fitting require the exact separate phrase:
`EXECUTE_KRAKEN_AI_V2_BIDIRECTIONAL_DEVELOPMENT_LEARNING_ONCE`.

The reviewed implementation remains inert. Calibration, Evaluation, Candidate
v2, PAPER, cloud, real orders and live execution remain unauthorized.
