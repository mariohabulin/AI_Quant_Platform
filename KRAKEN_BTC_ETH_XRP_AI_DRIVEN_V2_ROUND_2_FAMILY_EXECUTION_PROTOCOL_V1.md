# Kraken BTC/ETH/XRP AI-Driven v2 Round 2 Family Execution Protocol v1

## Status

`KRAKEN_AI_V2_ROUND_2_FAMILY_EXECUTION_IMPLEMENTED_DISCOVERY_RUNNER_REQUIRED`

Component ID:
`kraken-ai-v2-round-2-family-execution-v1`.

This synthetic-only milestone implements three exact family execution adapters
for the three immutable Round 2 hypotheses. An adapter may translate exact
causal `ENTER_NEXT_OPEN` evidence into a cost-aware research plan and model
protective or scheduled exits. It does not read a dataset, evaluate a route,
rank a strategy, select a winner or submit an order.

Round 1 remains closed against report SHA-256
`3ce14fda95f657c0b671b74c702d55ec4102da303e9e033ebaf0e02ff5c2fa9b`.
Its gates, routes and one-shot result cannot be changed by this component.
There is no Round 3 authorization and unused discovery capacity is not an
execution permission.

## Parent and configuration lock

Every adapter binds exact Round 2 configuration SHA-256
`2d591b048caa6ad123496b1ce1fcf4e523f924a9985737959d15cc8ddc1820c1`
from protocol
`kraken-btc-eth-xrp-ai-driven-v2-hybrid-discovery-round-2-v1` and accepts only
evidence emitted by component `kraken-ai-v2-round-2-causal-signals-v1`.

The exact family, route and execution identities are:

| Family | Asset scope | Execution contract |
| --- | --- | --- |
| `CAPITULATION_RECOVERY` | BTC, ETH, XRP | `kraken-ai-v2-r2-atr-capitulation-execution-v1` |
| `VOLATILITY_BREAKOUT` | BTC, ETH | `kraken-ai-v2-r2-breakout-retest-execution-v1` |
| `TREND_PULLBACK_CONTINUATION` | BTC, ETH | `kraken-ai-v2-r2-trend-macd-resumption-execution-v1` |

Each adapter verifies the exact hypothesis ID, confirmation transition,
feature availability, signal condition, `FLAT` post-signal state and
`ENTER_NEXT_OPEN` intent. XRP trend and breakout evidence returns
`NO_TRADE_HOLD_CASH`; retirement cannot be silently reversed. Unknown assets,
families and cross-family evidence fail closed.

## Timing and causal identity

Execution is modeled at the UTC-midnight day immediately following the signal.
No adapter reads that open before planning is explicitly invoked. The synthetic
position independently preserves the same signal-to-entry next-day identity.

Setup age must match the causal state machine:

- capitulation confirmation is two through seven completed days after setup;
- breakout confirmation is two through five completed days after breakout,
  and its setup low is the retained retest low; and
- trend confirmation is two through five completed days after pullback setup.

A completed position path must remain continuous at one-day steps from its
entry bar. A provider gap is an error, never an extra holding day or permission
to carry a position path across missing evidence.

## Frozen baseline and stress costs

The two unchanged Round 1 research profiles remain exact:

| Profile | Commission each side | Slippage each side | Full spread | Adverse price rate each side |
| --- | ---: | ---: | ---: | ---: |
| `kraken-tier1-taker-adverse-20260829-v1` | `0.80%` | `0.15%` | `0.30%` | `0.30%` |
| `kraken-tier1-taker-adverse-stress-r1-v1` | `0.80%` | `0.30%` | `0.60%` | `0.60%` |

Adverse rate is slippage plus half the full spread. Buy fill is
`raw open * (1 + adverse rate)` and sell fill is
`market reference * (1 - adverse rate)`. Commission applies to each adjusted
fill. Stress doubles only declared slippage and spread; it does not alter the
official Tier-1 taker commission assumption.

These research profiles do not establish current account tier, pair minimums,
partial fills, liquidity, executable spread or outage behavior.

## Shared safety envelope

Every adapter preserves the registered portfolio ceilings:

- current-equity risk per position is at most `0.50%`;
- total planned open risk is at most `1.50%` of current equity;
- at most three concurrent crypto positions;
- one asset may consume at most one third of current equity as notional;
- available cash is a hard sizing ceiling;
- cash-only, long-only and no leverage; and
- minimum cost-adjusted reward/risk is `3.0`.

Risk budget is the lower of `0.50%` current equity and remaining capacity under
the total-risk ceiling. Units are the minimum of net-risk size, remaining
per-asset notional size and available-cash size. A nonpositive result returns
`NO_TRADE_HOLD_CASH`.

The component accepts portfolio capacity as explicit causal input. It does not
allocate between routes or decide which eligible family deserves capital.

