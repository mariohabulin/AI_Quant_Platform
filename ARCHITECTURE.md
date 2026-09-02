# ARCHITECTURE

## Active architecture

AI-Driven V2 is an offline supervised-learning pipeline with a later immutable
inference runtime. Its first real learned path used locked Kraken 12h OHLCV,
causal features, cost-aware labels and purged walk-forward evidence; that
hypothesis is permanently closed with `HOLD_CASH`.

The next path is intentionally short:

1. inventory new public derivatives-context history without opening values;
2. stop for insufficient history or freeze one causal information hypothesis;
3. only then acquire and lock Development funding, open interest and basis;
4. reuse proven label, walk-forward and economic-evidence boundaries;
5. open later stages only after an independent Development pass.

Manual strategy-family generation and another spot-OHLCV model search are not
part of this path.

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

`kraken_ai_driven_v2_alpha_research_lab.py` reused the archive reader, 12h
causal features, cost-aware labels and three outer folds. Its exact six-variant
registry covered natural logistic, histogram boosting and extra trees for both
calibrated class utility and direct expected-net-R learning.

The earlier 75% of each outer training window fit the learner and its later
purged 25% fit the calibrator. Outer validation fit nothing. All six executed
before comparison with zero threshold and no hyperparameter sweep.

Viability requires fixed support, positive non-overlapping net R in every fold,
positive cumulative net R for at least two assets and positive overall net R.
Only gate passers could be ranked. Attempt 1 produced no passer: all six had
negative overall mean and cumulative net R, zero positive assets and no
all-fold stability. Result SHA-256
`d76bb013c2124672132868752a5bb350a782eb45ef7f062b78b5edcb6d3b3703`
closes this 12h spot-OHLCV architecture with `HOLD_CASH`. Calibration,
Evaluation and Candidate v2 remain sealed.

### Derivatives Context Source Feasibility

`kraken_ai_driven_v2_derivatives_context_feasibility.py` lists official archive
object metadata for monthly funding, daily futures metrics and monthly native
12h mark/index price files for BTCUSDT, ETHUSDT and XRPUSDT. Separate mark and
index legs permit a later causal basis feature.

It opens no values and records coverage across all twelve identities.
Feasibility requires 730 common days, 98% period coverage and no duplicates.
These source gates claim no alpha: pass means a separate learning protocol;
failure means another source or stop, never relaxed economic gates.

### Frozen Derivatives Context Hypothesis

The audit passed with 852 shared days, 100% coverage and no duplicates; report
SHA-256 is `3c84fba6034790ae59761f3fba23affca80fca0c8b7d29b3e3f3762c789d8e29`.
The synthetic-only hypothesis implements nine causal context features with
bounded backward-as-of joins, exact completed-bar basis and no fill. Two
spot-only histogram-GBT controls are matched to classification and net-R
context variants on identical rows and three 30-day-purged folds. Only context
variants can pass absolute and incremental gates. No values are opened or
models fitted.

## Runtime and risk boundary

An approved runtime may load an immutable artifact but cannot fit, mutate,
rank, promote or submit orders; Risk and Synthetic Execution remains the later
simulation/PAPER boundary.

## Failure behavior

The system fails closed for invalid data, boundary crossings, incomplete label
support, changed hashes or unstable after-cost evidence; action is `HOLD_CASH`.
Historical markers: Provider and Historical Availability Boundary v1; Kraken Bounded Blinded Replay Review Boundary v1; Supervised Blinded Replay Execution Boundary v1; AI-Driven v2 Layer Boundary; AI-Driven v2 Signal-State Layer; AI-Driven v2 Risk and Synthetic Execution Layer; AI-Driven v2 Partition Boundary; Development-Only Evidence Runner.
Round 1 Causal Signals, Round 1 Family Execution, Round 1 Discovery Runner and Round 1 Closure used four paths; Round 2 Causal Signals, Round 2 Family Execution, Round 2 Discovery Runner and Round 2 Closure used three paths.
Git through `8c51695` preserves the Rule Discovery Foundation and True Learning Engine scope correction.

## Immutable lineage index

Core IDs: `kraken-btc-eth-xrp-ai-driven-v2-causal-feature-contract-v1`,
`kraken-ai-v2-ccvr-reference-a-v1`, `kraken-ai-v2-risk-execution-reference-a-v1`,
`kraken-btc-eth-xrp-ai-driven-v2-partition-v1`, `kraken-btc-eth-xrp-ai-driven-v2-development-runner-v1`, `kraken-btc-eth-xrp-ai-driven-v2-hybrid-strategy-discovery-learning-v1`,
`kraken-btc-eth-xrp-ai-driven-v2-hybrid-discovery-round-1-v1`, `kraken-btc-eth-xrp-ai-driven-v2-hybrid-discovery-round-2-v1`, `kraken-btc-eth-xrp-ai-driven-v2-true-learning-contract-v1` at `70e7bca` and `796c8de`,
Learning Core and `kraken-btc-eth-xrp-ai-driven-v2-12h-development-learning-runner-v1`,
`kraken-btc-eth-xrp-ai-driven-v2-12h-development-economic-evidence-review-v1`,
`kraken-btc-eth-xrp-ai-driven-v2-alpha-research-lab-v1` and
`kraken-btc-eth-xrp-ai-v2-derivatives-context-feasibility-v1`, followed by
`kraken-btc-eth-xrp-ai-v2-derivatives-context-learning-hypothesis-v1`.

Evidence: BTC episode `56710a21a423a63963e5c97ab6ca956021f9cd7a7d494c3f29a197068367ff60`,
Round 1 `3ce14fda95f657c0b671b74c702d55ec4102da303e9e033ebaf0e02ff5c2fa9b`, Round 2
`5f9acde53d0e2cf35cd1010d0002222182670d7255bdf44e18715f4902c85a01`; Stage 2 compared 1d, 12h and 4h timestamp-only with report
`ca86d49f1dde1d1a8a1e61f07f4c1e98080ab942ab5c32f89880b387edd867d1`, Learning
Attempt 3 `30d020bd9c30306f3e8931b47c0958fea7e11a33bff3795c3473806ddcaa09cf`
and Reference A `f537410d2a237be207951b638518d80e861289dafa7db9b5c2322ffa32d4e594`.

Reference A closure status is
`KRAKEN_AI_V2_DEVELOPMENT_REFERENCE_A_CLOSED_NO_TRADE_HOLD_CASH`. Exact legacy
partition boundaries are `2024-04-01T00:00:00Z`, `2025-04-01T00:00:00Z` and
`2026-04-01T00:00:00Z`. True Learning Contract V1 defines a three-class learner.
Historical compatibility terms: Kraken daily, no model training, Round 1 Discovery
Runner, Round 2 Family Execution and True Learning Engine.
Legacy exact marker: resolution remains unselected.
Candidate v2, Calibration, Evaluation, PAPER, cloud and live remain unauthorized.
