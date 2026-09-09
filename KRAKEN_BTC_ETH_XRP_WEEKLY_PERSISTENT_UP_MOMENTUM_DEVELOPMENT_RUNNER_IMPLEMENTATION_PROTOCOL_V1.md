# Kraken BTC/ETH/XRP Weekly Persistent-UP Momentum Development Runner Implementation Protocol v1

## Status

`KRAKEN_WEEKLY_PERSISTENT_UP_MOMENTUM_DEVELOPMENT_RUNNER_IMPLEMENTED_NO_RUN_AUTHORIZATION`

Protocol ID:
`kraken-btc-eth-xrp-weekly-persistent-up-momentum-development-runner-implementation-v1`.

This milestone implements the runner design frozen at Git commit
`0b51b8455f218793605cc6da086862e96776e50d`. Tests use only generated
in-memory rows and temporary synthetic ZIP files. The real Kraken archive is
not located or opened, no real weekly bar or outcome is produced, and no
Development execution is authorized.

## Hash-bound reader

Production accepts only `Kraken_OHLCVT.zip`, exactly `7885068519` bytes with
SHA-256
`e6ab4a3d2fe3be99167607fa28f230a84a038ad3ea3348ef81dc4bffcabb758d`.
It requires one unique unencrypted member basename for each of
`XBTUSD_1440.csv`, `ETHUSD_1440.csv` and `XRPUSD_1440.csv`.

The reader hashes all archive and selected-member bytes. It parses every
member timestamp only for ordering and partition selection. OHLCVT fields are
decoded and validated only inside Development
`[2019-01-01T00:00:00Z, 2024-04-01T00:00:00Z)`. Later values remain opaque.

Development rows must use the exact seven-column source schema, UTC-midnight
integer timestamps, exact finite decimal OHLCV and positive integer Trades.
The full-grid subtraction must equal the frozen 1,916 BTC, 1,917 ETH and 1,915
XRP observations and the exact three provider-missing dates. There is no fill,
repair, resampling, alternate source or network fallback.

## Trusted adapter and parity

The private trusted adapter is callable by production only after the runner
has checked the exact one-shot phrase, external paths, source archive identity
and members. It maps validated decimal text directly into the already frozen
weekly engine primitives. It never passes or accepts the synthetic engine's
authorization token.

Tests compare the trusted adapter with the public synthetic engine on identical
generated rows after removing mode/status naming. Exact aggregation, invalid
weeks, gap reset, state, actions, boundaries and cost-profile arithmetic must
match. The adapter adds no signal, threshold, parameter, ranking or model.

## Gate evaluator

The evaluator consumes only trusted adapter decisions. A valid gate event must
be `LONG` and have both `t+1` and `t+2` Open boundaries within Development.
Invalid future boundaries remain counted diagnostics but never enter support
or arithmetic means.

For each rule and asset it records valid/invalid counts, overall baseline and
stress means and all five slice summaries. For the primary it also records the
largest positive baseline event share and the seven frozen asset gates. Empty
means are JSON `null`. Decimal inputs remain exact and output is canonical
non-exponential text.

The cross-asset result requires at least two assets passing every gate and the
primary rule strictly beating both controls on at least two assets. A pass is
only Development interest requiring human review. Failure is terminal
`HOLD_CASH` for this exact hypothesis. Both outcomes keep Candidate v2 false.

## One-shot evidence

The exact future production phrase remains:

`EXECUTE_KRAKEN_WEEKLY_PERSISTENT_UP_MOMENTUM_DEVELOPMENT_ONCE`.

It is declared inactive in this milestone. The production method checks the
phrase before opening any path. Archive, evidence root and Git project must be
distinct; evidence remains external. Existing final or staging directories
block the run.

The runner writes exactly four files under staging:

- canonical report JSON and binary-LF SHA-256 sidecar; and
- canonical decisions JSON and binary-LF SHA-256 sidecar.

The final directory appears only through atomic rename. A failed staging
directory is preserved for incident review. There are no model artifacts.

The independent reader requires the exact file set, validates both sidecars,
all frozen identities, negative authorization flags and the decisions digest,
then recomputes every summary and gate from the recorded decisions. It never
opens the source archive, uses a network, writes evidence or authorizes a next
stage.

## Current safety boundary

The code surfaces are implemented, but this milestone records all as false:

- authorization phrase active;
- real source/archive or Development values opened;
- real weekly aggregation and outcomes generated;
- Development gates or Development run executed;
- model training or parameter/threshold search;
- Calibration or Evaluation opened;
- Candidate v2 or automatic selection;
- PAPER, cloud, real orders or live execution.

After focused/static and full Windows regression pass, the next possible stage
is `SEPARATE_READ_ONLY_DEVELOPMENT_PREFLIGHT_DECISION`. A preflight may hash
and inspect only source metadata necessary to prove readiness; it may not parse
market values, aggregate weeks or execute Development. The one real run still
requires a later exact operator authorization.
