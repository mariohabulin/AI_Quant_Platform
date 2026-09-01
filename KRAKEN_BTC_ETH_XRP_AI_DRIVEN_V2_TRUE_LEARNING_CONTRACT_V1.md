# Kraken BTC/ETH/XRP AI-Driven V2 True Learning Contract V1

## Status and boundary

Protocol ID:
`kraken-btc-eth-xrp-ai-driven-v2-true-learning-contract-v1`

Contract ID:
`kraken-ai-v2-true-learning-contract-v1`

Status:
`KRAKEN_AI_V2_TRUE_LEARNING_CONTRACT_FROZEN_STAGE_2_AUDIT_REQUIRED`

This is the first contract for the actual learning subsystem. It is bound to
Stage 0 commit prefix `70e7bca`, closed Round 2 report SHA-256
`5f9acde53d0e2cf35cd1010d0002222182670d7255bdf44e18715f4902c85a01`
and the scope correction that renamed the existing deterministic stack to Rule
Discovery Foundation.

The model learns parameters; we do not write the decision rules. This contract
does not train a model, generate a label, open a dataset or authorize Candidate
v2.

## What one training example means

One example belongs to one asset and one completed source bar `t`.

1. Every feature must be computable after bar `t` closes using only information
   available at `t` or earlier.
2. A hypothetical research entry occurs at the next observed source-bar open.
3. One risk unit is `1.5 ×` causal ATR-14 measured at the signal timestamp.
4. The label looks forward no more than 30 elapsed UTC days inside one
   continuous provider segment.
5. Modeled entry and exit use the frozen baseline adverse cost profile.

The three-class label is:

- `TARGET_3R_FIRST` when the executable net `+3R` barrier occurs before the
  `-1R` barrier;
- `STOP_1R_FIRST` when the executable `-1R` barrier occurs first; and
- `TIMEOUT_NO_BARRIER` when neither barrier occurs within the frozen horizon.

If both barriers appear inside the same OHLC bar, the stop wins. A gap through a
barrier uses the adverse executable open. A provider gap inside the event or
insufficient right-edge history produces an invalid censored example that must
be counted and reported but never fitted. A timeout exits at the first observed
open at or after the horizon inside the same continuous segment.

The model outputs three probabilities in that exact class order. This preserves
the distinction between an actual loss and a context that simply did not
resolve inside the maximum holding horizon.

## Resolution boundary

Resolution is not selected in Stage 1. Daily is not retained automatically and
six-hour is not selected merely because older strategies used it.

Stage 2 must compare at least two official source-native candidates using only
nonperformance facts: row counts, continuous-segment lengths, known gaps,
feature warm-up loss, horizon censoring and capacity for purged chronological
folds. Returns, expectancy, profit factor, win rate and model score are forbidden
inputs to that choice. Any new source resolution requires a separately locked
dataset before label generation.

## Causal market context

The shared BTC/ETH/XRP learner may use asset identity and these feature groups:

- price returns and momentum;
- trend and market structure;
- volatility and ATR-normalized distance;
- relative volume and liquidity;
- causal support and resistance;
- market-regime context;
- cross-asset context available at the same timestamp; and
- calendar context already known at decision time.

Future OHLCV, centered/forward windows, barrier outcomes, full-sample
preprocessing, Calibration/Evaluation rows, previous route performance and
post-decision P&L are prohibited. Scalers, imputers, feature selection,
probability calibration and decision thresholds must be fitted again inside
each training fold only.

## Bounded learning budget

V1 permits two model families and no more than twelve total variants:

1. a six-variant multinomial logistic-regression baseline; and
2. a six-variant histogram gradient-boosted-tree challenger.

The logistic grid is the cross-product of regularization `C = 0.1, 1.0, 10.0`
and class weight `none, balanced`, with LBFGS and 2,000 maximum iterations. The
tree grid is the cross-product of learning rate `0.03, 0.08` and maximum leaf
nodes `7, 15, 31`, with 300 iterations, minimum leaf size 20, L2 regularization
1.0 and early stopping disabled. No unregistered variant may be substituted.

One deterministic seed, `1729`, is permitted. Unlimited AutoML, unbounded
hyperparameter search, a global performance leaderboard, runtime retraining and
automatic challenger promotion are prohibited. Passing models remain reviewed
artifacts; an operator must explicitly authorize any Candidate v2.

The bounded decision policy tests target-probability thresholds `0.35` through
`0.70` in steps of `0.05` inside each training fold only. Predicted utility is
`3 × P(target) - 1 × P(stop)` and must be at least `0.10R`. The threshold that
maximizes training net expectancy while satisfying the later-frozen Stage 2
support gates is retained; ties choose the higher target threshold. If none
passes, the action is `HOLD_CASH`.

## Development walk-forward contract

Only Development from `2019-01-01T00:00:00Z` inclusive to
`2024-04-01T00:00:00Z` exclusive may train or validate the learner.

The fold plan uses expanding earlier training followed by later validation,
with at least three global timestamp folds across all assets. Each split removes
every training event whose complete label interval overlaps validation, then
uses a 30-day purge and 30-day embargo plus event-uniqueness weighting for
overlapping labels. Validation rows never refit the model instance that
predicted them.
Fold boundaries cannot be selected from performance. Stage 2 must freeze the
exact fold plan before any label generation or training.

Required predictive evidence includes multiclass log loss and target-class
Brier score against fold-local priors, target precision-recall AUC, calibration
error and per-asset/per-regime class support. Economic evidence later uses both
frozen cost profiles and the shared risk envelope. Stage 2 may freeze numeric
support gates from nonperformance counts only, before labels exist. Failure of
any absolute gate produces `HOLD_CASH`; it never opens Calibration.

## Learned model artifact

Every trained variant must create an immutable learned model artifact and
canonical manifest. The evidence must hash model bytes, source code, environment,
dataset manifest, feature schema, label contract, fold plan, training-row
identities, fitted preprocessing, probability calibration, decision policy and
out-of-fold predictions. Rejected variants remain recorded.

Identical inputs inside the frozen environment must reproduce identical
artifact and prediction hashes. Runtime may load an approved immutable artifact
for inference only; it cannot mutate, retrain or self-promote it.

## Claim and authorization boundary

The project may claim a True Learning Engine only after model parameters are
learned from labeled Development examples, predictions are produced on rows not
used to fit that model instance, hashes reproduce, leakage tests pass and a new
challenger can be recreated from immutable feedback.

Calibration and Evaluation remain unopened. Candidate v2 remains unauthorized.
PAPER, cloud, real orders and live execution remain unauthorized. The only next
step is a nonperformance data-sufficiency and resolution audit; it requires its
own implementation and review before any dataset access.
