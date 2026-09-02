# ROADMAP

## Current objective
Keep the failed 12h spot-OHLCV hypothesis closed. The derivatives source audit
passed, so freeze one matched causal context experiment before implementing its
hash-bound dataset lock and reader. Do not train until that reader is reviewed.
## Active sequence

### 1. V2 Learning Core — COMMITTED AT `2a09363`

- [x] Freeze the active 12h Development-feasibility path.
- [x] Implement causal multi-asset features.
- [x] Implement next-open cost-aware three-class labels.
- [x] Implement three expanding walk-forward folds.
- [x] Implement one logistic baseline and one constrained tree challenger.
- [x] Prohibit automatic model selection and Candidate promotion.
- [x] Add deterministic synthetic learning and leakage tests.
- [x] Reproduce focused and full Windows tests.
- [x] Commit and push the exact Learning Core milestone.

### 2. Hash-Bound 12h Development Learning Runner — ATTEMPT 3 COMPLETED

- [x] Implement Development-only reader for exact official native 12h members.
- [x] Implement archive, member-byte and timestamp-identity hashes.
- [x] Implement one-shot label generation and censoring diagnostics.
- [x] Implement pre-fit fold/class support report and `HOLD_CASH` branch.
- [x] Persist both models from all three folds as six verifiable artifacts.
- [x] Persist canonical OOF probabilities and predictive metrics.
- [x] Implement atomic evidence package and independent lock.
- [x] Reproduce focused/full Windows tests and static review.
- [x] Commit/push the reviewed runner at `cc8ae44`.
- [x] Run clean Attempt 1 preflight and receive separate authorization.
- [x] Preserve fail-closed Attempt 1 staging after the eight-column adapter error.
- [x] Record the incident and correct to the frozen seven-column Kraken schema.
- [x] Require the untouched Attempt 1 marker and a new recovery authorization.
- [x] Reproduce focused/full Windows Attempt 2 recovery tests and static review.
- [x] Commit/push the reviewed Attempt 2 recovery at `203b4c5`.
- [x] Run clean Attempt 2 preflight and receive a separate recovery authorization.
- [x] Preserve fail-closed Attempt 2 staging after the contradictory endpoint check.
- [x] Record that no frame reached the Learning Core and no label/model was created.
- [x] Replace endpoint presence with full-grid missing-timestamp validation while
  retaining exact archive hash, row counts and missing counts.
- [x] Require both untouched prior markers and a new Attempt 3 authorization.
- [x] Reproduce focused/full Windows Attempt 3 recovery tests and static review.
- [x] Commit/push the reviewed Attempt 3 recovery at `9c1156e`.
- [x] Run clean Attempt 3 preflight and receive separate recovery authorization.
- [x] Execute exactly one authorized real Recovery Attempt 3.
- [x] Record 10,712 labels, six trained artifacts and 11,856 OOF predictions.
- [x] Lock report SHA-256
  `30d020bd9c30306f3e8931b47c0958fea7e11a33bff3795c3473806ddcaa09cf`.

Baseline labels already include adverse commission, spread and slippage. A
read-only economic/stress decision layer follows the immutable OOF evidence;
it is not allowed to refit or automatically select a model.

This stage ends with a real learned result, not another protocol-only loop.

### 3. Read-only Development economic evidence review — COMPLETED `HOLD_CASH`

- [x] Freeze one payoff-derived eligibility rule before opening economic OOF
  outcomes: `3 * P(target) - P(stop) > 0`.
- [x] Prohibit threshold sweep, top-k tuning and automatic model selection.
- [x] Implement raw and per-asset non-overlapping event views.
- [x] Freeze fold support, all-fold stability, asset breadth and PR-AUC-lift
  gates.
- [x] Implement strict prediction-schema, probability and chronology checks.
- [x] Add synthetic positive, `HOLD_CASH`, overlap and tamper tests.
- [x] Reproduce focused and complete Windows regression.
- [x] Commit/push the reviewed economic-review component at `dd7735f`.
- [x] Run it read-only against exact Attempt 3 evidence and prove evidence
  unchanged.
- [x] Record zero positive folds/assets for both families and retain
  `HOLD_CASH`.

### 4. Frozen Alpha Research Lab V1 — COMPLETED `HOLD_CASH`

- [x] Freeze 12h, the existing feature/label/cost boundary and three outer folds.
- [x] Freeze exactly six variants: three calibrated classifiers and three direct
  expected-net-R regressors.
- [x] Freeze chronological 75/25 inner fit/calibration without leakage.
- [x] Freeze zero eligibility threshold, support, all-fold, asset-breadth and
  overall-net-R gates.
- [x] Implement deterministic ranking among gate passers only.
- [x] Implement an executable Development runner with one atomic result.
- [x] Add synthetic leakage, six-variant, economic-gate and `HOLD_CASH` tests.
- [x] Reproduce 10 focused and 1,939 complete Windows tests.
- [x] Commit and push the reviewed lab at `3dcfb2e`.
- [x] Execute all six variants across three folds and 10,712 labels.
- [x] Record result SHA-256
  `d76bb013c2124672132868752a5bb350a782eb45ef7f062b78b5edcb6d3b3703`.
- [x] Close all six as non-viable without adding a seventh variant.

Exactly one branch follows:

