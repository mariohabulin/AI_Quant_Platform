# Kraken BTC/ETH/XRP AI-Driven V2 Learning Core Protocol V1

## Purpose

Protocol ID: `kraken-btc-eth-xrp-ai-driven-v2-learning-core-v1`

This protocol replaces the active rule-discovery loop with an executable
supervised-learning path. The model must learn parameters from labeled
Development examples. A manually written indicator route is not an AI model and
cannot satisfy this milestone.

The current milestone implements the reusable Learning Core. It does not open
the real archive and does not authorize a real Development training run.

## Why the process changed

Round 1 and Round 2 are retained as immutable historical evidence. They tested
predefined deterministic routes and produced `HOLD_CASH`; they did not train a
model.

Stage 2 Attempt 1 report SHA-256
`ca86d49f1dde1d1a8a1e61f07f4c1e98080ab942ab5c32f89880b387edd867d1`
showed that:

- native 1d contained about 1,673 to 1,796 valid examples per asset;
- native 12h contained about 3,348 to 3,593 valid examples per asset; and
- native 4h contained only 545 Development rows per asset.

The separately authorized timestamp forensic scan confirmed that each native
4h member begins at `2024-01-01T00:00:00Z`, is chronologically ordered, has no
duplicate timestamps and contains no hidden Development rows after the first
partition boundary. The audit reader was not responsible for the short 4h
history.

The previous requirement of 9,000 valid examples **per asset** and 3,000/900
examples **per asset in every fold** is retired from the active learning path.
It remains historical evidence of Stage 2 Attempt 1 and is not silently edited.
Those thresholds were not derived from the actual two-model Learning Core and
made 1d and 12h incapable of passing before class labels were known.

## Active feasibility resolution

The active Development-feasibility resolution is native Kraken `12h`.

This choice does not claim that 12h is profitable or optimal. It means only
that 12h provides the best currently verified balance of multi-year coverage
and example count without inventing candles or lowering a performance gate.
Native 4h remains eligible for a future version if a separately locked longer
source becomes available.

The real 12h dataset must still be hash-bound before the first authorized run.
Calibration and Evaluation must remain unopened.

## One learning example

For each asset and completed 12h bar `t`:

1. every feature uses bar `t` or earlier;
2. the hypothetical entry occurs at the next 12h open;
3. one risk unit equals `1.5 × ATR-14` known at `t`;
4. adverse baseline costs apply on entry and exit;
5. the future path ends after at most 30 UTC days; and
6. a provider gap or unavailable future horizon invalidates the example.

The exact classes are:

1. `TARGET_3R_FIRST`;
2. `STOP_1R_FIRST`; and
3. `TIMEOUT_NO_BARRIER`.

If target and stop are touched in one bar, stop wins. A barrier gap uses the
adverse executable open. A timeout exits at the first open at the horizon.

## Causal feature schema

The frozen V1 schema contains only market facts available at decision time:

- 1, 2, 6 and 14-bar returns;
- ATR fraction and 14-bar realized volatility;
- distance from EMA-12, EMA-48 and EMA-180;
- EMA-12/EMA-48 spread;
- 20-bar relative volume;
- distance from prior 20-bar high and low;
- RSI-14;
- same-timestamp three-asset market return; and
- same-timestamp BTC return plus asset identity.

Every rolling feature is backward-looking. The prior high and low explicitly
exclude the current bar. Future prices, outcomes, P&L, route results,
Calibration and Evaluation are prohibited features.

## Bounded model set

V1 implements exactly two learners:

1. `LOGISTIC_BASELINE` — regularized multinomial logistic regression;
2. `HIST_GBT_CHALLENGER` — one constrained histogram gradient-boosted tree.

Both learn their parameters from labels. Preprocessing is fitted again inside
each training fold. The seed is fixed at `1729`. There is no twelve-variant
grid, AutoML, automatic ranking, automatic promotion or runtime learning.

The two models are compared descriptively. An operator must review their
out-of-fold evidence before any later Candidate decision.

## Walk-forward boundary

Only Development from `2019-01-01T00:00:00Z` inclusive to
`2024-04-01T00:00:00Z` exclusive may participate.

Three expanding folds retain the already calendar-selected boundaries:

| Fold | Training end exclusive | Validation interval |
|---|---|---|
| FOLD_1 | 2021-03-02 | 2021-04-01 to 2022-04-01 exclusive |
| FOLD_2 | 2022-04-01 | 2022-05-01 to 2023-05-01 exclusive |
| FOLD_3 | 2023-05-01 | 2023-05-31 to 2024-04-01 exclusive |

An event must finish before the relevant training or validation boundary. No
validation row may fit the model instance that predicts it. Fold-local class
support is measured after labels exist; missing class support fails closed and
is reported instead of being repaired by changing dates.

## Required evidence from the first real run

The runner must record, for every fold and model:

- training and validation rows and class counts;
- multiclass log loss;
- target-class Brier score and precision-recall AUC;
- calibration error;
- immutable model-artifact SHA-256;
- out-of-fold probabilities and their row identities;
- per-asset and per-regime results;
- baseline and stress cost outcomes under the shared risk envelope; and
- every abstention and `HOLD_CASH` decision.

No single metric automatically chooses a winner. The result must answer whether
the signal is stable across later unseen Development periods, assets, regimes
and adverse costs.

## Stop rules

The next real Development run has exactly three possible conclusions:

- stable evidence: prepare a separately reviewed Calibration candidate;
- weak or unstable evidence: permit one versioned feature/label/source
  correction with an explicit reason; or
- no useful evidence: close this learning hypothesis and keep `HOLD_CASH`.

It does not trigger another open-ended manual strategy round.

## Current authorization state

- Learning Core implemented: `true`
- real Development archive opened: `false`
- real labels generated: `false`
- real model trained: `false`
- Calibration opened: `false`
- Evaluation opened: `false`
- Candidate v2 authorized: `false`
- PAPER or live execution authorized: `false`

The next milestone is a hash-bound 12h Development Learning Runner. Its real run
requires a separate explicit operator authorization after implementation,
tests, review, commit and clean-worktree preflight.
