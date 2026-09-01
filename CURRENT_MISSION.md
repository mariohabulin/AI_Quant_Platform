# CURRENT MISSION

## Mission

Perform one deterministic, read-only economic review of the immutable 12h
Development out-of-fold evidence created by successful Learning Recovery
Attempt 3. Do not retrain, tune a decision threshold, choose a model or promote
Candidate v2.

Status:
`KRAKEN_AI_V2_12H_DEVELOPMENT_ECONOMIC_REVIEW_IMPLEMENTATION_IN_REVIEW`

Parent milestone: `9c1156e`

Parent evidence SHA-256:
`30d020bd9c30306f3e8931b47c0958fea7e11a33bff3795c3473806ddcaa09cf`

Active protocol:
`kraken-btc-eth-xrp-ai-driven-v2-12h-development-economic-evidence-review-v1`

## Completed real learning milestone

The Development Learning Runner Recovery Attempt 3 completed successfully on
locked Kraken native 12h Development data:

- Development interval: 2019-01-01 through 2024-04-01 exclusive;
- labeled rows: 10,712;
- trained artifacts: six, comprising two model families across three folds;
- OOF predictions: 11,856;
- model families: `LOGISTIC_BASELINE` and `HIST_GBT_CHALLENGER`;
- Calibration data opened: false;
- Evaluation data opened: false;
- automatic model selection: false;
- Candidate v2 authorized: false;
- real orders submitted: false.

Attempt 1 and Attempt 2 remain preserved fail-closed incidents. Their empty
staging markers are not deleted or reused. Attempt 3 final evidence is complete
and independently hash-locked.

## Current implementation

The economic review:

1. locks the exact Attempt 3 evidence directory;
2. reads only canonical OOF prediction JSON and the parent report;
3. never opens the Kraken archive or unpickles a learned model;
4. applies the sole frozen rule
   `3 * P(TARGET_3R_FIRST) - P(STOP_1R_FIRST) > 0`;
5. reports raw eligible observations and a chronological non-overlapping view
   with at most one open event per asset;
6. requires sufficient support, positive net R in every fold, breadth across
   at least two assets and positive target PR-AUC lift in every fold; and
7. returns either operator review of Development interest or `HOLD_CASH`.

There is no threshold sweep, top-k search, Calibration access, Evaluation
access, automatic winner or Candidate authorization. The result is not yet a
portfolio backtest because cross-asset capital, simultaneous portfolio risk and
mark-to-market drawdown are not modeled in this review.

## Completion gate

1. focused economic-review tests pass;
2. complete regression passes;
3. parent runner, new protocol and new component hashes match;
4. Windows reproduces tests and the inert static review;
5. commit/push occurs from a reviewed worktree;
6. a read-only command is run on the locked Attempt 3 evidence; and
7. the evidence directory is proven byte-for-byte unchanged afterward.

The read-only evidence review needs no model-training authorization. It does not
write a new evidence package. Any later Candidate freeze remains a separate
operator decision.

## Possible terminal branches

- no model passes every frozen gate: close 12h V1 with `HOLD_CASH`;
- one or both model families pass: inspect the named family evidence without
  automatically selecting it, then separately decide whether a frozen
  Development candidate specification is justified.

## Permanent nonauthorization

- new model training: false;
- threshold or parameter search: false;
- automatic model selection: false;
- Calibration data access: false;
- Evaluation data access: false;
- Candidate v2 authorization: false;
- PAPER, cloud, real orders and live execution: false.

## Historical state

Git history through `8c51695` preserves Provider, Partition, Reference A, Round
1, Round 2, scope correction and Stage 2 work. Manual strategy-family discovery
is retired. Learning Core committed at `2a09363`; the first Development Learning
Runner at `cc8ae44`; recoveries at `203b4c5` and `9c1156e`.

Exact historical compatibility markers retained for regression:

- fail-closed Kraken daily acquisition;
- `SEALED PREFLIGHT PASS` and `SUPERVISED REPLAY PREPARATION`;
- `AI-DRIVEN V2 CAUSAL FEATURE CONTRACT`;
- `STATE MACHINE IMPLEMENTED`;
- `RISK AND EXECUTION ADAPTER IMPLEMENTED`;
- `PARTITION PROTOCOL FROZEN`;
- `DEVELOPMENT RUNNER IMPLEMENTED`;
- Round 1 Causal Signals, Round 1 Family Execution, Round 1 Discovery Runner
  and Round 1 Closure used four paths and 12 routes;
- Round 2 Causal Signals, Round 2 Family Execution, Round 2 Discovery Runner
  and Round 2 Closure used three paths and 7 routes; and
- Rule Discovery Foundation and True Learning Engine.

Historical protocol identifiers:

- `kraken-btc-eth-xrp-ai-driven-v2-causal-feature-contract-v1`;
- `kraken-ai-v2-ccvr-reference-a-v1`;
- `kraken-ai-v2-risk-execution-reference-a-v1`;
- `kraken-btc-eth-xrp-ai-driven-v2-partition-v1`;
- `kraken-btc-eth-xrp-ai-driven-v2-development-runner-v1`;
- `kraken-btc-eth-xrp-ai-driven-v2-hybrid-strategy-discovery-learning-v1`;
- `kraken-btc-eth-xrp-ai-driven-v2-hybrid-discovery-round-1-v1`;
- `kraken-btc-eth-xrp-ai-driven-v2-hybrid-discovery-round-2-v1`; and
- `kraken-btc-eth-xrp-ai-driven-v2-true-learning-contract-v1`.

Historical evidence and partition values:

- BTC episode `56710a21a423a63963e5c97ab6ca956021f9cd7a7d494c3f29a197068367ff60`;
- Reference A `f537410d2a237be207951b638518d80e861289dafa7db9b5c2322ffa32d4e594`;
- Round 1 report `3ce14fda95f657c0b671b74c702d55ec4102da303e9e033ebaf0e02ff5c2fa9b`;
- Round 2 report `5f9acde53d0e2cf35cd1010d0002222182670d7255bdf44e18715f4902c85a01`;
- Development, Calibration and Evaluation boundaries:
  `2024-04-01T00:00:00Z`, `2025-04-01T00:00:00Z`, `2026-04-01T00:00:00Z`.

Reference A closure status is
`KRAKEN_AI_V2_DEVELOPMENT_REFERENCE_A_CLOSED_NO_TRADE_HOLD_CASH`.
Reference A, Round 1 and Round 2 remain historical `HOLD_CASH` evidence, not
learned model candidates.

True Learning Contract V1 began at `70e7bca` and was integrated at `796c8de`.
Stage 2 compared 1d, 12h and 4h with timestamp-only access and no model training.
It defined the three-class boundary.
Legacy exact marker: resolution remains unselected.

Candidate v2 and live execution remain unauthorized.
