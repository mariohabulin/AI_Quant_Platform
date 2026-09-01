# LOG

This is the concise active decision log. Detailed historical implementation
notes remain recoverable in Git through commit `8c51695` and in the immutable
protocol/evidence files.

## 2026-09-01 — Learning process correction

- Confirmed that the Rule Discovery Foundation did not implement actual model
  training.
- Retired open-ended manual strategy rounds from the active roadmap.
- Preserved Reference A, Round 1 and Round 2 as immutable `HOLD_CASH` evidence.
- Preserved Stage 2 Attempt 1 report SHA-256
  `ca86d49f1dde1d1a8a1e61f07f4c1e98080ab942ab5c32f89880b387edd867d1`.
- Recorded that prior 9,000-per-asset and 3,000/900-per-fold support thresholds
  were not derived from the actual two-model learning design and are no longer
  active gates.
- Selected Kraken native 12h only for one bounded Development learning-
  feasibility run; this is not a profitability or Candidate claim.

## 2026-09-01 — Timestamp forensic conclusion

- Completed the separately authorized read-only scan of XBTUSD, ETHUSD and
  XRPUSD native 4h timestamp columns.
- Each file contained 4,383 timestamp rows from 2024-01-01 through 2025-12-31.
- Each contained only 545 Development rows, no ordering inversion, no duplicate
  and no hidden Development row after the first partition boundary.
- Concluded that native 4h source history is short; no audit reader bug was
  found and Stage 2 Attempt 1 was not rerun or modified.

## 2026-09-01 — AI-Driven V2 Learning Core

- Added `kraken-btc-eth-xrp-ai-driven-v2-learning-core-v1`.
- Implemented strict 12h Development frame validation.
- Implemented 16 causal market-context features plus asset identity.
- Implemented next-open cost-aware triple-barrier labeling with provider-gap
  and right-edge censoring.
- Implemented three expanding chronological folds with fold-local preprocessing.
- Implemented real parameter fitting for a logistic baseline and constrained
  histogram-gradient-boosting challenger.
- Implemented out-of-fold class probabilities, log loss, Brier score,
  precision-recall AUC, calibration error and model artifact hashes.
- Automatic selection, Candidate promotion and runtime learning remain false.
- Real Development archive access and real model training remain unauthorized.

## 2026-09-01 — 12h Development Learning Runner

- Added the hash-bound Development-only reader for exact native Kraken
  `XBTUSD_720`, `ETHUSD_720` and `XRPUSD_720` members.
- Bound the complete archive, opaque decompressed member bytes, timestamp
  identities, expected rows and missing buckets.
- Extended Learning Core results so actual fitted estimator bytes, not only
  their hashes, can be persisted and independently checked.
- Added atomic canonical report, OOF prediction and six-model evidence output.
- Added pre-fit fold/class support measurement and a terminal insufficient-
  support `HOLD_CASH` package that performs no model fitting.
- Preserved no-selection, no-Calibration, no-Evaluation, no-Candidate and
  no-live boundaries.
- The runner remains inert pending Windows reproduction, commit and a later
  separate one-shot operator authorization.

## 2026-09-01 — Learning Attempt 1 incident and recovery

- Attempt 1 ran from `cc8ae44`, validated the complete archive hash and failed
  on row 1 of `master_q4/XBTUSD_720.csv` before parsing OHLCV values.
- Final evidence remained absent; the empty staging marker remained present and
  correctly blocked a retry. No labels, models or predictions were created.
- Root cause was an eight-column VWAP assumption in the new runner and its
  synthetic fixture. The existing reviewed Kraken parser and protocol already
  froze seven fields: timestamp, OHLC, Volume and Trades.
- Corrected the adapter and fixture to exactly seven fields, added positive
  integer trade-count validation and an eight-column rejection regression.
- Recovery now requires the preserved Attempt 1 staging marker, a new Attempt 2
  evidence root and a new one-shot recovery phrase. Attempt 1 authorization is
  consumed.

## 2026-09-01 — Learning Attempt 2 incident and recovery

- Attempt 2 ran from `203b4c5`, validated the full archive and parsed BTC
  Development rows with the corrected seven-column schema.
- It failed before returning frames because the reader accepted the frozen
  3,833 BTC rows and one missing bucket but also required both interval
  endpoints to exist.
- Final evidence remained absent and Attempt 2 staging remained present. No
  feature, label, fold result, model, OOF prediction or conclusion was created.
- Root cause was a synthetic fixture that placed BTC's missing bucket inside
  the period instead of at the edge recorded by Stage 2.
- Replaced mandatory endpoint presence with full aligned-calendar subtraction,
  exact missing-timestamp evidence and unchanged archive/count validation.
- Attempt 3 requires both prior empty staging markers, a new evidence root and
  a new one-shot authorization. Attempts 1 and 2 are consumed and may not be
  rerun.

## 2026-09-01 — Learning Recovery Attempt 3 completed

- Attempt 3 passed archive, seven-column schema, full-grid missing-timestamp,
  partition and evidence-root checks.
- Generated 10,712 real Development labels.
- Fitted two real model families independently across three folds, producing
  six learned artifacts.
- Recorded 11,856 OOF probability rows and report SHA-256
  `30d020bd9c30306f3e8931b47c0958fea7e11a33bff3795c3473806ddcaa09cf`.
- Independent evidence lock passed; Attempt 1 and Attempt 2 empty staging
  markers remained unchanged.
- No Calibration, Evaluation, Candidate, PAPER, cloud, real-order or live
  boundary was opened.

## 2026-09-01 — Development economic-review contract

- Added a read-only consumer of exact Attempt 3 OOF evidence.
- Froze one untuned interest rule:
  `3 * P(TARGET_3R_FIRST) - P(STOP_1R_FIRST) > 0`.
