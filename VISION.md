# VISION

## Product

AI Quant Platform must become a deterministic AI-driven research agent that
learns when a cost-aware BTC, ETH or XRP trade has positive evidence and when
the correct action is `HOLD_CASH`.

The product is not a collection of manually written indicator strategies. Its
versioned model learns from causal context, predicts unseen later data and is
reproducible from locked inputs.

## What success means

A successful V2 system must:

- learn from Development labels instead of receiving entry rules from us;
- keep all features causal at the completed-bar decision timestamp;
- predict `TARGET_3R_FIRST`, `STOP_1R_FIRST` and `TIMEOUT_NO_BARRIER`;
- validate with expanding walk-forward predictions never used for fitting;
- include adverse costs, risk limits and the valid `HOLD_CASH` action;
- remain stable across time, BTC, ETH, XRP and market regimes;
- preserve Calibration and Evaluation until their explicit later gates; and
- create an immutable learned model artifact before runtime inference.

No process can guarantee alpha. The system must test repeatable after-cost
evidence honestly; a negative result prevents unjustified deployment.

## Active V2 path

The active feasibility resolution is Kraken native 12h over Development
`2019-01-01T00:00:00Z` through `2024-04-01T00:00:00Z` exclusive. This is a data-
support choice, not a profitability claim.

The Learning Core now implements:

1. causal multi-asset features;
2. next-open cost-aware triple-barrier labels;
3. three expanding purged walk-forward folds;
4. a regularized multinomial logistic baseline;
5. one constrained histogram-gradient-boosting challenger; and
6. immutable probability, metric and model-hash evidence.

The hash-bound real 12h Development Learning Runner is implemented. Attempt 1
failed closed before learning because its new synthetic fixture assumed an
eighth VWAP field that the frozen seven-column Kraken archive does not contain.
Attempt 2 corrected that defect but failed before learning because the fixture
did not reproduce BTC's known missing edge bucket: the reader accepted the
frozen missing count and then incorrectly required that endpoint. The archive
and Learning Core were not at fault in either incident. Recovery now validates
the full grid and records missing timestamps without weakening archive hashes
or counts. Recovery Attempt 3 then completed successfully with 10,712 labeled
rows, six real fold-model artifacts and 11,856 exact OOF predictions. Its report
SHA-256 is
`30d020bd9c30306f3e8931b47c0958fea7e11a33bff3795c3473806ddcaa09cf`.
No model was automatically selected and Calibration and Evaluation remained
unopened.

The read-only V1 economic review is complete. Neither learned family produced
positive net R in any outer fold or on any asset. Logistic regression selected
659 non-overlapping events for `-378.32 R`; histogram boosting selected 240 for
`-82.93 R`. V1 is therefore frozen as
`KRAKEN_AI_V2_12H_DEVELOPMENT_ECONOMIC_REVIEW_HOLD_CASH`.

Alpha Research Lab Attempt 1 then executed all six frozen learners across three
folds and 10,712 labels. Every variant lost net R, every asset breadth count was
zero and the latest fold produced at most one losing eligible event. Result SHA
`d76bb013c2124672132868752a5bb350a782eb45ef7f062b78b5edcb6d3b3703`
closes the 12h spot-OHLCV hypothesis with `HOLD_CASH`. There is no seventh
variant or automatic process change. Continuation requires a separately frozen
hypothesis containing materially new information, not more fitting of the same
representation.

The derivatives-context feasibility audit passed all four source gates. It
found 852 common calendar days from 2021-12-01 through 2024-04-01 exclusive,
100% expected period coverage and no duplicates across funding, open interest
and both basis legs for all three assets. Report SHA-256 is
`3c84fba6034790ae59761f3fba23affca80fca0c8b7d29b3e3f3762c789d8e29`.

The next hypothesis was pre-registered at `af0af86` before any value access. It compares
two matched spot-only controls with two otherwise identical models receiving
nine causal derivatives-context features. Same-row ablation, three purged
walk-forward folds and fixed absolute plus incremental economic gates must show
that any improvement comes from new information rather than another learner or
an easier sample.

The hash-bound context lock and reader was committed at `970ce17`. Attempt 1
failed on exact blanks in unused Binance ratio columns. Attempt 2, committed at
`8181d05`, accepted those blanks but failed at object 181 on an official paired
`0E-8` open-interest sentinel. No final lock, label or model was created, and
both staging directories are preserved.

A complete content scan of all 2,556 metrics archives found exactly 399 paired
sentinels at the same 133 timestamps for each asset, with no negative, blank,
non-finite or alternate invalid open-interest values. Attempt 3 passed this
bounded correction, then a DNS outage stopped acquisition at object 696. Its
695 complete pairs are preserved, but no final lock exists.

Attempt 4 revalidated the exact Attempt 3 prefix, downloaded the remaining
2,113 objects and atomically completed the 2,808-object lock. Manifest SHA-256
is `db4dde045d9fce22bee1389fe8c7ad13d3e3ccc5e5c4ace7c433f5461ba11916`;
all three earlier staging directories remain immutable.

The first reader recovery made mixed-precision ISO-8601 UTC parsing explicit.
The next review proved index timestamps are exact mark subsets: 18 BTC and two
ETH/XRP mark-only bars, with no opposite, duplicate or close-time mismatch.
Exact common-bar alignment leaves missing context missing. The final immutable
read-only review passed at `9b23d05`; acquisition is closed.

The runner committed at `4e3867d` trained twelve models on 3,793 rows and wrote
8,468 OOF predictions. Report SHA `bddb6f7c0a9b056dcf8a4ca79fc3b8128dbf4ded4aac47e19022a84222215fb4`
passed review. Both context models selected zero trades; beating losing controls
incrementally did not pass absolute gates. Result: `HOLD_CASH`, no candidate.

