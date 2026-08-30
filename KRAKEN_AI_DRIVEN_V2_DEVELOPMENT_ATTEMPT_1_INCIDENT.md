# Kraken AI-Driven v2 Development Attempt 1 — Numeric Type Incident

## Incident record

- Date: `2026-08-30`
- Development-runner commit: `5054da1`
- Run ID: `kraken-btc-eth-xrp-ai-driven-v2-development-reference-a-v1`
- Dataset ID:
  `kraken-spot-btc-eth-xrp-native-1d-20190101-20260401-archive-only-v2`
- Dataset manifest SHA-256:
  `8c91b42f2bc0c16a0ef0c6b4373572ac53fbf7f5937d4ebbbe75a0d39483df1c`
- Outcome classification: `TECHNICAL_NUMERIC_TYPE_INTEGRATION_FAILURE`

## What happened

The operator separately authorized one development-only reference-A attempt.
The runner revalidated the locked manifest and full asset-file hashes, parsed
only the development prefix and began the frozen causal state/execution path.
At the first eligible entry, the risk adapter rejected the signal `Close` with
`TypeError: Signal close must be numeric.`

The canonical CSV reader deliberately used `Decimal` while validating finite
OHLCV values and price geometry. It then retained those objects in a Pandas
frame. Synthetic runner tests had supplied `float` frames, while the risk
adapter correctly required its established `numbers.Real` input contract.
The missing boundary was conversion from validated external decimal text to
the project's canonical internal `float64` OHLCV representation.

The exception occurred inside `execute_development()` before the evidence-root
creation, staging write or final atomic promotion path. The CLI printed no
performance result, report SHA-256 or strategy classification. Runtime
absence of final and staging evidence must still be confirmed before recovery.

## Evidence and knowledge boundary

Development data was opened for the authorized attempt. Full locked files were
hashed, while rows from `2024-04-01T00:00:00Z` onward remained opaque bytes;
calibration and evaluation OHLCV values were not parsed. No network request,
venue order, real fill, parameter sweep, ranking or promotion was executed.

Attempt 1 is a technical integration incident, not a completed development
result. It supports no conclusion about returns, drawdown, trades, reference-A
quality or Candidate v2 eligibility. Its authorization is consumed and cannot
be reused.

## Recovery boundary

Recovery is limited to one causal representation repair:

- retain `Decimal` validation of external canonical CSV text;
- emit validated reader frames as explicit `float64` OHLCV;
- add a real-reader-to-risk-adapter regression matching the failure;
- update the exact hash-bound runner review;
- run focused and complete regressions on local and Windows environments;
- commit and push the exact recovery before any recovery execution; and
- require a new separate operator authorization for one recovery attempt.

No dataset byte, manifest, partition, feature rule, state parameter, risk
limit, cost assumption, portfolio rule or evidence schema may change. Existing
final or staging evidence remains a hard retry blocker. Calibration, sealed
evaluation, optimization, Candidate v2, PAPER, cloud and live execution remain
unauthorized.
