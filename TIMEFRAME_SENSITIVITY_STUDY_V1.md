# Timeframe Sensitivity Study v1

## Purpose

This study asks one narrow research question after the rejection of the first
strategy candidate: does the existing long-only EMA 20/50 behavior materially
change when the native candle timeframe changes from six hours to one hour or
one day?

It is exploratory development evidence. It is not candidate optimization, a
formal Strategy Evaluation Protocol promotion attempt or permission to PAPER or
trade live. Candidate v1 remains permanently closed as `REJECTED`.

## Frozen comparison

The study keeps these inputs unchanged across all three evidence views:

- existing `ema_crossover` Strategy Engine implementation
- nominal fast period 20 and slow period 50
- long-only behavior with no leverage
- exact `BTC-USD` and `ETH-USD` scope
- public native Coinbase Exchange candles
- `[2019-01-01T00:00:00Z, 2026-08-01T00:00:00Z)` range
- 70/30 chronological OOS split
- expanding, non-overlapping walk-forward tests
- completed-Close signal observation and next-bar-Open execution
- final-Close terminal-position reporting
- initial research capital 5,000
- random seed `20260822`, 5,000 simulations and 95% confidence
- the already reviewed baseline and stressed execution-cost profiles

The nominal EMA periods intentionally remain 20/50 bars. Their calendar
horizons therefore change with the timeframe; that is the sensitivity being
measured, not an accidental inconsistency.

| Timeframe | Rows per asset | EMA horizons | Train | Test / step | Source |
| --- | ---: | --- | ---: | ---: | --- |
| `1h` | 66,456 | 20h / 50h | 17,280 bars / 720 days | 4,320 bars / 180 days | New exploratory evaluation |
| `6h` | 11,076 | 120h / 300h | 2,880 bars / 720 days | 720 bars / 180 days | Recorded candidate-v1 report |
| `1d` | 2,769 | 480h / 1,200h | 720 bars / 720 days | 180 bars / 180 days | New exploratory evaluation |

Calendar-equivalent 720-day training and 180-day test/step durations prevent
one timeframe from receiving longer market-history windows merely because it
contains fewer bars.

## Candidate-v1 isolation

The six-hour strategy is not rerun. The study accepts only the exact recorded
candidate-v1 report with SHA-256:

```text
6b79d0932ee334574ffdbef1aca73c8b900ab8fcb8fbafb857bdd327d38d547c
```

It independently verifies that report's checksum sidecar, rejected outcome,
candidate identity, manifest hash, configuration and authorization flags before
using its baseline and stress evidence as the six-hour reference.

Only `1h` and `1d` receive new exploratory evaluations. Their datasets use new
contracts and canonical manifests. The shared generic dataset lock rechecks
manifest bytes and sidecar, source/canonicalization metadata, asset hashes, row
counts, exact UTC grids and OHLCV validity before either evaluation begins.

## Output and interpretation

The one-shot report contains compact baseline and stress evidence for every
timeframe plus a fixed-order comparison of:

- aggregate and per-asset diagnostic classifications
- unseen OOS strategy, benchmark and excess returns
- unseen OOS maximum drawdown and completed trade count
- walk-forward window count, unseen trade count and positive-excess rate
- bootstrap interval, permutation p-value and falsification result

Large equity-curve and individual trade-history arrays are not duplicated into
the study report. Before compaction, every complete in-memory evaluation is
canonically serialized, checked for invalid values and assigned its own
SHA-256 plus canonical byte count. The persisted compact evidence retains OOS,
per-window, aggregate and statistical results needed for review while keeping
the Git artifact bounded. Exact trade-level detail remains deterministically
reproducible from the locked data, configuration, code revision and seed.

The study creates no score, ranking or winner. A strong-looking timeframe is a
hypothesis generator only. The `1h` and `1d` series cover the same underlying
historical market period already inspected through six-hour evidence, so none
of them can serve as a new unseen promotion test.

Every declaration, acquisition summary and recorded result retains:

- `candidate_v1_reopened=false`
- `automatic_timeframe_selection=false`
- `formal_candidate_evaluation=false`
- `candidate_v2_authorized=false`
- `optimization_authorized=false`
- `bounded_forward_paper_review_eligible=false`
- `bounded_forward_paper_authorized=false`
- `live_execution_authorized=false`

## One-shot evidence boundary

The fixed final evidence location is:

```text
data/research/timeframe_sensitivity_v1/study_v1/timeframe_sensitivity_report.json
data/research/timeframe_sensitivity_v1/study_v1/timeframe_sensitivity_report.sha256
```

Existing final evidence refuses any repeat. An interrupted write leaves
`.study_v1.staging`, which also refuses automatic retry until manually reviewed.
Canonical serialization occurs before staging creation, rejects missing time
values and non-finite numbers, and writes no partial result to stdout.

## Controlled integration sequence

Print the frozen declaration without network access or evaluation:

```powershell
python src/timeframe_sensitivity_study.py
```

Do not acquire data merely because the patch is applied. First reproduce the
focused and complete Windows tests, review the diff, commit and push the exact
implementation with a clean working tree.

After that integration gate, acquire the two new development datasets:

```powershell
python src/timeframe_sensitivity_study.py acquire --timeframe 1h --output data/research/timeframe_sensitivity_v1/1h
python src/timeframe_sensitivity_study.py acquire --timeframe 1d --output data/research/timeframe_sensitivity_v1/1d
```

The CSV files remain ignored local research artifacts. Their canonical
manifests and SHA-256 sidecars must be reviewed, committed and pushed as a
separate dataset-lock gate before the study may run.

Only after that separate gate, execute the one-shot comparison:

```powershell
python src/timeframe_sensitivity_study.py run `
    --manifest-1h data/research/timeframe_sensitivity_v1/1h/manifest.json `
    --manifest-1d data/research/timeframe_sensitivity_v1/1d/manifest.json `
    --reference-report data/research/first_candidate_v1/evaluation_v1/evaluation_report.json
```

The recorded study must then be checked, summarized and closed before any v2
design. A formal candidate v2 requires a new immutable identity and a separately
locked genuinely unseen final-validation boundary.
