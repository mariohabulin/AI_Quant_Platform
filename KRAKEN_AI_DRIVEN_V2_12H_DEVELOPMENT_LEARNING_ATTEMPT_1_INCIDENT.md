# Kraken AI-Driven V2 12h Development Learning Attempt 1 Incident

## Immutable attempt identity

- attempt: `1`;
- execution commit: `cc8ae44c45d41182af3bc91ee21cf075e65011b5`;
- runner protocol:
  `kraken-btc-eth-xrp-ai-driven-v2-12h-development-learning-runner-v1`;
- authorized partition: `DEVELOPMENT` only;
- authorized resolution: Kraken native `12h`;
- source archive SHA-256:
  `e6ab4a3d2fe3be99167607fa28f230a84a038ad3ea3348ef81dc4bffcabb758d`.

## Observed terminal state

The separately authorized Attempt 1 exited with code `1` while reading row 1
of `master_q4/XBTUSD_720.csv`:

`RuntimeError: 12h source row must contain eight columns`

After the failure:

- final evidence existed: `false`;
- staging evidence existed: `true`;
- worktree remained clean: `true`;
- retry was explicitly prohibited: `true`.

The staging marker at
`.v2_12h_development_learning_v1.staging` must remain preserved under the
Attempt 1 evidence root. It is not successful learning evidence and must not be
renamed, deleted, reused or treated as a completed run.

## Failure boundary

The runner validated the complete archive filename, byte size and SHA-256, then
opened the required BTC 12h member. It rejected the first row on column count
before parsing that row's OHLCV values.

Therefore Attempt 1 produced no:

- Development frame;
- causal feature;
- triple-barrier label;
- class-support result;
- fitted model;
- out-of-fold prediction;
- performance conclusion; or
- Candidate authorization.

Calibration and Evaluation remained unopened. No PAPER, cloud, order or live
operation occurred.

## Root cause

The new 12h runner and its synthetic ZIP fixture assumed this eight-field row:

`Unix time, Open, High, Low, Close, VWAP, Volume, Trades`

That assumption contradicted the already reviewed provider parser and
`KRAKEN_BTC_ETH_XRP_DAILY_DATASET_LOCK_PROTOCOL_V2.md`, which freeze the
official Kraken archive row as exactly seven fields:

`Unix time, Open, High, Low, Close, Volume, Trades`

The production source behaved according to the existing seven-column
contract. The defect was in the new adapter and test fixture, not in the Kraken
archive and not in the Learning Core.

## Recovery rule

Recovery requires all of the following before any new real-data attempt:

1. parse exactly seven fields and read Volume from field 6 and Trades from
   field 7 when counting from one;
2. validate positive integer Trades on every Development row;
3. preserve non-Development value-column opacity;
4. replace the eight-column synthetic fixture with the frozen seven-column
   format and add an explicit eight-column rejection regression;
5. bind the corrected runner and this incident document by SHA-256;
6. require the unchanged Attempt 1 staging directory as a recovery precondition;
7. use a new evidence root for Attempt 2; and
8. require a new one-shot recovery authorization phrase.

Attempt 1 authorization is consumed. It cannot be reinterpreted as permission
for Attempt 2.
