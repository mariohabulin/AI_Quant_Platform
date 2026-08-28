# Kraken BTC/ETH/XRP Supervised Blinded Replay Protocol v1

## Status

`SUPERVISED_REPLAY_METHOD_REVIEWED_NOT_AUTHORIZED`

This protocol prepares one bounded human-supervised replay path from the exact
sealed Kraken preflight. It does not authorize or execute a real chart replay,
define a crypto strategy, calculate performance, select parameters or authorize
Candidate v2, PAPER, cloud or live execution.

## Frozen inputs

- execution protocol ID:
  `kraken-btc-eth-xrp-supervised-blinded-replay-v1`;
- selection protocol ID:
  `kraken-btc-eth-xrp-bounded-blinded-replay-review-v1`;
- dataset ID:
  `kraken-spot-btc-eth-xrp-native-1d-20190101-20260401-archive-only-v2`;
- dataset manifest SHA-256:
  `8c91b42f2bc0c16a0ef0c6b4373572ac53fbf7f5937d4ebbbe75a0d39483df1c`;
- sealed selection schedule SHA-256:
  `3e805044356777f0bdfa2901db267d714c1e14d11415dd4686acaaaed92f1042`;
- preflight-evidence normalized SHA-256:
  `ca5958b01370c222efd28c5149bb7a04e7627e0b71eef720db73116c7ccdfdf3`;
- source mode: `OFFICIAL_OHLCVT_ARCHIVES_ONLY`;
- asset order: `BTC-USD`, `ETH-USD`, `XRP-USD`;
- episodes: one per asset, three total;
- episode rows: `89`;
- initial visible context: `30` completed daily bars;
- decisions: `60` per episode;
- one-episode operator authorization phrase:
  `AUTHORIZE_ONE_KRAKEN_BLINDED_REPLAY_EPISODE_V1`;
- evidence role: `INSPECTED_HYPOTHESIS_RECONSTRUCTION_ONLY`.

The dataset-lock evidence, replay-review protocol, sealed-preflight evidence,
causal replay component and durable evidence component are all exact-hash
preconditions. A mismatch fails before the external dataset is opened.

## Explicit authorization boundary

Review mode is the default and accesses no dataset. Real replay may begin only
after the implementation is integrated, focused and complete tests pass, the
review declaration is inspected and the operator separately supplies the exact
one-episode authorization phrase.

The authorization applies to only the next chronological asset episode. It is
not reusable authorization for all three assets, performance evaluation, a
strategy, Candidate v2, PAPER, cloud or live execution.

## One episode per invocation

The evidence root enforces the frozen asset order. A fresh root permits only
BTC. A valid completed BTC episode permits only ETH; valid BTC and ETH permit
only XRP. Every existing episode is independently re-locked before another can
begin. Skipped assets, changed identities, unexpected files, incomplete
staging, tampered evidence or an already completed catalog fail closed.

Only one 60-decision episode may run per invocation. This provides a clean
review and rest boundary between assets without allowing the participant to
choose an attractive asset or historical period.

## Causal participant view

The runner independently re-locks the dataset, recomputes the availability-only
catalog and requires the exact sealed schedule SHA-256 before constructing a
view. It then selects the next episode from timestamps only and passes its 89
rows to the frozen `BlindedDailyReplaySession`.

The participant sees only:

- the current asset;
- the current sequence and completed UTC timestamp;
- current position state and allowed action set;
- the trailing 30 completed OHLCV bars in an in-memory candlestick/volume
  chart.

The chart is updated in memory and is not written to disk. It contains no
future bar, episode endpoint, remaining-bar field, return, P&L, benchmark,
drawdown, indicator, signal or parameter recommendation.

## Decisions and evidence ordering

While `FLAT`, only `ENTER` or `SKIP` is accepted. While `LONG`, only `EXIT` or
`HOLD` is accepted. Every action requires a nonempty contemporaneous reason.
The exact-decimal visible-frame SHA-256 binds the decision to what was visible.

The durable journal must exclusively write canonical decision JSON, its
SHA-256 sidecar and the prior-decision hash before replay state changes or the
next completed bar appears. The sixtieth decision finalizes the episode; a
separate lock immediately revalidates the final manifest, every decision,
every sidecar, sequence, timestamp continuity, position chain and safety flag.

Every episode begins `FLAT`. A terminal `LONG` remains
`OPEN_POSITION_UNRESOLVED_AT_EPISODE_END`; no synthetic exit or cross-episode
position carry is permitted.

## Interruption policy

The operator must begin an episode only when enough uninterrupted time is
available for all 60 decisions. Keyboard interruption, process failure, chart
failure, input failure or durable-write failure leaves the exclusive staging
evidence in place and blocks automatic overwrite, retry or resume. Recovery
requires a separate incident review; the runner never deletes or silently
repairs incomplete evidence.

## Three-episode catalog

After the third episode, the runner independently re-locks all three episode
directories and atomically writes one canonical catalog and checksum. The
catalog binds exact dataset and protocol identity, sealed schedule hash, asset
order, episode evidence hashes, decision counts and terminal resolutions.

The catalog stores no OHLCV source rows, chart image, return, P&L, benchmark,
drawdown, ranking or selected parameter. Catalog completion closes inspected
hypothesis reconstruction only; any strategy definition remains a later new
pre-registration boundary.

## Reviewed execution sequence

1. Integrate this protocol, runner, catalog lock and synthetic tests.
2. Reproduce focused and complete Windows tests.
3. Commit and push the reviewed implementation before any chart is shown.
4. Run review mode and inspect only bindings and authorization flags.
5. Separately authorize exactly the next one-asset episode.
6. Complete and independently lock all 60 decisions without interruption.
7. Review compact episode evidence before authorizing the next asset.
8. After all three assets, independently re-lock the final catalog.
9. Record compact completion evidence in Git without OHLCV or performance.

## Authorization state

- sealed preflight completed: `true`;
- supervised replay review eligible: `true`;
- real replay authorized: `false`;
- real chart replay executed: `false`;
- crypto strategy implemented: `false`;
- performance evaluation executed: `false`;
- optimization authorized: `false`;
- Candidate v2 authorized: `false`;
- bounded forward PAPER authorized: `false`;
- cloud execution authorized: `false`;
- live execution authorized: `false`.
