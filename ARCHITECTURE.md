# ARCHITECTURE

## Active architecture

AI-Driven V2 is an offline supervised-learning research pipeline with a later
immutable inference runtime. The active path is intentionally short:

1. locked Kraken 12h Development OHLCV;
2. causal feature construction;
3. next-open cost-aware triple-barrier labeling;
4. expanding purged walk-forward learning;
5. out-of-fold predictive and economic evidence;
6. an operator-reviewed frozen Candidate, if evidence warrants one;
7. one-time Calibration, untouched Evaluation and bounded PAPER in that order.

Manual strategy-family generation is not part of this path.

## Data and partition boundary

The research universe is `BTC-USD`, `ETH-USD`, `XRP-USD` in that order.

| Partition | UTC interval | Active use |
|---|---|---|
| Development | 2019-01-01 to 2024-04-01 exclusive | feature, label, fit and walk-forward validation |
| Calibration | 2024-04-01 to 2025-04-01 exclusive | unopened; later frozen-candidate confirmation only |
| Evaluation | 2025-04-01 to 2026-04-01 exclusive | unopened sealed one-time evaluation |

No preprocessing state, label path or model parameter crosses a partition.
Provider gaps split causal segments and invalidate any event that crosses them.

## Learning Core components

### Frame validator

Accepts exactly three timezone-aware, ordered 12h OHLCV frames. It checks
numeric values, OHLC geometry, timestamp alignment and the Development boundary.
It does not repair, interpolate or manufacture rows.

### Causal feature engine

`kraken_ai_driven_v2_learning_core.py` constructs a fixed low-dimensional
schema from returns, ATR, volatility, EMA distances, prior structure, relative
volume, RSI, same-timestamp market context and asset identity.

All rolling state ends at the completed decision bar. Prior support/resistance
excludes the current bar. Cross-asset context is joined only at a common already
completed timestamp.

### Label engine

The label engine enters at the next observed open. Baseline adverse commission,
spread and slippage are included. One risk unit is `1.5 ×` signal-time ATR-14.
It records target-first, stop-first or timeout; same-bar ambiguity is stop-first.
Insufficient future history and provider gaps are censored, reported and never
fitted.

### Walk-forward learner

Each fold creates a new preprocessing pipeline and model instance. Training
events must finish before the training boundary. Validation begins later and no
validation row can refit the model that predicts it.

V1 contains exactly:

- `LOGISTIC_BASELINE`;
- `HIST_GBT_CHALLENGER`.

There is no automatic winner. The output is probabilities, metrics and model
artifact hashes for operator review.

### Development Learning Runner

`kraken_ai_driven_v2_12h_development_learning_runner.py` is now implemented but
inert. After a separate exact one-shot authorization it can read only the three
native Kraken 12h members inside Development, hash the archive and complete
member bytes, call the Learning Core and atomically record label diagnostics,
fold support, OOF predictions, metrics and learned model files.

The native adapter accepts exactly the frozen seven source fields `Unix time,
Open, High, Low, Close, Volume, Trades`. Attempt 1 at `cc8ae44` exposed an
eight-column synthetic-fixture defect before any OHLCV value, label or model
was produced. Recovery requires the preserved empty Attempt 1 staging marker,
a new Attempt 2 evidence root and a new authorization phrase.

Every completed training branch contains exactly six `.pkl` artifacts: two
models fitted independently in each of three folds. The lock hashes them
without unpickling. If a fold lacks all three classes, fitting does not begin
and immutable evidence closes with `HOLD_CASH`. The runner never selects a
winner or promotes a Candidate.

## Runtime and risk boundary

An approved runtime may load one immutable artifact for inference. It cannot
fit, mutate, rank or promote a model. The existing AI-Driven v2 Risk and
Synthetic Execution Layer remains the safety boundary for later simulation and
PAPER. No research component can submit a real order.

## Failure behavior

The system fails closed when:

- timestamps, OHLCV or feature values are invalid;
- an event crosses a provider gap or Development boundary;
- a fold lacks all three outcome classes;
- a source, configuration, model or prediction hash changes;
- Calibration or Evaluation appears in training input; or
- no model produces stable later-period evidence after costs.

The failure action is `HOLD_CASH`, not a relaxed gate or another automatic
strategy search.

## Historical architecture retained outside the active path

Git history through `8c51695` and the versioned protocol files preserve these
completed boundaries:

- Provider and Historical Availability Boundary v1;
- Kraken Bounded Blinded Replay Review Boundary v1;
- Supervised Blinded Replay Execution Boundary v1;
- AI-Driven v2 Layer Boundary;
- AI-Driven v2 Signal-State Layer;
- AI-Driven v2 Risk and Synthetic Execution Layer;
- AI-Driven v2 Partition Boundary;
- Development-Only Evidence Runner;
- Round 1 Causal Signals, Round 1 Family Execution, Round 1 Discovery Runner
  and Round 1 Closure;
- Round 2 Causal Signals, Round 2 Family Execution, Round 2 Discovery Runner
  and Round 2 Closure; and
- Rule Discovery Foundation and True Learning Engine scope correction.

Reference A used four deterministic paths and closed with 13 rejected entries,
zero approved entries and `HOLD_CASH`; this was not a break-even strategy result.
Round 1 evaluated 12 routes, while Round 2 evaluated 7 routes and three exact
families. These are historical rule tests, not learned model artifacts.

## Immutable lineage index

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
- BTC episode `56710a21a423a63963e5c97ab6ca956021f9cd7a7d494c3f29a197068367ff60`
- Round 1 `3ce14fda95f657c0b671b74c702d55ec4102da303e9e033ebaf0e02ff5c2fa9b`
- Round 2 `5f9acde53d0e2cf35cd1010d0002222182670d7255bdf44e18715f4902c85a01`
- Stage 2 `ca86d49f1dde1d1a8a1e61f07f4c1e98080ab942ab5c32f89880b387edd867d1`
- Reference A `f537410d2a237be207951b638518d80e861289dafa7db9b5c2322ffa32d4e594`

True Learning Contract V1 began at `70e7bca` and was integrated at `796c8de`.
Stage 2 compared 1d, 12h and 4h using a timestamp-only reader with no model
training. The old statement that the resolution remains unselected is retained
only as historical Stage 1 state; the active feasibility resolution is 12h.

Reference A closure status is
`KRAKEN_AI_V2_DEVELOPMENT_REFERENCE_A_CLOSED_NO_TRADE_HOLD_CASH`. Exact legacy
partition boundaries are `2024-04-01T00:00:00Z`, `2025-04-01T00:00:00Z` and
`2026-04-01T00:00:00Z`. True Learning Contract V1 defines a three-class learner.

Historical compatibility terms: Kraken daily, no model training, Round 1
Discovery Runner, Round 2 Family Execution, True Learning Engine and the former
statement that the resolution remains unselected.
Legacy exact marker: resolution remains unselected.

Candidate v2, Calibration, Evaluation, PAPER, cloud and live remain unauthorized.
