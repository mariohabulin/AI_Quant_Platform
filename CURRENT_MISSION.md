# CURRENT MISSION

## Mission

Preserve the closed spot-OHLCV result, frozen derivatives-context hypothesis,
three fail-closed attempts and the completed Attempt 4 dataset lock. Correct
the independent reader's mixed-precision ISO-8601 parsing defect, then rerun
only read-only verification against the existing manifest. Do not reacquire
data, generate labels, fit models, open Calibration/Evaluation or promote
Candidate v2.

Status:
`KRAKEN_AI_V2_DERIVATIVES_CONTEXT_MARK_INDEX_ALIGNMENT_RECOVERY_IMPLEMENTATION_REVIEW_REQUIRED`
Attempt 4 execution milestone: `40b5943`
Final manifest SHA-256:
`db4dde045d9fce22bee1389fe8c7ad13d3e3ccc5e5c4ace7c433f5461ba11916`
Hypothesis parent milestone: `af0af86`
Feasibility evidence SHA-256:
`3c84fba6034790ae59761f3fba23affca80fca0c8b7d29b3e3f3762c789d8e29`
Active protocol:
`kraken-btc-eth-xrp-ai-v2-derivatives-context-dataset-lock-reader-v1`

## Implemented dataset lock and reader
The component freezes exactly 2,808 official Binance USD-M archive objects:
84 funding, 2,556 daily open-interest metrics, 84 native 12h mark-price and 84
native 12h index-price ZIPs across BTCUSDT, ETHUSDT and XRPUSDT. Every object
must match its official `.CHECKSUM` and exact schema before it can enter the
lock.
Attempt 1 exposed exact blanks in unused ratio fields. Attempt 2 then reached
object 181 and exposed an official paired `0E-8` open-interest sentinel. Neither
attempt created a final lock, label or model; both non-final staging directories
remain preserved. A complete scan of all 2,556 metrics ZIPs found exactly 399
sentinel rows: the same 133 timestamps for each asset and no negative, blank,
non-finite or other invalid open-interest value.

Attempt 3 stopped on DNS after 695 complete pairs. Attempt 4 revalidated that
prefix, downloaded the remaining 2,113 objects and atomically published all
2,808 objects plus twelve normalized files in 728.63 minutes. Its final lock
exists, staging does not, the prior staging inventories are unchanged and the
399 exact `0E-8` sentinels remain recorded without fill.

The first reader correction made mixed-precision ISO-8601 parsing explicit.
The next read-only review reached a real mark/index alignment gate. A
timestamp-only scan proved index is an exact subset of mark: BTC has 1,680
common and 18 mark-only rows; ETH and XRP each have 1,698 common and two
mark-only rows. All sources are ordered and unique, with zero index-only or
paired close-time mismatch. The bounded fix inner-aligns exact completed bars
and leaves every absent row missing. No fill, locked-byte change or acquisition
rerun is permitted.

## Completed source audit and active hypothesis
The metadata-only audit found all twelve source/asset identities, 852 common
days from 2021-12-01 through 2024-04-01, 100% common period coverage and no
duplicates. It opened no market value and made no profitability claim.

The pre-registered experiment adds exactly nine funding, open-interest and
basis features to the unchanged 16 spot features. Two spot-only controls are
paired with two otherwise identical context models across three purged folds.
All variants use identical context-complete rows. A context variant must pass
the existing support, all-fold, asset-breadth and overall-net-R gates and also
beat its matched control. Controls can never become candidates.

## Completed real learning milestone
The Development Learning Runner Recovery Attempt 3 completed successfully on
locked Kraken native 12h Development data:

- Development interval: 2019-01-01 through 2024-04-01 exclusive;
- labeled rows: 10,712;
- trained artifacts: six, comprising two model families across three folds;
- OOF predictions: 11,856;
- immutable Learning Attempt 3 report SHA-256:
  `30d020bd9c30306f3e8931b47c0958fea7e11a33bff3795c3473806ddcaa09cf`;
- model families: `LOGISTIC_BASELINE` and `HIST_GBT_CHALLENGER`;
- Calibration data opened: false;
- Evaluation data opened: false;
- automatic model selection: false;
- Candidate v2 authorized: false;
- real orders submitted: false.

