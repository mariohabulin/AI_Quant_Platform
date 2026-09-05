# LOG

This is the concise active decision log. Detailed historical implementation
notes remain recoverable in Git through commit `8c51695` and in the immutable
protocol/evidence files.

## 2026-09-05 — Dataset Lock Attempt 4 completed; reader recovery bounded
- Attempt 4 at `40b5943` revalidated 695 cached pairs, downloaded 2,113 and
  atomically locked all 2,808 objects plus twelve normalized files in 728.63
  minutes. Manifest SHA-256 is
  `db4dde045d9fce22bee1389fe8c7ad13d3e3ccc5e5c4ace7c433f5461ba11916`.
- Independent review verified all evidence through normalized hashes, then
  failed on valid mixed-precision ISO-8601 timestamps during Pandas frame
  construction. The reader now uses explicit ISO-8601 UTC parsing.
- Acquisition is complete and must not repeat. Next is the same-lock read-only
  review; labels, fitting, later partitions and execution remain closed.

## 2026-09-02 — Derivatives-context Dataset Lock Attempt 1 incident
- Attempt 1 at `970ce17` failed before object 114; no final lock exists and staging is preserved.
- Official BTC metrics retain positive open interest but contain exact blanks in four unused ratio fields.
- Attempt 2 records blanks without fill, keeps learned inputs strict, fingerprints prior staging and uses a new root. No learning or later partition opened.

## 2026-09-02 — Derivatives-context dataset lock and reader implemented
- Bound `af0af86` and 2,808 Development objects to official checksums and raw/member/normalized hashes.
- Added strict schema, chronology, period, grid, atomic manifest and independent no-fallback checks.
- Kept acquisition, values, labels and models closed pending Windows review.

## 2026-09-02 — Derivatives-context hypothesis pre-registered
- Feasibility SHA `3c84fba6034790ae59761f3fba23affca80fca0c8b7d29b3e3f3762c789d8e29` confirms 12 identities, 852 days, full coverage and no duplicates.
- Froze nine causal features, bounded availability, exact 12h basis, warmup and no fill.
- Froze matched control/context pairs, identical rows, three purged folds and fixed gates.
- Kept values, fitting, later partitions and execution closed for the source lock.

## 2026-09-02 — Derivatives-context source feasibility frozen
- Preserved Alpha Research Lab Attempt 1 result SHA-256
  `d76bb013c2124672132868752a5bb350a782eb45ef7f062b78b5edcb6d3b3703`
  and the terminal 12h spot-OHLCV `HOLD_CASH` conclusion.
- Froze exactly four candidate public archive series: funding rate,
  open-interest metrics, native 12h mark price and native 12h index price.
- Limited the first audit to BTCUSDT, ETHUSDT and XRPUSDT object metadata.
- Implemented paginated public-object inventory, common-history calculation,
  per-period gap reporting and atomic JSON evidence output.
- Froze feasibility at all twelve identities, at least 730 common calendar
  days, at least 98% coverage and no duplicate period.
- Kept market values, labels, fitting, tuning, Calibration, Evaluation,
  Candidate v2, PAPER and live execution closed.
- A pass permits only a separately pre-registered derivatives-context learning
  hypothesis; a failure requires another historical source or a stop decision.

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
- The authorized timestamp-only scan found 4,383 native 4h rows per asset but
  only 545 Development rows; no reader defect or hidden earlier history existed.

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

## 2026-09-01 — Alpha Research Lab completed `HOLD_CASH`

- Completed the immutable V1 review: logistic selected 659 non-overlapping
  events for `-378.32 R`; histogram boosting selected 240 for `-82.93 R`.
- Both families had zero positive folds and zero positive assets; V1 action is
  `KRAKEN_AI_V2_12H_DEVELOPMENT_ECONOMIC_REVIEW_HOLD_CASH`.
- Executed all six frozen Alpha Research Lab variants across three folds and
  10,712 labels from commit `3dcfb2e`.
- All six produced negative cumulative and mean non-overlapping net R; every
  positive-asset count was zero and none passed all-fold stability.
- Recorded result SHA-256
  `d76bb013c2124672132868752a5bb350a782eb45ef7f062b78b5edcb6d3b3703`.
- Closed the 12h spot-OHLCV hypothesis with `HOLD_CASH`; there is no seventh
  variant, threshold relaxation or Calibration/Evaluation access.

## Compact historical milestone index
Provider and Historical Availability Audit v1 established fail-closed Kraken acquisition; Sealed Preflight Completed and Supervised Blinded Replay v1 preserved hidden timestamps and no-live boundaries.
AI-Driven v2 Causal Feature Contract preceded AI-Driven v2 State Machine, AI-Driven v2 Risk and Execution, AI-Driven v2 Development/Evaluation Partition, AI-Driven v2 Partition Protocol and AI-Driven v2 Development Runner; Reference A closed 13 rejected entries with `HOLD_CASH`.
Hybrid foundation `kraken-btc-eth-xrp-ai-driven-v2-hybrid-strategy-discovery-learning-v1` preceded both rounds. Round 1 Causal Signals, Round 1 Family Execution, Round 1 Discovery Runner and Round 1 Closure (`kraken-btc-eth-xrp-ai-driven-v2-hybrid-discovery-round-1-v1`) covered four paths/12 routes and retained
`3ce14fda95f657c0b671b74c702d55ec4102da303e9e033ebaf0e02ff5c2fa9b`;
Round 2 Causal Signals, Round 2 Family Execution, Round 2 Discovery Runner and Round 2 Closure (`kraken-btc-eth-xrp-ai-driven-v2-hybrid-discovery-round-2-v1`) covered three paths/7 routes and retained
`5f9acde53d0e2cf35cd1010d0002222182670d7255bdf44e18715f4902c85a01`.
True Learning Contract V1 (`70e7bca`, `796c8de`) separated learning from the
Rule Discovery Foundation; Stage 2 compared 1d, 12h and 4h timestamp-only support without
model training. Legacy wording that the resolution remains unselected is kept.

## Immutable identifiers
IDs cover causal feature, state, risk, partition, Development runner (`kraken-ai-v2-ccvr-reference-a-v1`, `kraken-ai-v2-risk-execution-reference-a-v1`, `kraken-btc-eth-xrp-ai-driven-v2-partition-v1`, `kraken-btc-eth-xrp-ai-driven-v2-development-runner-v1`),
hybrid/Rounds, True Learning Contract, Learning Core and 12h learning/economic
review. Evidence includes `56710a21a423a63963e5c97ab6ca956021f9cd7a7d494c3f29a197068367ff60`,
`f537410d2a237be207951b638518d80e861289dafa7db9b5c2322ffa32d4e594` and
`30d020bd9c30306f3e8931b47c0958fea7e11a33bff3795c3473806ddcaa09cf`.
Reference A status is `KRAKEN_AI_V2_DEVELOPMENT_REFERENCE_A_CLOSED_NO_TRADE_HOLD_CASH`;
fixed terms include `FLAT -> ARMED -> LONG -> FLAT`, Layer/Signal-State/Risk
and Synthetic Execution/Partition boundaries and supervised blinded replay.

Historical compatibility terms: Kraken daily, three-class, no model training, Round 1 Discovery Runner, Round 2 Family Execution, True Learning Engine and
the former statement that the resolution remains unselected.
Legacy exact marker: resolution remains unselected.
Development/Calibration/Evaluation end at `2024-04-01T00:00:00Z`,
`2025-04-01T00:00:00Z` and `2026-04-01T00:00:00Z`.
Candidate v2, PAPER, cloud, real orders and live execution remain unauthorized.