The active forensic asks whether OOF scores rank net outcomes consistently by
decile, fold and asset. It cannot fit, sweep thresholds, open later partitions
or choose Experiment 2. Evidence permits one frozen experiment or closure.

## Permanent safety boundary

- Development may train and validate.
- Calibration may only confirm a frozen Development candidate.
- Evaluation is a sealed one-time evaluation and remains untouched.
- PAPER and live execution require later, separate authorization.
- Runtime may load an approved immutable model but may not retrain itself.
- Real orders are never an implicit consequence of a research result.

## Preserved foundations
These components remain useful even though manual strategy discovery is
retired from the active path:

- Venue-Bound Crypto Evidence and fail-closed Kraken archive locking;
- opaque byte hashing and independent evidence verification;
- AI-Driven v2 Layer Boundary and AI-DRIVEN V2 CAUSAL FEATURE CONTRACT;
- AI-Driven v2 State Machine (`FLAT -> ARMED -> LONG -> FLAT`);
- AI-Driven v2 Risk and Execution;
- AI-Driven v2 Development/Evaluation Partition;
- Development-Only Evidence Runner;
- supervised and one-episode-at-a-time blinded replay controls; and
- Rule Discovery Foundation evidence from Reference A, Round 1 and Round 2.

Selected timestamps were protected during blinded review; fabricated rows were
prohibited, and sealed review was not a performance result.
The supervised boundary exposed one asset episode at a time.
Historical compatibility terms: selected timestamps, Kraken daily,
three-class, no model training, Round 1 Discovery Runner, Round 2 Family
Execution, True Learning Engine and the former statement that the resolution
remains unselected.
Legacy exact marker: resolution remains unselected.

## Historical evidence index

Detailed append-only history remains recoverable in Git through parent commit
`8c51695`. The active documents keep only this compact immutable lineage:

- provider dataset: `kraken-spot-btc-eth-xrp-native-1d-20190101-20260401-archive-only-v2`;
- partition/features/state/risk: `kraken-btc-eth-xrp-ai-driven-v2-partition-v1`,
  `kraken-btc-eth-xrp-ai-driven-v2-causal-feature-contract-v1`,
  `kraken-ai-v2-ccvr-reference-a-v1`, `kraken-ai-v2-risk-execution-reference-a-v1`;
- Development runner: `kraken-btc-eth-xrp-ai-driven-v2-development-runner-v1`;
- hybrid foundation: `kraken-btc-eth-xrp-ai-driven-v2-hybrid-strategy-discovery-learning-v1`;
- Round 1: `kraken-btc-eth-xrp-ai-driven-v2-hybrid-discovery-round-1-v1`;
- Round 2: `kraken-btc-eth-xrp-ai-driven-v2-hybrid-discovery-round-2-v1`;
- True Learning Contract V1: `kraken-btc-eth-xrp-ai-driven-v2-true-learning-contract-v1` at `70e7bca` and `796c8de`;
- Stage 2 compared 1d, 12h and 4h with a timestamp-only reader and no model training;
- Learning Core: `kraken-btc-eth-xrp-ai-driven-v2-learning-core-v1`.
- 12h learner/review: `kraken-btc-eth-xrp-ai-driven-v2-12h-development-learning-runner-v1` and its economic evidence review.
- frozen Alpha Research Lab: `kraken-btc-eth-xrp-ai-driven-v2-alpha-research-lab-v1`.
- derivatives-context feasibility: `kraken-btc-eth-xrp-ai-v2-derivatives-context-feasibility-v1`.
- derivatives-context learning hypothesis:
  `kraken-btc-eth-xrp-ai-v2-derivatives-context-learning-hypothesis-v1`.
- derivatives-context dataset lock and reader:
  `kraken-btc-eth-xrp-ai-v2-derivatives-context-dataset-lock-reader-v1`.

Immutable hashes retained for traceability:

- blinded BTC episode: `56710a21a423a63963e5c97ab6ca956021f9cd7a7d494c3f29a197068367ff60`;
- Reference A report: `f537410d2a237be207951b638518d80e861289dafa7db9b5c2322ffa32d4e594`;
- Round 1 report: `3ce14fda95f657c0b671b74c702d55ec4102da303e9e033ebaf0e02ff5c2fa9b`;
- Round 2 report: `5f9acde53d0e2cf35cd1010d0002222182670d7255bdf44e18715f4902c85a01`;
- Stage 2 report: `ca86d49f1dde1d1a8a1e61f07f4c1e98080ab942ab5c32f89880b387edd867d1`.
- 12h Learning Attempt 3 report:
  `30d020bd9c30306f3e8931b47c0958fea7e11a33bff3795c3473806ddcaa09cf`.

Reference A closure status:
`KRAKEN_AI_V2_DEVELOPMENT_REFERENCE_A_CLOSED_NO_TRADE_HOLD_CASH`.
Partition boundaries: `2024-04-01T00:00:00Z`, `2025-04-01T00:00:00Z`, `2026-04-01T00:00:00Z`.

Historical Round 1 Causal Signals, Round 1 Family Execution, Round 1 Discovery
Runner, Round 1 Closure, Round 2 Causal Signals, Round 2 Family Execution,
Round 2 Discovery Runner and Round 2 Closure remain immutable evidence. The
former four-path and later three-path results do not constitute learned alpha.

## Current authorization

Candidate v2: not authorized. Calibration: unopened. Evaluation: unopened.
PAPER, cloud, real orders and live execution: not authorized.
