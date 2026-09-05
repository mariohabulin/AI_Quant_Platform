# Kraken AI-Driven V2 Attempt 4 Mark/Index Alignment Incident

## Read-only review result

The corrected independent reader ran against the immutable Attempt 4 final
lock from commit `245db6b82a82826b80af30b30e9cdf58e8810ead`. The manifest
SHA-256 remained
`db4dde045d9fce22bee1389fe8c7ad13d3e3ccc5e5c4ace7c433f5461ba11916`.
The manifest, sidecar, 5,630-file count and 63,045,508 total bytes were
unchanged, and no network access, label generation or model training occurred.

Explicit ISO-8601 parsing passed. The reader then failed because it required
the complete mark-price and index-price timestamp indexes to be identical
before constructing basis inputs.

## Timestamp-only forensic evidence

The authorized read-only forensic scan opened only normalized open and close
timestamp columns. It found:

| Asset | Mark rows | Index rows | Common rows | Mark only | Index only | Close mismatch |
|---|---:|---:|---:|---:|---:|---:|
| BTC-USD | 1,698 | 1,680 | 1,680 | 18 | 0 | 0 |
| ETH-USD | 1,700 | 1,698 | 1,698 | 2 | 0 | 0 |
| XRP-USD | 1,700 | 1,698 | 1,698 | 2 | 0 | 0 |

Both source indexes are strictly increasing and unique, share the same first
and last timestamps, and every common open timestamp has the same mark/index
close timestamp. The index source is therefore an exact timestamp subset of
the mark source. The unmatched rows are source absences, not altered or
misordered observations.

## Frozen correction

The parent hypothesis already requires mark and index prices from the exact
same completed native 12h bar and states that an absent source invalidates the
row and its rolling context. The independent reader must therefore inner-align
mark and index on exact open timestamps, verify equal close timestamps on every
common row, and expose only those paired observations.

No timestamp or value may be filled, interpolated, shifted, synthesized or
matched approximately. Each source must remain strictly increasing and unique.
The reader records source-row, common-row and unmatched-row counts for every
asset. Reindexing those paired observations onto Kraken decision timestamps
leaves missing bars as missing, so the existing 60-consecutive-bar context
rule invalidates affected rows naturally.

This correction changes no locked byte, manifest, feature formula, label,
economic gate or model. Attempt 4 acquisition remains complete and consumed.
After implementation, tests and a new commit, only the same existing final
lock may be reviewed again read-only.
