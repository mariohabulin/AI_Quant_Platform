# Kraken BTC/ETH/XRP AI-Driven v2 Development Runner Protocol v1

## Status

`AI_DRIVEN_V2_DEVELOPMENT_RUNNER_REVIEWED_SYNTHETIC_TESTS_ONLY`

This protocol prepares one evidence-locked execution of the frozen AI-driven
v2 reference-A path on `DEVELOPMENT` only. Preparation and review do not open
the external dataset, execute performance or authorize the run. Calibration
and evaluation remain inaccessible.

## Frozen identity chain

- protocol ID:
  `kraken-btc-eth-xrp-ai-driven-v2-development-runner-v1`;
- run ID:
  `kraken-btc-eth-xrp-ai-driven-v2-development-reference-a-v1`;
- dataset ID:
  `kraken-spot-btc-eth-xrp-native-1d-20190101-20260401-archive-only-v2`;
- dataset manifest SHA-256:
  `8c91b42f2bc0c16a0ef0c6b4373572ac53fbf7f5937d4ebbbe75a0d39483df1c`;
- partition protocol ID:
  `kraken-btc-eth-xrp-ai-driven-v2-partition-v1`;
- state parameter set: `kraken-ai-v2-ccvr-reference-a-v1`;
- risk/execution policy:
  `kraken-ai-v2-risk-execution-reference-a-v1`;
- cost profile: `kraken-tier1-taker-adverse-20260829-v1`;
- exact authorization phrase:
  `EXECUTE_KRAKEN_AI_V2_DEVELOPMENT_REFERENCE_A_ONCE`.

The nonexecuting review hash-binds the exact feature, state, risk/execution,
partition and development-runner protocols and components. Any changed byte
requires a new reviewed binding before execution.

## Development-only visibility

The only permitted OHLCV window is:

- start: `2019-01-01T00:00:00Z` inclusive;
- end: `2024-04-01T00:00:00Z` exclusive;
- role: `INSPECTED_DEVELOPMENT_ONLY`.

Expected parsed rows are BTC `1916`, ETH `1917` and XRP `1915`. The BTC gap on
`2024-03-31T00:00:00Z` and XRP gaps on `2022-05-11T00:00:00Z` and
`2022-05-12T00:00:00Z` remain absent. Continuous segment lengths must be BTC
`1916`, ETH `1917` and XRP `1226, 689`.

The reader verifies the complete canonical manifest, inventory and each full
asset file by SHA-256. Full asset bytes beyond development are handled only as
opaque hash input. It may inspect the timestamp token needed to identify the
first excluded row, but it must not parse, convert, retain or expose any
calibration/evaluation OHLCV value.

The first opaque timestamp for every asset must be exactly
`2024-04-01T00:00:00Z`. Exactly 730 locked rows per asset remain opaque: 365
calibration rows and 365 sealed evaluation rows. The runner must report:

- calibration rows parsed: `0`;
- evaluation rows parsed: `0`;
- calibration data opened: `false`;
- evaluation data opened: `false`.

No complete-data `KrakenDailyDatasetLock` object may be used by this runner,
because that loader converts all locked rows into values. Opaque byte hashing
is provenance verification and does not create a market-data view.

## Frozen research capital and ordering

Initial capital is `5000.00` in `USD_RESEARCH_NOTIONAL`. It is not a claim
about an actual account balance or EUR/USD conversion. Venue minimum sizes,
order-book depth, partial fills, outages and an operator account fee tier remain
unverified; therefore every fill remains synthetic.

Assets share one cash balance, one marked equity value, one total open-risk
budget and one concurrent-position count. When events share a UTC timestamp,
the phase order is:

1. existing-position open exits;
2. pending entries in fixed `BTC-USD`, `ETH-USD`, `XRP-USD` order;
3. active-position intrabar protection;
4. completed-bar exit scheduling;
5. adverse close liquidation mark.

All existing open exits are resolved before a new entry sees equity, cash,
open risk or position count. Same-timestamp entry order is identity, not a
ranking. Each approved entry immediately reduces shared cash by adverse buy
fill plus commission. Every synthetic exit credits adverse sell proceeds net
of commission.

