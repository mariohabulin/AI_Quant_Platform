# CURRENT MISSION

## Mission

Recover the fail-closed 12h Development Learning Attempt 2, remove the
contradictory endpoint assertion while retaining exact hash/grid/count checks,
and review a new one-shot Attempt 3 boundary. The corrected Development
Learning Runner remains inert during this review.

Status:
`KRAKEN_AI_V2_12H_DEVELOPMENT_LEARNING_ATTEMPT_2_FAILED_RECOVERY_REVIEW_REQUIRED`

Recovery parent milestone: `203b4c5`

Active protocol:
`kraken-btc-eth-xrp-ai-driven-v2-12h-development-learning-runner-v1`

## What is implemented now

- strict Development-only 12h frame validation;
- 16 causal market-context features plus asset identity;
- next-open, adverse-cost, `3R/-1R/30-day` triple-barrier labels;
- stop-first same-bar handling and provider-gap censoring;
- three fixed expanding walk-forward folds;
- fold-local preprocessing;
- real multinomial logistic-regression fitting;
- real histogram-gradient-boosting fitting;
- out-of-fold probabilities and predictive metrics;
- deterministic learned-model SHA-256 artifacts; and
- no automatic ranking or promotion.

The runner additionally persists real estimator bytes, canonical OOF
predictions, label/censor diagnostics and exact source/artifact hashes. It has a
noncrashing `HOLD_CASH` evidence branch if a fold lacks class support.

Synthetic tests train actual parameters. Attempt 1 failed on an incorrect
eight-column assumption before parsing OHLCV. Attempt 2 corrected that schema,
validated the full archive and parsed BTC Development rows, then failed before
returning any frame because the reader simultaneously accepted one missing BTC
bucket and required the final bucket to exist. Neither attempt generated a
feature, label, model, prediction or conclusion. Both staging markers are
preserved and both authorizations are consumed. No real Development model has yet been fitted.

## Why 12h is active

Stage 2 report
`ca86d49f1dde1d1a8a1e61f07f4c1e98080ab942ab5c32f89880b387edd867d1`
found approximately 3,348 to 3,593 valid 12h examples per asset over the full
Development interval. That is enough to attempt one bounded shared low-
complexity feasibility learner; it is not a profitability guarantee.

The timestamp-only forensic scan confirmed that native 4h covers only
`2024-01-01T00:00:00Z` through the end of the archive. The reader was correctly
ordered and did not omit hidden 2019-2023 rows.

The old Stage 2 per-asset thresholds remain historical evidence but are retired
from the active process because they were not derived from the implemented
two-model learning design.

## Completion gate for this milestone

1. focused Learning Core and runner tests pass;
2. complete regression passes;
3. independent Core, protocol and runner hashes match;
4. Windows reproduces the results;
5. commit/push occurs from a clean reviewed worktree.

Only then do we run a clean Attempt 3 source/evidence preflight. Recovery
requires both preserved prior staging markers, a new Attempt 3 evidence root
and the new separate phrase
`EXECUTE_KRAKEN_AI_V2_12H_DEVELOPMENT_LEARNING_RECOVERY_ATTEMPT_3_ONCE`.

## Nonauthorization

- source archive opened during failed Attempt 2: `true`;
- BTC Development source values parsed during failed Attempt 2: `true`;
- complete Development frames returned to Learning Core: `false`;
- real labels generated: `false`;
- real model training executed: `false`;
- Calibration data opened: `false`;
- Evaluation data opened: `false`;
- Candidate v2 authorized: `false`;
- PAPER, cloud, real orders and live execution authorized: `false`.

## Historical state, no longer the active mission

The following exact markers are preserved for regression traceability:

- `AI-DRIVEN V2 CAUSAL FEATURE CONTRACT`;
- `STATE MACHINE IMPLEMENTED`;
- `RISK AND EXECUTION ADAPTER IMPLEMENTED`;
- `PARTITION PROTOCOL FROZEN`;
- `DEVELOPMENT RUNNER IMPLEMENTED`;
- `SEALED PREFLIGHT PASS` and `SUPERVISED REPLAY PREPARATION`;
- Reference A closed after 13 rejected entries with `HOLD_CASH`;
- Round 1 used four paths and 12 routes;
- Round 2 used three paths and 7 routes;
- Rule Discovery Foundation is closed; True Learning Engine work is now active.

Historical component IDs:

- `kraken-btc-eth-xrp-ai-driven-v2-causal-feature-contract-v1`
- `kraken-ai-v2-ccvr-reference-a-v1`
- `kraken-ai-v2-risk-execution-reference-a-v1`
- `kraken-btc-eth-xrp-ai-driven-v2-partition-v1`
- `kraken-btc-eth-xrp-ai-driven-v2-development-runner-v1`
- `kraken-btc-eth-xrp-ai-driven-v2-hybrid-strategy-discovery-learning-v1`
- `kraken-btc-eth-xrp-ai-driven-v2-hybrid-discovery-round-1-v1`
- `kraken-btc-eth-xrp-ai-driven-v2-hybrid-discovery-round-2-v1`
- `kraken-btc-eth-xrp-ai-driven-v2-true-learning-contract-v1`

Historical hashes:

- `56710a21a423a63963e5c97ab6ca956021f9cd7a7d494c3f29a197068367ff60`
- `f537410d2a237be207951b638518d80e861289dafa7db9b5c2322ffa32d4e594`
- `3ce14fda95f657c0b671b74c702d55ec4102da303e9e033ebaf0e02ff5c2fa9b`
- `5f9acde53d0e2cf35cd1010d0002222182670d7255bdf44e18715f4902c85a01`

Reference A closure status:
`KRAKEN_AI_V2_DEVELOPMENT_REFERENCE_A_CLOSED_NO_TRADE_HOLD_CASH`.
Historical provider work used fail-closed Kraken daily acquisition. Exact
partition boundaries are `2024-04-01T00:00:00Z`,
`2025-04-01T00:00:00Z` and `2026-04-01T00:00:00Z`.

True Learning Contract V1 was defined at `70e7bca` and integrated at `796c8de`.
Its historical statement that the resolution remains unselected preceded the
Stage 2 comparison of 1d, 12h and 4h with timestamp-only access and no model
training. The active feasibility resolution is now 12h.

Historical names retained: AI-Driven v2 State Machine, AI-Driven v2 Risk and
Execution, AI-Driven v2 Development/Evaluation Partition, AI-Driven v2
Development Runner, Round 1 Causal Signals, Round 1 Family Execution, Round 1
Discovery Runner, Round 1 Closure, Round 2 Causal Signals, Round 2 Family
Execution, Round 2 Discovery Runner and Round 2 Closure.

Historical compatibility terms: Kraken daily, three-class, no model training,
Round 1 Discovery Runner, Round 2 Family Execution, True Learning Engine and
the former statement that the resolution remains unselected.
Legacy exact marker: resolution remains unselected.

Candidate v2 and live execution remain unauthorized.
