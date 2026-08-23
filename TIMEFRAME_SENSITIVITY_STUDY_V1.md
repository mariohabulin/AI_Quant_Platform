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
- public provider-observed native Coinbase Exchange candles
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
| `1h` | 66,456 expected; observed gaps explicit | 20h / 50h | 720 calendar days | 180 calendar days | New exploratory evaluation |
| `6h` | 11,076 | 120h / 300h | 2,880 bars / 720 days | 720 bars / 180 days | Recorded candidate-v1 report |
| `1d` | 2,769 | 480h / 1,200h | 720 bars / 720 days | 180 bars / 180 days | New exploratory evaluation |

Calendar-equivalent 720-day training and 180-day test/step boundaries prevent
one timeframe from receiving longer market-history windows merely because it
contains fewer observed bars. For one-hour evidence, the boundary is computed
from UTC time rather than shifted by missing provider buckets.

## Candidate-v1 isolation

The six-hour strategy is not rerun. The study accepts only the exact recorded
candidate-v1 report with SHA-256:

```text
6b79d0932ee334574ffdbef1aca73c8b900ab8fcb8fbafb857bdd327d38d547c
```

It independently verifies that report's checksum sidecar, rejected outcome,
candidate identity, manifest hash, configuration and authorization flags before
using its baseline and stress evidence as the six-hour reference.

Only `1h` and `1d` receive new exploratory evaluations. The continuous daily
dataset retains the generic exact-grid lock. The one-hour dataset uses the
separate gap-aware v2 lock after two acquisition attempts proved 19 persistent
BTC provider gaps before ETH acquisition began.

After the normal chunked provider pass, an incomplete grid may trigger only
bounded exact-gap recovery: at most two passes, at most 100 individual missing-
bucket requests per asset and the existing finite transport retry policy on
every request. Recovery accepts only complete Coinbase-returned OHLCV rows. It
never interpolates, forward-fills, resamples or synthesizes a candle. Persistent
gaps remain fatal in the generic continuous-grid builder. The study-only 1h v2
boundary may accept persistent provider gaps only after exact recovery is
exhausted, with at most 50 gaps per asset and at most 24 consecutive gaps. Its
canonical manifest records every absent UTC timestamp, expected/observed counts,
recovery status and maximum consecutive gap. It still never interpolates,
forward-fills, resamples or synthesizes a candle.

The sparse 1h evaluator uses calendar-time OOS and walk-forward boundaries. A
signal immediately before a missing interval may execute only at the next real
provider-observed Open. No absent interval can carry a signal, price, volume or
execution. Acquisition fetches and validates both assets before atomic staging;
failure creates no final dataset evidence.

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

After that integration gate, acquire the two new development datasets. The
daily dataset is already locked; the current remaining command is the reviewed
gap-aware one-hour acquisition:

```powershell
python src/timeframe_sensitivity_study.py acquire --timeframe 1h --output data/research/timeframe_sensitivity_v1/1h
python src/timeframe_sensitivity_study.py acquire --timeframe 1d --output data/research/timeframe_sensitivity_v1/1d
```

If an acquisition stops on a provider-incomplete grid, do not rerun it ad hoc.
Record the attempt first and integrate any reviewed acquisition correction with
tests before retry. Dataset incompleteness is not strategy evidence.

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
