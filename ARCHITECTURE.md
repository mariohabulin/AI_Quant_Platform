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

### Development Learning Runner and completed evidence

`kraken_ai_driven_v2_12h_development_learning_runner.py` read only the three
native Kraken 12h members inside Development, hashed the archive and complete
member bytes, called the Learning Core and atomically recorded label
diagnostics, fold support, OOF predictions, metrics and learned model files.

The native adapter accepts the frozen seven source fields `Unix time, Open,
High, Low, Close, Volume, Trades`. Attempts 1 and 2 exposed fixture assumptions
before any learning result. The corrected reader validates the full aligned
grid, records missing timestamps and retains archive hash, row and gap counts.

Every completed training branch contains exactly six `.pkl` artifacts: two
models fitted independently in each of three folds. The lock hashes them
without unpickling. If a fold lacks all three classes, fitting does not begin
and immutable evidence closes with `HOLD_CASH`. The runner never selects a
winner or promotes a Candidate.

Recovery Attempt 3 completed with 10,712 labeled rows, six fold-model artifacts
and 11,856 OOF predictions. Its immutable report SHA-256 is
`30d020bd9c30306f3e8931b47c0958fea7e11a33bff3795c3473806ddcaa09cf`;
Calibration and Evaluation remained unopened.

### Development Economic Evidence Review

`kraken_ai_driven_v2_12h_development_economic_review.py` is a deterministic
read-only consumer of the locked Attempt 3 evidence. It does not open source
OHLCV, generate labels, unpickle models or refit parameters.

The sole entry-interest rule is the untuned payoff floor
`3 * P(target) - P(stop) > 0`. It reports both every eligible OOF decision and a
chronological view with at most one overlapping event per asset. Development
interest requires support, positive net R in all three folds, positive breadth
across at least two assets and positive target PR-AUC lift in every fold. A pass
requires operator review; it cannot select a family or authorize Candidate v2.
A failure returns `HOLD_CASH`. The completed review found zero positive folds
and assets for both V1 families: logistic produced 659 non-overlapping events
and `-378.32 R`; histogram boosting produced 240 and `-82.93 R`.

This is not a portfolio simulation. Capital allocation, cross-asset concurrency,
drawdown and stress execution remain later work only if evidence warrants it.

### Frozen Alpha Research Lab

`kraken_ai_driven_v2_alpha_research_lab.py` is the sole active Development
experimentation loop. It reuses the same archive reader, 12h causal features,
cost-aware labels and three outer folds. Its registry contains exactly six
variants: natural logistic, histogram boosting and extra trees for calibrated
three-class utility, plus ridge, histogram boosting and extra trees for direct
expected-net-R learning.

Within each outer training window, the earlier 75% of decision timestamps fits
the base learner and the later purged 25% fits a probability or net-R calibrator.
Outer validation fits nothing. All six variants execute before comparison.
Eligibility stays at predicted utility/net R above zero; there is no threshold
or hyperparameter sweep.

Viability requires fixed support, positive non-overlapping net R in every fold,
positive cumulative net R for at least two assets and positive overall net R.
Only gate passers can be ranked, first by worst-fold mean net R, then overall
mean, then frozen registry order. A selected result is only a Development
winner. Calibration, Evaluation and Candidate v2 remain sealed.

## Runtime and risk boundary

An approved runtime may load one immutable artifact but cannot fit, mutate,
rank, promote or submit orders. The AI-Driven v2 Risk and Synthetic Execution
Layer remains the boundary for any later simulation or PAPER stage.

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

Git through `8c51695` preserves Provider and Historical Availability Boundary v1; Kraken Bounded Blinded Replay Review Boundary v1; Supervised Blinded Replay Execution Boundary v1; AI-Driven v2 Layer Boundary; AI-Driven v2 Signal-State Layer; AI-Driven v2 Risk and Synthetic Execution Layer; AI-Driven v2 Partition Boundary; and Development-Only Evidence Runner.
It also preserves Round 1 Causal Signals with four paths, Round 1 Family Execution, Round 1 Discovery Runner and Round 1 Closure; Round 2 Causal Signals, Round 2 Family Execution, Round 2 Discovery Runner and Round 2 Closure; and the Rule Discovery Foundation and True Learning Engine scope correction.
These are historical rule tests, not learned model artifacts.

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
- `kraken-btc-eth-xrp-ai-driven-v2-12h-development-economic-evidence-review-v1`
- `kraken-btc-eth-xrp-ai-driven-v2-alpha-research-lab-v1`
- BTC episode `56710a21a423a63963e5c97ab6ca956021f9cd7a7d494c3f29a197068367ff60`
- Round 1 `3ce14fda95f657c0b671b74c702d55ec4102da303e9e033ebaf0e02ff5c2fa9b`
- Round 2 `5f9acde53d0e2cf35cd1010d0002222182670d7255bdf44e18715f4902c85a01`
- Stage 2 `ca86d49f1dde1d1a8a1e61f07f4c1e98080ab942ab5c32f89880b387edd867d1`
- 12h Learning Attempt 3 `30d020bd9c30306f3e8931b47c0958fea7e11a33bff3795c3473806ddcaa09cf`
- Reference A `f537410d2a237be207951b638518d80e861289dafa7db9b5c2322ffa32d4e594`

True Learning Contract V1 began at `70e7bca` and was integrated at `796c8de`.
Stage 2 compared 1d, 12h and 4h using a timestamp-only reader with no model
training. The old statement that the resolution remains unselected is retained
only as historical Stage 1 state; the active feasibility resolution is 12h.

Reference A closure status is
`KRAKEN_AI_V2_DEVELOPMENT_REFERENCE_A_CLOSED_NO_TRADE_HOLD_CASH`. Exact legacy
partition boundaries are `2024-04-01T00:00:00Z`, `2025-04-01T00:00:00Z` and
`2026-04-01T00:00:00Z`. True Learning Contract V1 defines a three-class learner.
Historical compatibility terms: Kraken daily, no model training, Round 1 Discovery
Runner, Round 2 Family Execution and True Learning Engine.
Legacy exact marker: resolution remains unselected.
Candidate v2, Calibration, Evaluation, PAPER, cloud and live remain unauthorized.