- Added raw and chronological non-overlapping views; the latter permits at most
  one active event per asset.
- Froze minimum support, all-three-fold positive net R, two-asset breadth and
  all-fold positive target PR-AUC-lift gates.
- Prohibited threshold search, model refit, artifact unpickling, automatic
  model selection and Candidate promotion.
- A pass requests operator review only; otherwise the action is `HOLD_CASH`.

## 2026-09-01 — V1 result and frozen final Development loop

- Completed the immutable V1 review: logistic selected 659 non-overlapping
  events for `-378.32 R`; histogram boosting selected 240 for `-82.93 R`.
- Both families had zero positive folds and zero positive assets; V1 action is
  `KRAKEN_AI_V2_12H_DEVELOPMENT_ECONOMIC_REVIEW_HOLD_CASH`.
- Froze `kraken-btc-eth-xrp-ai-driven-v2-alpha-research-lab-v1` as the only
  remaining Development experiment.
- Registered exactly six variants: three natural-frequency calibrated
  classifiers and three direct expected-net-R regressors.
- Froze 12h, the existing features, labels, costs, outer folds, inner 75/25
  chronology, zero threshold and economic gates before real execution.
- Prohibited a seventh variant, threshold/hyperparameter sweep, automatic
  Candidate promotion and Calibration/Evaluation access.
- Frozen exit: one Development winner for separate review, or terminal
  `HOLD_CASH` for the 12h OHLCV hypothesis.

## Compact historical milestone index

- Provider and Historical Availability Audit v1 established Venue-Bound Crypto
  Evidence and fail-closed Kraken daily acquisition.
- Sealed Preflight Completed with `KRAKEN_BLINDED_REPLAY_PREFLIGHT_PASS`;
  selected timestamps remained hidden and one-episode-at-a-time review required
  an explicit decision.
- Supervised Blinded Replay v1 preserved the no-live boundary.
- AI-Driven v2 Causal Feature Contract preceded AI-Driven v2 State Machine.
- AI-Driven v2 Risk and Execution preceded AI-Driven v2 Partition Protocol.
- AI-Driven v2 Development Runner and Development-Only Evidence Runner closed
  Reference A with 13 rejected entries and `HOLD_CASH`; it was not a break-even
  strategy result.
- Round 1 Causal Signals implemented four paths; Round 1 Family Execution and
  Round 1 Discovery Runner covered 12 routes; Round 1 Closure retained
  `3ce14fda95f657c0b671b74c702d55ec4102da303e9e033ebaf0e02ff5c2fa9b`.
- Round 2 Causal Signals implemented three paths; Round 2 Family Execution and
  Round 2 Discovery Runner covered 7 routes; Round 2 Closure retained
  `5f9acde53d0e2cf35cd1010d0002222182670d7255bdf44e18715f4902c85a01`.
- The Rule Discovery Foundation is not the True Learning Engine.
- True Learning Contract V1 began at `70e7bca`, was integrated at `796c8de`,
  defined a three-class learner and initially recorded that the resolution
  remains unselected.
- Stage 2 compared 1d, 12h and 4h using timestamp-only access and no model
  training.

## Immutable identifiers

- `kraken-btc-eth-xrp-ai-driven-v2-causal-feature-contract-v1`
- `kraken-ai-v2-ccvr-reference-a-v1`
- `kraken-ai-v2-risk-execution-reference-a-v1`
- `kraken-btc-eth-xrp-ai-driven-v2-partition-v1`
- `kraken-btc-eth-xrp-ai-driven-v2-development-runner-v1`
- `kraken-btc-eth-xrp-ai-driven-v2-hybrid-strategy-discovery-learning-v1`
- `kraken-btc-eth-xrp-ai-driven-v2-hybrid-discovery-round-1-v1`
- `kraken-btc-eth-xrp-ai-driven-v2-hybrid-discovery-round-2-v1`
- `kraken-btc-eth-xrp-ai-driven-v2-true-learning-contract-v1`
- `kraken-btc-eth-xrp-ai-driven-v2-learning-core-v1`
- `kraken-btc-eth-xrp-ai-driven-v2-12h-development-learning-runner-v1`
- `kraken-btc-eth-xrp-ai-driven-v2-12h-development-economic-evidence-review-v1`
- `56710a21a423a63963e5c97ab6ca956021f9cd7a7d494c3f29a197068367ff60`
- `f537410d2a237be207951b638518d80e861289dafa7db9b5c2322ffa32d4e594`
- `30d020bd9c30306f3e8931b47c0958fea7e11a33bff3795c3473806ddcaa09cf`

Reference A closure status:
`KRAKEN_AI_V2_DEVELOPMENT_REFERENCE_A_CLOSED_NO_TRADE_HOLD_CASH`.

Historical fixed boundary terms: `FLAT -> ARMED -> LONG -> FLAT`, AI-Driven v2
Layer Boundary, AI-Driven v2 Signal-State Layer, AI-Driven v2 Risk and Synthetic
Execution Layer, AI-Driven v2 Partition Boundary, Kraken Bounded Blinded Replay
Review Boundary v1 and Supervised Blinded Replay Execution Boundary v1.

Historical compatibility terms: Kraken daily, three-class, no model training,
Round 1 Discovery Runner, Round 2 Family Execution, True Learning Engine and
the former statement that the resolution remains unselected.
Legacy exact marker: resolution remains unselected.

Development ends at `2024-04-01T00:00:00Z`, Calibration ends at
`2025-04-01T00:00:00Z`, and Evaluation ends at `2026-04-01T00:00:00Z`.
Candidate v2, PAPER, cloud, real orders and live execution remain unauthorized.
