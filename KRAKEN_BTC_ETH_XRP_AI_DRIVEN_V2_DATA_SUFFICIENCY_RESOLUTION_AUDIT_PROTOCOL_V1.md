# Kraken BTC/ETH/XRP AI-Driven V2 Data Sufficiency and Resolution Audit Protocol V1

## Status and purpose

Protocol ID:
`kraken-btc-eth-xrp-ai-driven-v2-stage-2-data-sufficiency-resolution-audit-v1`

Audit ID:
`kraken-ai-v2-stage-2-data-sufficiency-resolution-audit-v1`

Status:
`KRAKEN_AI_V2_STAGE_2_DATA_SUFFICIENCY_AUDIT_IMPLEMENTED_NO_RUN_AUTHORIZATION`

This is Stage 2 of the True Learning Engine plan. It is bound to the completed
True Learning Contract V1 milestone `796c8de`. It determines whether an
official Kraken source-native resolution contains enough causal Development
opportunities for the bounded learner. It does not ask which timeframe made
more money.

This protocol implements and reviews the audit before any source archive is
opened. Execution requires the exact separate operator phrase
`EXECUTE_KRAKEN_AI_V2_STAGE_2_DATA_SUFFICIENCY_AUDIT_ONCE` after commit/push.

## Why these three resolutions

The fixed candidate order is:

1. `KRAKEN_NATIVE_1D` — `1440` minutes;
2. `KRAKEN_NATIVE_12H` — `720` minutes; and
3. `KRAKEN_NATIVE_4H` — `240` minutes.

All three are native members of Kraken's official downloadable historical
OHLCVT archive. The audit compares 1d, 12h and 4h. Six-hour data is not used:
it is not a member of the official Kraken archive candidate set and an older
hand-written six-hour strategy is not evidence for choosing it.

The candidate order is coarsest to finest. The frozen selection policy is
`COARSEST_PASSING_CANDIDATE`: if more than one candidate passes every absolute
support gate, the coarsest passing candidate is selected to
limit serial dependence and computational load. A candidate that fails one
asset or one fold fails as a shared BTC/ETH/XRP learning resolution.

## Timestamp-only access boundary

The audit uses the exact previously frozen complete Kraken archive:

- filename: `Kraken_OHLCVT.zip`;
- bytes: `7,885,068,519`;
- SHA-256:
  `e6ab4a3d2fe3be99167607fa28f230a84a038ad3ea3348ef81dc4bffcabb758d`.

The reader locates exactly one `XBTUSD`, `ETHUSD` and `XRPUSD` member for each
of intervals `1440`, `720` and `240`. It consumes only the first Unix timestamp
field and ignores all remaining value fields. It stops at the Development end.

The audit therefore may report availability geometry but may not parse or
report Open, High, Low, Close, VWAP, Volume, Trades, returns, labels, barriers,
signals, fills, P&L or any model score. Calibration and Evaluation market data
remain unopened. Network acquisition is not implemented or authorized.

The archive and evidence directories must stay outside the repository and may
not overlap. The archive filename, byte size and SHA-256 must match before any
timestamp member is read.

## Frozen Development window

Only the half-open calendar interval from `2019-01-01T00:00:00Z` inclusive to
`2024-04-01T00:00:00Z` exclusive participates in candidate counts.

For every asset and resolution, timestamps must be integer Unix seconds,
strictly increasing, unique, inside Development and aligned to the candidate
interval from the Development start. A missing bucket remains missing. It is
never forward-filled, backfilled, interpolated or represented by a synthetic
zero-volume row. Every discontinuity starts a new continuous segment.

## Resolution-neutral example geometry

The True Learning Contract permits features whose maximum causal warm-up is
frozen here at `90` elapsed UTC days. That becomes 90 daily bars, 180 twelve-
hour bars or 540 four-hour bars. Each continuous segment pays its own warm-up;
no context crosses a provider gap.

The label horizon remains the Stage 1 value of `30` elapsed UTC days. A valid
potential example requires:

- a completed decision bar after the full 90-day warm-up;
- a next observed bar for the hypothetical entry; and
- a complete 30-day future timestamp path inside the same continuous segment.

This audit does not generate the outcome label. It counts only whether the
timestamp geometry could support one. Warm-up losses, right-edge censored
opportunities, gaps and continuous-segment lengths are reported separately.

For conservative dependence reporting, nonoverlapping horizon capacity counts
decision intervals spaced by at least one complete 30-day horizon. Training
will still require event-uniqueness weights; this capacity is not a claim that
all remaining bar-level examples are statistically independent.

## Absolute nonperformance support gates

Every candidate must satisfy every gate for every asset:

| Gate | Frozen minimum or maximum |
|---|---:|
| observed timestamp coverage | at least `0.995` |
| valid potential examples | at least `9,000` |
| nonoverlapping 30-day horizons | at least `48` |
| largest continuous segment | at least `730` UTC days |
| maximum provider gap | at most `7` UTC days |
| training examples per asset in every fold | at least `3,000` |
| validation examples per asset in every fold | at least `900` |

These gates were fixed before opening the archive and before labels exist. They
represent minimum support for three assets, three outcome classes, fold-local
preprocessing/probability calibration and twelve bounded model variants. They
are not profitability thresholds and may not be weakened after seeing audit
counts. If no resolution passes, the result is no selection and the project
must extend or re-lock source data before Stage 3.

## Exact global walk-forward capacity plan

All assets share these calendar folds. A label interval must end before the
training or validation end to count inside that scope.

| Fold | Training end exclusive | Purge | Validation | Embargo end exclusive |
|---|---|---:|---|---|
| `FOLD_1` | `2021-03-02T00:00:00Z` | 30 days | `2021-04-01` through `2022-04-01` exclusive | `2022-05-01T00:00:00Z` |
| `FOLD_2` | `2022-04-01T00:00:00Z` | 30 days | `2022-05-01` through `2023-05-01` exclusive | `2023-05-31T00:00:00Z` |
| `FOLD_3` | `2023-05-01T00:00:00Z` | 30 days | `2023-05-31` through `2024-04-01` exclusive | `2024-05-01T00:00:00Z` |

Training always begins at Development start and expands forward. Validation
windows do not overlap. The final validation window ends exactly at the
Development boundary. Fold dates are calendar-selected and cannot change in
response to class support, predictive score or economic outcome.

## Deterministic selection and evidence

Each asset/resolution result records:

- expected and observed timestamp rows;
- coverage and missing-bucket counts;
- gap count and maximum gap size;
- continuous-segment row counts and largest-segment days;
- warm-up loss and right-edge censoring;
- valid example count and nonoverlapping horizon capacity;
- training/validation capacity for all three folds; and
- SHA-256 of the valid potential-example timestamp identities.

The candidate gate matrix and selection are canonical JSON. One exact run may
atomically write the report and SHA-256 sidecar, then an independent evidence
lock must reproduce the checksum, canonical encoding, identity and all safety
fields. A final or staging evidence directory makes a repeat fail closed.

Possible terminal statuses are:

- `KRAKEN_AI_V2_STAGE_2_RESOLUTION_SELECTED_DATASET_LOCK_REQUIRED`; or
- `KRAKEN_AI_V2_STAGE_2_NO_RESOLUTION_SELECTED_DATA_EXTENSION_REQUIRED`.

Selection does not itself create or lock a dataset. Any newly selected
resolution requires a separate immutable dataset lock before feature or label
generation.

## Explicit prohibitions

Stage 2 may not use or produce:

- returns, expectancy, profit factor, win rate, model score or prior route
  performance;
- OHLCVT values, features, labels, barriers, trades or positions;
- model fitting, hyperparameter search, walk-forward prediction or ranking;
- Calibration or Evaluation market access;
- Candidate v2 promotion;
- PAPER, cloud, real orders or live execution; or
- an automatic change to the True Learning Contract.

At protocol review, source archive opened, timestamp columns opened, labels
generated and model training executed are all `false`. The only next action is
a separate operator decision for one timestamp-only Stage 2 audit.
