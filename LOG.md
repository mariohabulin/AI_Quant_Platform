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
- `56710a21a423a63963e5c97ab6ca956021f9cd7a7d494c3f29a197068367ff60`
- `f537410d2a237be207951b638518d80e861289dafa7db9b5c2322ffa32d4e594`

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
