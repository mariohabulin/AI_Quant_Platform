# Kraken BTC/ETH/XRP AI-Driven V2 12h Development Economic Evidence Review Protocol V1

## Purpose

This protocol converts the immutable out-of-fold predictions from the completed
12h Development learning run into a bounded economic evidence review. It does
not train, refit, calibrate, rank or promote a model. It never opens the source
archive, Calibration or Evaluation and it never unpickles a model artifact.

The only accepted parent evidence is the completed Recovery Attempt 3 report
with SHA-256
`30d020bd9c30306f3e8931b47c0958fea7e11a33bff3795c3473806ddcaa09cf`.

## Frozen decision rule

For every OOF prediction the estimated net reward is:

`predicted_net_r_floor = 3 * P(TARGET_3R_FIRST) - P(STOP_1R_FIRST)`

`TIMEOUT_NO_BARRIER` contributes zero to this deliberately conservative floor.
An observation is economically eligible only when the value is strictly above
zero. This is the unique V1 threshold. There is no threshold sweep, top-k
selection, per-asset tuning, model comparison tuning or use of realized outcome
to decide eligibility.

## Two views of the same fixed rule

1. The raw view contains every eligible OOF decision.
2. The non-overlapping view processes each model, fold and asset in chronological
   order and admits a new decision only after the previously admitted event has
   ended. This represents at most one open research position per asset and avoids
   treating overlapping 30-day labels as independent trades.

Neither view is a portfolio simulation. Cross-asset capital allocation,
concurrent portfolio risk and mark-to-market drawdown remain unimplemented.

## Frozen Development-interest gates

A model family has Development economic interest only if all conditions pass:

- at least 30 raw eligible observations in every fold;
- at least 10 non-overlapping eligible observations in every fold;
- positive cumulative and mean realized net R in every fold under the
  non-overlapping view;
- positive cumulative realized net R for at least two of BTC, ETH and XRP when
  all folds are combined under the non-overlapping view;
- positive cumulative and mean realized net R overall under the non-overlapping
  view; and
- target-class precision-recall AUC exceeds the observed target prevalence in
  every fold.

These gates were frozen before the economic OOF outcomes were opened. Passing
creates only `DEVELOPMENT_ECONOMIC_INTEREST_REVIEW_REQUIRED`. It does not choose
between model families and does not create or authorize Candidate v2. If no
model passes, the terminal action is `HOLD_CASH`.

## Evidence validation

The review first invokes the independent parent evidence lock. It additionally
requires the exact report hash, canonical prediction JSON, exact class/model/
fold/asset identities, unique prediction keys, finite normalized probabilities,
valid chronological event boundaries, causal training boundaries and finite
realized net R values.

## Safety boundary

- new label generation: false;
- model loading or unpickling: false;
- model training or refitting: false;
- automatic model selection: false;
- Calibration and Evaluation access: false;
- Candidate v2 authorization: false;
- PAPER, cloud, real-order and live authorization: false;
- evidence writes: false.

The review is deterministic and read-only. Its output is a JSON summary printed
to the operator; the locked Attempt 3 evidence remains byte-for-byte unchanged.