Attempt 1 and Attempt 2 remain preserved fail-closed incidents. Their empty
staging markers are not deleted or reused. Attempt 3 final evidence is complete
and independently hash-locked.

## Completed V1 economic conclusion

The read-only review of Attempt 3 passed its evidence lock and changed no parent
evidence. Both V1 learners failed every economic stability branch:

- logistic: 659 non-overlapping selections, `-378.32 R`, mean `-0.574 R`;
- histogram boosting: 240 selections, `-82.93 R`, mean `-0.346 R`;
- positive folds: zero; positive assets: zero; action: `HOLD_CASH`.

This result is immutable. It is not reinterpreted, rerun or hidden.

## Frozen Alpha Research Lab

Exactly six variants use the same 16 causal features plus asset identity, 12h
Development rows, cost-aware triple-barrier outcomes and three outer folds:

1. natural multinomial logistic classifier;
2. histogram gradient-boosted classifier;
3. extra-trees classifier;
4. ridge direct-net-R regressor;
5. histogram gradient-boosted direct-net-R regressor; and
6. extra-trees direct-net-R regressor.

Every outer training window has an earlier 75% base-fit region and later 25%
calibration region. Classifiers learn natural-frequency calibrated probabilities;
regressors learn expected net R directly. No validation event fits a model or
calibrator that predicts it.

All six always execute. Fixed viability requires per-fold support, positive
non-overlapping net R in all three folds, positive breadth across at least two
assets and positive overall net R. Ranking is deterministic only among variants
passing every gate. A winner is a Development research result, not Candidate v2.

Attempt 1 executed all six variants across all three folds in 21.44 seconds.
None passed: every overall mean net R was negative, every positive-asset count
was zero and Fold 3 contained at most one losing eligible event. The least
negative result, extra-trees classification, still returned `-34.4499 R` and
mean `-0.2140 R`. Result SHA-256 is
`d76bb013c2124672132868752a5bb350a782eb45ef7f062b78b5edcb6d3b3703`.

## Completion gate
The source audit passed 14 focused and 1,954 total Windows tests, all four
feasibility gates and an immutable external evidence lock. The hypothesis
passed 20 focused and 1,974 total Windows tests and was committed at `af0af86`.
Attempt 4 completed the final lock. The ISO-8601 correction passed 31 focused
and 2,005 total Windows tests at `245db6b`. Exact alignment recovery now needs
Windows reproduction, commit and a same-lock read-only review after passing 33
focused and 2,007 total local tests plus static source binding.

## Next deterministic branches
- current branch: reproduce and commit exact common-bar alignment, then verify
  the existing Attempt 4 lock without network access;
- after that independent pass: separately implement the frozen four-variant
  Development runner;
- schema or causal-alignment failure: fail closed and repair the reader without
  changing the hypothesis.

## Permanent nonauthorization

- model training outside the six-variant Development lab: false;
- derivatives market-value access in this pre-registration: false;
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

Historical evidence: BTC episode `56710a21a423a63963e5c97ab6ca956021f9cd7a7d494c3f29a197068367ff60`; Reference A `f537410d2a237be207951b638518d80e861289dafa7db9b5c2322ffa32d4e594`; Round 1 `3ce14fda95f657c0b671b74c702d55ec4102da303e9e033ebaf0e02ff5c2fa9b`; Round 2 `5f9acde53d0e2cf35cd1010d0002222182670d7255bdf44e18715f4902c85a01`. Partition boundaries: `2024-04-01T00:00:00Z`, `2025-04-01T00:00:00Z`, `2026-04-01T00:00:00Z`.

Reference A closure status is
`KRAKEN_AI_V2_DEVELOPMENT_REFERENCE_A_CLOSED_NO_TRADE_HOLD_CASH`.
Reference A, Round 1 and Round 2 remain historical `HOLD_CASH` evidence, not
learned model candidates.

True Learning Contract V1 began at `70e7bca` and was integrated at `796c8de`.
Stage 2 compared 1d, 12h and 4h with timestamp-only access and no model training.
It defined the three-class boundary.
Legacy exact marker: resolution remains unselected.

Candidate v2 and live execution remain unauthorized.
Compatibility: AI-Driven v2 State Machine; AI-Driven v2 Risk and Execution; AI-Driven v2 Development/Evaluation Partition; AI-Driven v2 Development Runner.