- observed branch: no stable evidence; 12h OHLCV closes with `HOLD_CASH`.

No automatic Round 3, resolution change, seventh variant or unbounded search
exists.

### 5. Derivatives-context source feasibility — COMPLETED `SOURCE_FEASIBLE`

- [x] preserve Alpha Research Lab Attempt 1 and its `HOLD_CASH` result;
- [x] freeze funding, open-interest metrics and mark/index basis inputs as the
  only first information bundle;
- [x] implement official public-object listing without opening market values;
- [x] freeze all-assets, 730-day, 98%-coverage and no-duplicate source gates;
- [x] prohibit labels, fitting, tuning, Calibration, Evaluation and Candidate
  promotion inside the audit;
- [x] add deterministic pagination, coverage, missing-source and tamper tests;
- [x] reproduce 14 focused and 1,954 complete Windows tests;
- [x] commit and push the reviewed audit component at `99f6242`;
- [x] run the read-only metadata audit and record report SHA-256
  `3c84fba6034790ae59761f3fba23affca80fca0c8b7d29b3e3f3762c789d8e29`;
- [x] confirm 852 common days, 100% common coverage and zero duplicates.

### 6. Derivatives-context learning hypothesis — PRE-REGISTERED

- [x] freeze nine causal funding, open-interest and basis features;
- [x] freeze causal availability, no-fill rules and three 30-day-purged folds;
- [x] freeze two matched pairs, identical rows and 12 maximum fold fits;
- [x] freeze absolute and incremental gates with no sweeps/control promotion;
- [ ] reproduce focused and complete Windows tests and static review;
- [ ] commit and push the pre-registration milestone;
- [ ] implement the hash-bound derivatives-context dataset lock and reader;
- [ ] validate source schemas before a separate frozen learning runner.

Calibration, Evaluation, Candidate v2, PAPER and live remain closed. A future
run may execute only the frozen variants after independent reader review.

## Retired active work

The following work remains tested historical evidence but is no longer the
active research loop:

- AI-Driven Crypto Research v2 deterministic route discovery;
- AI-Driven v2 State Machine;
- AI-Driven v2 Risk and Execution;
- AI-Driven v2 Development/Evaluation Partition;
- AI-Driven v2 Development Runner;
- Round 1 Causal Signals, Round 1 Family Execution, Round 1 Discovery Runner
  and Round 1 Closure;
- Round 2 Causal Signals, Round 2 Family Execution, Round 2 Discovery Runner
  and Round 2 Closure.

Reference A, four Round 1 families and three Round 2 families are not candidate
models. They are the closed Rule Discovery Foundation.

## Completed evidence controls

- [x] Audit official provider/history evidence.
- [x] Acquire, byte-inventory and lock the v2 archive-only Kraken daily source.
- [x] Acquire, byte-inventory and lock source evidence.
- [x] Execute one sealed preflight with selected timestamps hidden.
- [x] Preserve one-episode-at-a-time review and explicitly decide before advance.
- [x] Preserve opaque source hashes and the Development/Calibration/Evaluation split.
- [x] Close Reference A, Round 1 and Round 2 as `HOLD_CASH`.
- [x] Record True Learning Contract V1 at `70e7bca` and `796c8de`.
- [x] Run Stage 2 over 1d, 12h and 4h using timestamp-only access and no model training.
- [x] Forensically confirm that native 4h begins on 2024-01-01.

## Immutable lineage

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
- `kraken-btc-eth-xrp-ai-driven-v2-alpha-research-lab-v1`
- `kraken-btc-eth-xrp-ai-driven-v2-12h-development-economic-evidence-review-v1`

Evidence hashes include BTC episode `56710a21a423a63963e5c97ab6ca956021f9cd7a7d494c3f29a197068367ff60`,
Reference A `f537410d2a237be207951b638518d80e861289dafa7db9b5c2322ffa32d4e594`,
Round 1 `3ce14fda95f657c0b671b74c702d55ec4102da303e9e033ebaf0e02ff5c2fa9b`, Round 2 `5f9acde53d0e2cf35cd1010d0002222182670d7255bdf44e18715f4902c85a01`, Stage 2 and Learning Attempt 3
`30d020bd9c30306f3e8931b47c0958fea7e11a33bff3795c3473806ddcaa09cf`.

Historical milestones include Provider and Historical Availability Audit v1,
Sealed Preflight Completed, Supervised Blinded Replay v1 and AI-Driven v2
Partition Protocol. `SEALED PREFLIGHT PASS` did not authorize a real replay,
Candidate v2 or live execution.

Reference A closure status:
`KRAKEN_AI_V2_DEVELOPMENT_REFERENCE_A_CLOSED_NO_TRADE_HOLD_CASH`.
Exact partition boundaries: `2024-04-01T00:00:00Z`,
`2025-04-01T00:00:00Z`, `2026-04-01T00:00:00Z`.

Historical compatibility terms: Kraken daily, three-class, no model training,
Round 1 Discovery Runner, Round 2 Family Execution, True Learning Engine and
the former statement that the resolution remains unselected.
Legacy exact marker: resolution remains unselected.

## Authorization state
Candidate v2 is false. Calibration/Evaluation are unopened; PAPER, cloud, real
orders and live execution are unauthorized.
