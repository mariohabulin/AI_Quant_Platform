# Strategy Family Screening Runner v1

## Purpose

This runner executes the already pre-registered default-only development screen
exactly once and records canonical bounded evidence. It does not change the
frozen strategy list, parameters, dataset, windows, costs, thresholds or
interpretation policy.

The runner may eliminate mechanisms or identify mechanisms that retain research
interest. It cannot rank them, choose a winner, create candidate v2 or authorize
PAPER/live execution.

## Exact execution matrix

The frozen order is:

1. ADX 14/25
2. ATR breakout 14/1
3. Bollinger 20/2
4. Donchian 20
5. MACD 12/26/9
6. RSI 14/30/70
7. Stochastic 14/3/20/80
8. Supertrend 10/3

Each strategy runs once under baseline costs and once under stressed costs.
Every run uses the same BTC/ETH 6h frames and the same `MultiAssetValidator`
configuration. The complete matrix is therefore 16 multi-asset evaluations, or
32 asset/profile views. No parameter loop or indicator combination exists.

## Fail-closed preconditions

Before constructing any validator, the runner requires:

- absent final `screening_v1` evidence
- absent `.screening_v1.staging` evidence
- the exact protocol dataset lock and manifest SHA-256
  `6506dd2700b983a134a132890ef4c4ae6e84c0918ba65a5abff6ab2c204c4e7f`
- exact BTC/ETH asset scope
- exact eight-strategy order and Strategy Engine identities
- the unchanged frozen screening configuration
- exact strategy declaration order and fingerprints

Any identity, scope, classification or evidence-shape drift stops execution.

## Evidence and outcomes

Baseline and stress evidence is independently compacted. The complete raw
in-memory evaluation receives a canonical SHA-256 and byte count, while the
persisted report omits duplicated trade histories and equity curves. It retains
aggregate/asset classifications, OOS performance and benchmark comparison,
walk-forward windows and summaries, unseen trade counts and falsification
evidence.

The existing defined `profit_factor=+inf` state is encoded only as
`POSITIVE_INFINITY_NO_LOSING_TRADES`, with an occurrence count per evaluation.
NaN, negative infinity and every other unsupported non-finite value remain
fatal before staging exists. The same compactor now serves the already tested
Timeframe Sensitivity runner without changing its schema or evidence bytes.

The frozen gate review permits only:

- `SCREEN_OUT` when either baseline or stress multi-asset classification is
  `REJECTED`
- `MECHANISM_RETAINS_INTEREST` when baseline and stress are both `VALIDATED`
  and every frozen window/trade-volume/drawdown gate passes
- `INCONCLUSIVE` otherwise

The report contains fixed-order outcomes and counts, not a return score. A list
of mechanisms retaining interest preserves protocol order and has no tie-break.
Several mechanisms or none may appear. `selected_strategy` remains null.

## Atomic one-shot persistence

All 16 evaluations, compaction, comparisons and final canonical serialization
complete in memory before any directory is created. The runner then writes:

```text
data/research/strategy_family_screening_v1/.screening_v1.staging/
  strategy_family_screening_report.json
  strategy_family_screening_report.sha256
```

Only after both bytes are written does the staging directory atomically rename
to `screening_v1`. Existing final or staging evidence refuses every repeat. An
interrupted staging directory requires manual review; it is never silently
deleted or reused.

## Controlled command after repository integration

First confirm a clean repository, exact pushed runner revision, valid frozen
manifest and absent final/staging evidence. Then the separately reviewed
one-shot command is:

```powershell
python src/strategy_family_screening_runner.py `
    --manifest data/research/first_candidate_v1/manifest.json
```

The CLI prints only the recorded status, report/checksum paths, SHA-256, outcome
counts and mechanisms retaining interest. Full evidence remains in the
canonical report for independent review and hashing.

Running the command establishes only inspected development evidence. Every
report explicitly retains:

- `automatic_ranking_generated=false`
- `automatic_strategy_selection=false`
- `formal_candidate_evaluation=false`
- `candidate_v2_authorized=false`
- `optimization_authorized=false`
- `bounded_forward_paper_authorized=false`
- `live_execution_authorized=false`

No later review may convert this historical screen into unseen validation.
