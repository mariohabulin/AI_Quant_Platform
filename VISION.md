# VISION

## Product

AI Quant Platform must become a deterministic AI-driven research agent that
learns when a cost-aware BTC, ETH or XRP trade has positive evidence and when
the correct action is `HOLD_CASH`.

The product is not a collection of manually written indicator strategies. Its
core output is a versioned model that learns parameters from causal market
context, produces probabilities on unseen later data and can be reproduced
from locked inputs.

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

No process can guarantee alpha. This system must determine honestly whether a
bounded hypothesis contains repeatable evidence after costs. A negative result
is useful when it stops capital from being deployed.

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
or counts. It awaits independent review and a separate Attempt 3 authorization.
A successful recovery will create six real fold-model artifacts and exact OOF
probabilities; insufficient class support will close atomically as `HOLD_CASH`.
Another open-ended rule-discovery round is not part of the active roadmap.

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
- partition: `kraken-btc-eth-xrp-ai-driven-v2-partition-v1`;
- causal features: `kraken-btc-eth-xrp-ai-driven-v2-causal-feature-contract-v1`;
- state parameters: `kraken-ai-v2-ccvr-reference-a-v1`;
- risk policy: `kraken-ai-v2-risk-execution-reference-a-v1`;
- Development runner: `kraken-btc-eth-xrp-ai-driven-v2-development-runner-v1`;
- hybrid foundation: `kraken-btc-eth-xrp-ai-driven-v2-hybrid-strategy-discovery-learning-v1`;
- Round 1: `kraken-btc-eth-xrp-ai-driven-v2-hybrid-discovery-round-1-v1`;
- Round 2: `kraken-btc-eth-xrp-ai-driven-v2-hybrid-discovery-round-2-v1`;
- True Learning Contract V1: `kraken-btc-eth-xrp-ai-driven-v2-true-learning-contract-v1` at `70e7bca` and `796c8de`;
- Stage 2 compared 1d, 12h and 4h with a timestamp-only reader and no model training;
- Learning Core: `kraken-btc-eth-xrp-ai-driven-v2-learning-core-v1`.
- 12h Development learner:
  `kraken-btc-eth-xrp-ai-driven-v2-12h-development-learning-runner-v1`.

Immutable hashes retained for traceability:

- blinded BTC episode: `56710a21a423a63963e5c97ab6ca956021f9cd7a7d494c3f29a197068367ff60`;
- Reference A report: `f537410d2a237be207951b638518d80e861289dafa7db9b5c2322ffa32d4e594`;
- Round 1 report: `3ce14fda95f657c0b671b74c702d55ec4102da303e9e033ebaf0e02ff5c2fa9b`;
- Round 2 report: `5f9acde53d0e2cf35cd1010d0002222182670d7255bdf44e18715f4902c85a01`;
- Stage 2 report: `ca86d49f1dde1d1a8a1e61f07f4c1e98080ab942ab5c32f89880b387edd867d1`.

Reference A closure status:
`KRAKEN_AI_V2_DEVELOPMENT_REFERENCE_A_CLOSED_NO_TRADE_HOLD_CASH`.
Exact partition boundaries retained for compatibility are
`2024-04-01T00:00:00Z`, `2025-04-01T00:00:00Z` and
`2026-04-01T00:00:00Z`.

Historical Round 1 Causal Signals, Round 1 Family Execution, Round 1 Discovery
Runner, Round 1 Closure, Round 2 Causal Signals, Round 2 Family Execution,
Round 2 Discovery Runner and Round 2 Closure remain immutable evidence. The
former four-path and later three-path results do not constitute learned alpha.

## Current authorization

Candidate v2: not authorized. Calibration: unopened. Evaluation: unopened.
PAPER, cloud, real orders and live execution: not authorized.
