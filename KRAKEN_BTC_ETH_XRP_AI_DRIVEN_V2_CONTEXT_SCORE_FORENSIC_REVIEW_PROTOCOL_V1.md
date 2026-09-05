# Kraken BTC/ETH/XRP AI-Driven V2 Context Score Forensic Review V1

## Purpose and immutable input

Protocol ID: `kraken-btc-eth-xrp-ai-v2-context-score-forensic-review-v1`.

This review diagnoses why both derivatives-context models selected zero rows in
Development Learning Attempt 1. It reads only the independently verified final
evidence whose report SHA-256 is
`bddb6f7c0a9b056dcf8a4ca79fc3b8128dbf4ded4aac47e19022a84222215fb4`.
It first invokes the existing independent reader, verifies every model byte
without unpickling, and then parses only canonical report and out-of-fold
prediction JSON.

## Frozen diagnostics

For each of the four registered variants the review reports:

- score count, range, mean and fixed 1/5/10/25/50/75/90/95/99 percentiles;
- the score/outcome Spearman association overall, by fold and by asset;
- deterministic equal-count score deciles with raw and per-asset
  non-overlapping net-R summaries;
- top-decile results overall and separately in every outer fold;
- class support by fold; and
- event-duration summaries overall and by realized label.

Rows are ordered by score, decision timestamp, asset and fold before assigning
deciles. Matched context/control pairs must have identical row identities,
labels and outcomes. Any mismatch fails closed.

The artifact contains net outcomes only. Gross return, commission, spread and
slippage cannot be decomposed and the review must state that limitation.

## Decision boundary

This is diagnostic evidence, not a threshold search. It does not simulate a
new threshold, choose top-k trades, refit or unpickle a model, generate a label,
modify the evidence directory, or select Experiment 2 automatically.

The interpretation is deliberately limited to measured ranking shape and
stability. A human review decides whether one separately pre-registered
Experiment 2 is justified. If score rank is not stable and economically
positive across folds, the derivatives-context hypothesis closes.

## Safety

Implementation and static review open no evidence. The eventual external run
is read-only and needs no market-data download. Calibration, Evaluation,
Candidate v2, PAPER, cloud, real orders and live execution remain unauthorized.
