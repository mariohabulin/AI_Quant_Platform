# Kraken AI-Driven V2 Derivatives Context Dataset Lock Attempt 4 Reader Incident

## Execution result

Dataset Lock Recovery Attempt 4 was executed once from commit
`40b5943442c96d5ef26434db95d9dc955ca41c12`. It revalidated the 695-object
Attempt 3 prefix and downloaded the remaining 2,113 frozen public objects.

- run exit code: `0`;
- elapsed time: `728.63` minutes;
- object count: `2808`;
- normalized file count: `12`;
- verified-resume object count: `695`;
- public-download object count: `2113`;
- exact open-interest zero sentinels: `399`;
- final Attempt 4 lock: present;
- Attempt 4 staging: absent after atomic publication;
- Attempts 1, 2 and 3 staging counts: unchanged at `226`, `360` and `1390`;
- labels generated: false;
- model training executed: false;
- Calibration and Evaluation opened: false;
- Candidate v2 and real orders authorized: false.

The immutable final manifest SHA-256 is
`db4dde045d9fce22bee1389fe8c7ad13d3e3ccc5e5c4ace7c433f5461ba11916`.
Attempt 4 acquisition succeeded and its authorization is consumed. The lock
must not be downloaded again, rewritten or replaced.

## Independent-reader failure

The subsequent read-only review verified the manifest identity and sidecar,
the frozen object registry, acquisition origins, all prior staging inventories,
every raw ZIP and official checksum, every source schema and all twelve
normalized file hashes. It then failed while constructing the funding frame.

Pandas inferred a single second-resolution format from the first normalized
timestamp and rejected a later valid ISO-8601 timestamp containing fractional
seconds, for example `2021-12-01T16:00:00.001000Z`.

This is a local reader-compatibility defect. It is not a source, checksum,
manifest, chronology, causal-alignment, model or strategy failure. The final
dataset remains immutable and no acquisition recovery attempt is required.

## Frozen read-only correction

The independent reader must parse every normalized timestamp column with the
explicit pandas `ISO8601` format and UTC conversion. This supports the already
validated canonical forms with or without fractional seconds while continuing
to reject malformed timestamps.

The correction applies consistently to funding timestamps, open-interest
timestamps, mark/index open timestamps and mark/index close timestamps. It
does not alter any normalized byte, timestamp, value, hash, manifest or source
rule.

After tests, static source binding and a new commit, the existing Attempt 4
final lock may be reviewed again read-only using its recorded manifest hash.
That review requires no acquisition authorization, performs no network fetch,
and may not generate labels or fit a model. Only a successful independent
reader result may permit implementation of the frozen context-learning runner.
