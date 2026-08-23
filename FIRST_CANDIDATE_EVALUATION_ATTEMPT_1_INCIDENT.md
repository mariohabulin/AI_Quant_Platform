# First Candidate Evaluation Attempt 1 — Serialization Incident

## Incident record

- Date: `2026-08-23`
- Frozen candidate: `ema-crossover-20-50-btc-eth-native-6h-v1`
- Manifest SHA-256:
  `6506dd2700b983a134a132890ef4c4ae6e84c0918ba65a5abff6ab2c204c4e7f`
- Pre-registration commit: `a43fd57`
- Evaluation-runner commit: `1b8f7d1`
- Outcome classification: `TECHNICAL_SERIALIZATION_FAILURE`

## What happened

The controlled runner loaded and revalidated the frozen dataset, executed the
existing Strategy Evaluation Protocol, and assembled its in-memory evidence.
Canonical JSON serialization then failed because a benchmark `entry_index`
contained a Pandas `Timestamp`, which the v1 serializer did not support.

The exception occurred before creation of either the final `evaluation_v1`
directory or the `.evaluation_v1.staging` directory. Both paths were explicitly
checked after the failure and were absent. The CLI printed no strategy outcome
or performance values, and no report or checksum was persisted.

This incident is not `PAPER_CANDIDATE`, `RESEARCH_HOLD` or `REJECTED`. It is a
runner evidence-serialization defect and reveals no strategy result.

## Recovery authorization boundary

Recovery is limited to deterministic evidence serialization:

- support Pandas/NumPy timestamps and scalar values in canonical JSON
- add a regression test matching the failing nested `entry_index`
- retain rejection of missing time values and non-finite numbers
- run focused and full tests
- review, commit and push the exact repair before recovery execution

The candidate identity, strategy parameters, dataset and hashes, chronological
windows, seed, costs, thresholds and protocol decision logic must not change.
Because the protocol is deterministic under frozen seed `20260822`, a recovery
execution after this repair is a reproduction of the same immutable evaluation,
not a new candidate or permission to tune after seeing results.

Optimization, bounded forward PAPER and live execution remain unauthorized.
