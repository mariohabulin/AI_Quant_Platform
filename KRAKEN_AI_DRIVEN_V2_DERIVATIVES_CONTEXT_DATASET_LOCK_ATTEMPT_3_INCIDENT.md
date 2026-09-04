# Kraken AI-Driven V2 Derivatives Context Dataset Lock Attempt 3 Incident

## Scope

Dataset Lock Recovery Attempt 3 was the single authorized Development-only
acquisition run executed from commit
`25d55b695740045697d8d835698e2bf3016e8fc6`. It could only download, verify,
normalize and atomically lock the frozen 2,808 Binance USD-M context objects.
It did not authorize labels, model training, Calibration, Evaluation,
Candidate v2, PAPER or orders.

## Recorded execution result

- run exit code: `1`;
- elapsed time: `39.07` minutes;
- last emitted progress marker:
  `675/2808|OPEN_INTEREST_METRICS|BTC-USD|2023-07-14`;
- first missing registry object: `696`,
  `BTCUSDT-metrics-2023-08-04.zip`;
- exception: DNS `getaddrinfo failed` while resolving `data.binance.vision`;
- final Attempt 3 dataset: absent;
- Attempt 3 staging: present and preserved;
- prior Attempt 1 and Attempt 2 staging counts: unchanged at `226` and `360`;
- repository content after failure: unchanged.

Attempt 3 consumed its authorization. It may not be rerun and its staging may
not be renamed, deleted or published as a final dataset.

## Read-only staging inventory

The post-incident scan parsed no market value and changed no file. It found:

- complete ZIP/checksum pairs: `695`;
- partial pairs: `0`;
- missing registry objects: `2113`;
- ZIP files: `695`;
- checksum files: `695`;
- normalized files: `0`;
- manifest or sidecar: absent;
- total staging files: `1390`;
- total staging bytes: `7317431`;
- staging inventory SHA-256:
  `8de82f8905358c79f3e0cb609f8b8ecd782e32e02497e9ef784e85b528aa63dd`;
- last complete object: `695`,
  `BTCUSDT-metrics-2023-08-03.zip`;
- first missing object: `696`,
  `BTCUSDT-metrics-2023-08-04.zip`;
- DNS resolution after the incident: available.

The 695 complete pairs form one exact contiguous prefix of the frozen registry.
No incomplete object, normalized output or manifest exists in Attempt 3
staging.

## Root cause

The reader successfully passed the prior optional-blank and exact `0E-8`
sentinel corrections. The failure was a transient transport/DNS outage after
three short retries, not a checksum, schema, timestamp, source-value, model or
strategy failure.

The previous recovery design always downloaded the whole registry into a new
root and could not safely resume already verified work. That is inadequate for
5,616 public HTTP fetches and is the process defect corrected for Attempt 4.

## Frozen recovery rule for a possible Attempt 4

Attempt 4 must use a new root and preserve Attempts 1, 2 and 3. Before reuse it
must require the exact Attempt 3 file count, byte count, inventory hash and
contiguous 695-object file set. Every cached ZIP and checksum must then pass the
same official checksum, safe-member, exact-schema, chronology, period and
source-value validation as a newly downloaded object.

Only those 695 fully revalidated pairs may be copied into the new staging.
Objects 696 through 2,808 must be fetched from the frozen public registry and
fully validated. Transport retries use bounded exponential backoff. A continued
outage still fails closed and preserves the new staging.

No partial file is trusted, no source validation is skipped and no prior
staging is modified. The final manifest must distinguish 695 verified-resume
objects from 2,113 newly downloaded objects and record all three prior staging
inventories. Attempt 4 requires a new commit, preflight, root and explicit
one-shot operator authorization. This incident record does not authorize it.