Portfolio equity used for sizing and daily diagnostic marks equals cash plus
the net proceeds that would remain after adverse sell slippage/spread and
commission at the contemporaneously available open or completed close. This is
a conservative valuation mark, not an executed liquidation.

## Causal state and execution path

Each continuous asset segment independently invokes the frozen feature/state
path with empty warmup and initial `FLAT` state. No measurement, event anchor,
state age, intent or position crosses a recorded gap.

An `ENTER_NEXT_OPEN` intent can be considered only on the immediately following
calendar-day open inside development. A missing following open cancels the
intent as `FOLLOWING_OPEN_UNAVAILABLE_AT_RECORDED_GAP`. A following open at or
after `2024-04-01T00:00:00Z` is outside scope and cannot be read.

The risk adapter retains its exact following-open, gap, fixed setup-low stop,
cost-aware causal `3R`, cash, position-risk, total-risk, position-cap,
entry-bar protection, stop-first conflict and 20-completed-bar rules. A signal
state is not a synthetic position and a synthetic position is not a venue
order.

## Gap and terminal-position policy

If a position is active when its next expected calendar bar is provider-
unavailable, the complete portfolio run halts before any later row is
processed. The position remains
`OPEN_POSITION_UNRESOLVED`; the status is
`KRAKEN_AI_V2_DEVELOPMENT_INCONCLUSIVE_OPEN_POSITION_AT_GAP`. No price is
invented, no earlier close is reinterpreted as an executable exit and no state
or capital crosses the gap.

At the development boundary, an open position is also preserved unresolved.
Its last completed development close may supply a separately labeled adverse
liquidation mark for diagnostic equity, but no synthetic terminal exit, trade
or realized P&L is created. A final pending entry intent is canceled because
the required following open lies outside development.

The run status is one of:

- `KRAKEN_AI_V2_DEVELOPMENT_COMPLETED_FLAT`;
- `KRAKEN_AI_V2_DEVELOPMENT_COMPLETED_WITH_UNRESOLVED_TERMINAL_POSITION`;
- `KRAKEN_AI_V2_DEVELOPMENT_INCONCLUSIVE_OPEN_POSITION_AT_GAP`.

## Frozen evidence

The external evidence root must be outside the repository, outside the dataset
directory and non-overlapping with it. The one-shot final directory is
`development_reference_a_v1`; incomplete writes remain under
`.development_reference_a_v1.staging` for incident review. Existing final or
staging evidence blocks overwrite, retry and automatic resume.

The canonical report and SHA-256 sidecar record:

- all frozen IDs, component configuration and source hashes;
- exact parsed/opaque row counts and segment lengths;
- state transition counts per asset;
- approved, rejected and canceled entry evidence;
- closed synthetic trade ledger and exit-reason counts;
- realized cash/P&L, modeled commissions and adverse marked equity/drawdown;
- maximum concurrent positions and planned open-risk fraction;
- unresolved terminal positions without fabricated exit;
- every data-access, execution and authorization safety flag.

After atomic promotion, `KrakenAIDrivenV2DevelopmentEvidenceLock` must reread
the canonical bytes, sidecar, complete frozen identity/configuration and all
non-promotion flags. The runner may report success only after that independent
lock passes.

Raw source OHLCV rows and the daily equity curve are not persisted. The trade
ledger is development evidence, not calibration/evaluation evidence or a live
track record.

## One-shot authorization boundary

After Windows regression, hash-bound review, commit and push, a separate
operator decision may authorize exactly one run by supplying the exact phrase.
Wrong or absent authorization must touch neither dataset nor evidence paths.

This protocol and its implementation do not themselves authorize execution.
At local review:

- external dataset opened: `false`;
- development data opened: `false`;
- calibration data opened: `false`;
- evaluation data opened: `false`;
- development performance executed: `false`;
- parameter sweep executed: `false`;
- development run authorized: `false`.

## Non-promotion boundary

The report observes one exact reference configuration. It performs no
parameter sweep, automatic ranking, strategy selection or automatic promotion.
No result by itself authorizes calibration, sealed evaluation, optimization,
Candidate v2, bounded forward PAPER, cloud deployment or live execution.

After the run, its canonical report must be independently reviewed and closed.
Only a separate decision may reject reference A, design a newly identified
development hypothesis, or propose a calibration protocol. Evaluation remains
sealed behind its later one-time authorization.