## Common entry gate order

Every adapter applies the following order:

1. exact family signal and valid setup timing;
2. registered asset scope;
3. concurrent-position capacity;
4. total-open-risk capacity;
5. per-asset notional capacity;
6. positive family stop below the raw open;
7. raw upward gap no greater than `signal close + 0.50 * prior ATR`;
8. positive cost-aware risk distance;
9. exact net cost-adjusted `3R` target; and
10. positive units under risk, notional and cash ceilings.

The inclusive upward-gap boundary is permitted; any amount above it fails.
Stops are never widened to admit a gap.

For one unit, entry cash is adverse buy fill plus entry commission. Stop
proceeds are adverse sell fill at the trigger minus exit commission. Net risk
is entry cash minus stop proceeds. Target reference is solved so adverse target
proceeds minus entry cash equal exactly three times that net risk.

## ATR-normalized capitulation execution

The stop is the retained running setup low minus `0.25` signal-time prior ATR.
The target is exact net cost-adjusted `3R`. Maximum hold is 25 completed bars,
counting the entry bar.

After open and intrabar protection survive, a completed close below the causal
prior 10-close low schedules a following-open structural exit. The closed
Reference-A resistance-room gate is not restored.

## Breakout-retest continuation execution

The stop is the retained retest low minus `0.25` signal-time prior ATR. It does
not reuse the Round 1 `max(structural stop, open minus 2 ATR)` branch. The target
is exact net cost-adjusted `3R` and maximum hold is 60 completed bars.

A completed close below the causal prior 10-close low schedules a
following-open structural exit. The breakout level is signal-state evidence,
not a mutable trailing stop or an alternate direct-breakout entry.

## Multi-bar MACD trend-resumption execution

The stop is the retained pullback low minus `0.25` signal-time prior ATR. The
target is exact net cost-adjusted `3R` and maximum hold is 40 completed bars.

A completed close below the causal prior EMA-50 schedules a following-open
structural exit. MACD is an entry-confirmation mechanism only; it does not
create a new intrabar exit, trailing target or runtime-mutating policy.

## Protective and scheduled execution

Open priority is stop gap, target gap, scheduled exit, hold. A stop gap sells
from the adverse raw-open reference. A target gap receives no favorable open
improvement and sells from the frozen target reference. A scheduled structural
or maximum-hold exit may use raw open only when neither protective gap exists.

Intrabar priority is stop touch, target touch, hold. Entry-bar protection is
mandatory and a same-bar stop/target conflict is `STOP_FIRST`. Every modeled
sell applies the selected adverse rate and taker commission.

After a surviving completed bar, bars held increments and the adapter evaluates
the exact family structural condition and maximum hold. If both are due, both
reasons are preserved. Stop and target remain immutable; there is no break-even
move, trailing stop, partial exit, averaging down, pyramiding or target
extension.

## Evidence boundary

Approved plans, synthetic positions, protective decisions and completed-bar
schedules expose deterministic audit fields. Planned risk and reward are sizing
evidence, not realized P&L or performance.

Synthetic tests cover identities, asymmetric asset scopes, both cost profiles,
real Pandas Round 2 signal integration, setup ages, gap limits, three stop and
target rules, exact net `3R`, shared risk/notional/cash caps, adverse fills,
stop-first ambiguity, structural exits, maximum holds, daily continuity,
immutability and cross-family rejection.

## Current authorization state

- Round 2 causal feature component implemented: `true`;
- three Round 2 causal signal components implemented: `true`;
- three Round 2 execution components implemented: `true`;
- baseline and stress cost profiles implemented: `true`;
- shared safety envelope implemented: `true`;
- protective synthetic execution implemented: `true`;
- Round 2 discovery runner implemented: `false`;
- dataset opened: `false`;
- Development data opened: `false`;
- Calibration data opened: `false`;
- Evaluation data opened: `false`;
- Development run authorized: `false`;
- performance evaluation executed: `false`;
- parameter sweep authorized: `false`;
- automatic ranking authorized: `false`;
- automatic strategy selection authorized: `false`;
- Candidate v2 authorized: `false`;
- bounded forward PAPER authorized: `false`;
- cloud execution authorized: `false`;
- real orders submitted: `false`; and
- live execution authorized: `false`.

## Next controlled boundary

The next stage is `IMPLEMENT_ROUND_2_DEVELOPMENT_DISCOVERY_RUNNER`.

That later runner must initially remain unexecuted and unauthorized. It must
bind these exact artifacts, evaluate only the seven registered Round 2
asset-family routes under both cost profiles and unchanged gates, preserve
continuous Development segments, emit immutable evidence and perform no
automatic ranking or selection. Any Development execution requires a later,
separate one-shot operator authorization. Calibration and Evaluation remain
closed.
