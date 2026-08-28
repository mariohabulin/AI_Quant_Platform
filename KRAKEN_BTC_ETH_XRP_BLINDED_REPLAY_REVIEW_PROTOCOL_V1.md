# Kraken BTC/ETH/XRP Bounded Blinded Replay Review Protocol v1

## Status

`METHODOLOGY_REVIEWED_PREFLIGHT_NOT_EXECUTED`

This protocol reviews how the locked Kraken daily dataset may later be used for
bounded human hypothesis reconstruction without hindsight. It does not execute
a real replay, define a crypto strategy, calculate performance, select a
parameter or authorize Candidate v2, PAPER, cloud or live execution.

## Frozen inputs

- protocol ID:
  `kraken-btc-eth-xrp-bounded-blinded-replay-review-v1`;
- dataset ID:
  `kraken-spot-btc-eth-xrp-native-1d-20190101-20260401-archive-only-v2`;
- dataset manifest SHA-256:
  `8c91b42f2bc0c16a0ef0c6b4373572ac53fbf7f5937d4ebbbe75a0d39483df1c`;
- dataset-lock evidence normalized SHA-256:
  `cd83822005525381024f0cd90130f34246ec609a90436c714b79633daed82184`;
- replay component normalized SHA-256:
  `9aa103e0cb8c1cb48479eb6b6d7357884cb6a3373b04613d9461d779fc0972a0`;
- durable replay-evidence component normalized SHA-256:
  `2341e3f7da6086565caf537df61df9410dfb6f6931944d1923122822ec103bf5`;
- source mode: `OFFICIAL_OHLCVT_ARCHIVES_ONLY`;
- assets, in exact order: `BTC-USD`, `ETH-USD`, `XRP-USD`;
- interval: provider-native completed `1440` minutes;
- participant position state at every episode start: `FLAT`;
- evidence role: `INSPECTED_HYPOTHESIS_RECONSTRUCTION_ONLY`.

The historical Coinbase-bound replay protocol remains immutable evidence of an
earlier provider-audit-required boundary. It is not silently rewritten into the
Kraken production review.

## Reviewed deficiencies and resolution

The existing replay primitive already hides future bars from its public view,
returns defensive copies, requires one reasoned decision before advancing,
constrains actions by position state and emits no performance. A real replay
was nevertheless blocked because the old declaration did not bind the Kraken
lock, decisions existed only in memory, provider gaps had no explicit position
policy and no bounded price-independent episode selection was frozen.

This protocol resolves those deficiencies before any real chart is shown:

1. the exact Kraken manifest is independently re-locked;
2. only complete continuous availability segments may supply an episode;
3. episode selection uses manifest identity and availability only;
4. every decision is durably written before the next bar can appear;
5. every episode is independent and starts `FLAT`;
6. an open terminal position remains explicitly unresolved;
7. no synthetic exit, cross-gap carry or performance result is created.

## Bounded episode catalog

The first real replay review, if later authorized, contains exactly three
episodes: one for each frozen asset. Every episode has exactly:

- 30 initial visible context bars;
- 60 sequential decision bars, including the context-ending bar;
- 89 distinct provider-native daily rows in its rolling views;
- one decision for each of the 60 decision timestamps;
- no missing timestamp inside the episode;
- no revealed episode end, remaining-bar count or future timestamp.

`BlindedDailyReplaySession` therefore receives 89 continuous rows with
`context_bars=30`. Its first view ends on row 30 and its sixtieth and final view
ends on row 89.

## Price-independent selection

For each asset, the preflight enumerates every 89-row candidate window that is
fully contained within one manifest-recorded continuous availability segment.
Candidates are ordered by UTC start timestamp. No OHLCV value, return, volume
event, drawdown or manually identified market episode enters selection.

The selected candidate index is:

`integer(SHA256(protocol_id + "|" + manifest_sha256 + "|" + asset)) mod candidate_count`

The canonical three-asset schedule is hashed for evidence, but review-mode and
preflight CLI output must not reveal selected timestamps, segment ordinals,
remaining counts or future endpoints to the participant. Any change to the
dataset, protocol identity, asset or availability segments changes the
selection evidence.

## Gap and terminal-position policy

The locked provider-native gaps remain:

- BTC: `2024-03-31T00:00:00Z`;
- ETH: none;
- XRP: `2022-05-11T00:00:00Z` and `2022-05-12T00:00:00Z`.

No selected episode may cross one of these boundaries. Episodes never carry a
position into another episode. If the final decision leaves the state `LONG`,
the evidence records `OPEN_POSITION_UNRESOLVED_AT_EPISODE_END`; it never
invents an exit price, closing trade or return. A `FLAT` terminal state records
`FLAT_AT_EPISODE_END`.

## Durable decision evidence

The participant may receive only `BlindedReplayView`: asset, current sequence,
current completed timestamp, position state and the trailing 30-bar defensive
copy. Each decision binds the exact-decimal canonical SHA-256 of those visible
bars.

Before `advance()` can reveal another bar, a durable journal must write a new
exclusive canonical JSON decision file and SHA-256 sidecar. Every record binds
the dataset, protocol, asset, episode, sequence, prior decision hash, reason,
position transition and visible-frame hash. Decision files contain no future
bars or performance fields.

A completed episode atomically promotes one final canonical evidence manifest
and sidecar. Existing final or incomplete staging evidence blocks automatic
overwrite or retry. Source data, future bars, P&L, benchmark, drawdown and
parameter ranking are never copied into replay evidence.

An independent evidence lock reopens the final manifest, every decision and
every sidecar; it revalidates canonical bytes, exact identity, file order,
sequence, the prior-decision hash chain, terminal-position resolution and every
non-performance safety flag.

## Preflight boundary

Preflight may independently re-lock the dataset, reproduce availability
segments, confirm every candidate episode is continuous and compute only the
sealed schedule SHA-256. It does not construct a participant view, request a
decision or execute a real chart replay.

Preflight must fail closed for any manifest mismatch, source-evidence mismatch,
asset/hash mismatch, unexpected gap, changed segment, insufficient episode
length, noncausal selection field or replay-protocol hash drift.

## Reviewed execution sequence

1. Integrate the protocol, deterministic selection, durable journal and tests.
2. Reproduce focused and complete Windows tests.
3. Run review mode with every execution and authorization flag false.
4. Run one preflight against the exact external locked Kraken dataset.
5. Review only counts, hashes and safety flags; do not expose schedule dates.
6. Record compact preflight evidence in Git.
7. Separately decide whether one supervised three-episode real replay may run.

## Authorization state

- data acquisition executed by this boundary: `false`;
- all-asset dataset previously locked: `true`;
- preflight executed: `false`;
- real chart replay authorized: `false`;
- real chart replay executed: `false`;
- crypto strategy implemented: `false`;
- performance evaluation executed: `false`;
- optimization authorized: `false`;
- Candidate v2 authorized: `false`;
- bounded forward PAPER authorized: `false`;
- cloud execution authorized: `false`;
- live execution authorized: `false`.
