# Kraken BTC/ETH/XRP AI-Driven v2 Round 1 Family Execution Protocol v1

## Status

`KRAKEN_AI_V2_ROUND_1_FAMILY_EXECUTION_IMPLEMENTED_DISCOVERY_RUNNER_REQUIRED`

Component ID:
`kraken-ai-v2-round-1-family-execution-v1`.

This synthetic-only milestone implements four family-specific execution adapters
for the four immutable hybrid discovery Round 1 hypotheses. The adapters turn
an exact causal `ENTER_NEXT_OPEN` signal into a cost-aware research plan and
model protective or scheduled exits. They do not read a dataset, evaluate a
strategy, rank a route or submit an order.

Reference A remains closed `NO_TRADE_HOLD_CASH`. The new adapters may reuse
reviewed generic adverse-cost and protective-ordering mechanics, but none uses
the Reference-A policy, signal, execution or run identity. Candidate v2 and all
deployment authorizations remain false.

## Parent and configuration lock

Every adapter binds the exact configuration SHA-256
`259c1b7ed717058e09ed46dd702311f2f2b667185e4d5ef3db84df5745bda39e`
from protocol
`kraken-btc-eth-xrp-ai-driven-v2-hybrid-discovery-round-1-v1` and consumes only
evidence emitted by component `kraken-ai-v2-round-1-causal-signals-v1`.

The four registered family/execution identities are:

| Family | Execution contract |
| --- | --- |
| `CAPITULATION_RECOVERY` | `kraken-ai-v2-r1-capitulation-execution-v1` |
| `TREND_PULLBACK_CONTINUATION` | `kraken-ai-v2-r1-trend-pullback-execution-v1` |
| `RANGE_MEAN_REVERSION` | `kraken-ai-v2-r1-range-reversion-execution-v1` |
| `VOLATILITY_BREAKOUT` | `kraken-ai-v2-r1-volatility-breakout-execution-v1` |

Each adapter also verifies the registered hypothesis ID, family-specific
confirmation transition, feature availability, signal condition, `FLAT`
post-signal state and `ENTER_NEXT_OPEN` intent. Unknown or cross-family evidence
returns `NO_TRADE_HOLD_CASH`.

## Timing and setup identity

The execution timestamp must be exactly the UTC-midnight day immediately after
the signal timestamp. The position independently preserves the same signal-to-
entry next-day identity.

Setup timing must match the causal state machine:

- capitulation setup is one through five completed days before confirmation;
- trend-pullback setup is the immediate prior completed day;
- range-reversion setup is the immediate prior completed day; and
- breakout setup and confirmation are the same completed day.

A completed position path must remain daily and continuous from its entry bar.
A missing provider day is an error, not an extra holding day or permission to
carry state across a gap.

## Frozen baseline and stress costs

Both pre-registered research profiles are implemented:

| Profile | Commission each side | Slippage each side | Full spread | Adverse price rate each side |
| --- | ---: | ---: | ---: | ---: |
| `kraken-tier1-taker-adverse-20260829-v1` | `0.80%` | `0.15%` | `0.30%` | `0.30%` |
| `kraken-tier1-taker-adverse-stress-r1-v1` | `0.80%` | `0.30%` | `0.60%` | `0.60%` |

The adverse price rate is slippage plus half the full spread. A buy fill is
`raw_open * (1 + adverse_rate)`. A sell fill is
`market_reference * (1 - adverse_rate)`. Commission is applied to the adjusted
fill on both sides. Stress does not change the official Tier-1 taker commission
assumption; it doubles only the separately declared research spread and
slippage.

Neither profile proves actual account tier, liquidity, partial-fill behavior,
pair minimums, outage handling or current executable spread.

## Shared safety envelope

Every family preserves the parent portfolio ceilings:

- current-equity risk per position: at most `0.50%`;
- total planned open risk: at most `1.50%` of current equity;
- concurrent crypto positions: at most three;
- total notional for one asset: at most one third of current equity;
- available cash is a hard sizing ceiling;
- cash-only, long-only and no leverage; and
- minimum cost-adjusted reward/risk: `3.0`.

The risk budget is the lower of `0.50%` of equity and remaining capacity under
the total-open-risk ceiling. Units are the minimum of cost-aware risk size,
remaining per-asset notional size and available-cash size. No positive size
produces `NO_TRADE_HOLD_CASH`.

This component accepts current portfolio capacity as explicit causal input. It
does not choose between multiple passing routes for one asset; that remains a
separate portfolio-review boundary.

## Common entry order

After strict signal, timestamp, asset and portfolio validation, every adapter
applies gates in this order:

1. exact family signal and setup timing;
2. concurrent-position capacity;
3. total-open-risk capacity;
4. per-asset notional capacity;
5. positive family stop below the raw open;
6. raw upward gap no greater than `signal_close + 0.50 * prior_ATR`;
7. positive cost-aware risk distance;
8. family target above the cost-adjusted entry and net reward/risk at least
   `3.0`; and
9. positive units under risk, notional and cash ceilings.

The inclusive upward-gap boundary is permitted; any amount above it fails.
Stops are never widened to admit a gap.

For one unit, entry cash is adverse buy fill plus commission. Stop proceeds are
adverse sell fill at the trigger minus commission. Net risk is entry cash minus
stop proceeds. Target reward is adverse target proceeds minus entry cash. All
target-room and sizing decisions use these net values.

## Capitulation recovery execution

The stop is the running causal setup low minus `0.25` signal-time prior ATR.
The target trigger is calculated as the exact market reference that yields net
cost-adjusted `3R`. Maximum hold is 20 completed bars, counting the entry bar.

After open and intrabar protection survive, a completed close below the causal
prior 10-close low schedules a following-open structural exit. This does not
restore the closed Reference-A prior-resistance-room gate.

## Trend-pullback continuation execution

The stop is the pullback setup low minus `0.25` signal-time prior ATR. The
target trigger is the exact net cost-adjusted `3R` market reference. Maximum
hold is 40 completed bars.

A completed close below the prior EMA-50 schedules the following-open
structural exit after protective checks survive.

## Range mean-reversion execution

The stop is the minimum setup/confirmation low minus `0.25` signal-time prior
ATR. The target is the immutable signal-time prior Bollinger midline carried by
the causal signal component. The adapter rejects the entry unless that frozen
anchor supplies at least net cost-adjusted `3R` under the selected cost profile.

The target cannot move with a later Bollinger calculation. It remains active as
the fixed protective target; otherwise maximum hold at 15 completed bars
schedules the following-open exit.

## Volatility-breakout execution

The stop is the higher of:

- breakout-bar low minus `0.25` signal-time prior ATR; and
- raw following-open entry reference minus `2.0` signal-time prior ATR.

The target trigger is the exact net cost-adjusted `3R` market reference.
Maximum hold is 60 completed bars. A completed close below the causal prior
10-close low schedules a following-open structural exit.

## Protective and scheduled execution

Every open uses the same conservative priority: stop gap before scheduled exit,
with target gap checked between them. A stop gap sells from the adverse raw-open
reference. A target gap receives no favorable open improvement and sells from
the frozen target reference. Only when neither protective gap exists may a
previously scheduled structural or maximum-hold exit use the raw open.

Intrabar priority is stop touch, target touch, then hold. Entry-bar protection
is mandatory. The same-bar stop and target: `STOP_FIRST`. Every modeled sell
applies the selected adverse price rate and taker commission.

After a surviving completed bar, the adapter increments bars held and evaluates
the family structural condition plus maximum hold. If both are due, both reasons
are preserved in one following-open schedule. Stops and targets are immutable;
there is no break-even stop, trailing stop, partial exit, averaging down,
pyramiding or target extension.

## Evidence boundary

Approved plans, synthetic positions, protective decisions and completed-bar
schedules expose deterministic audit fields. Planned risk and reward are sizing
evidence, not realized P&L or performance. No public object contains P&L,
strategy return, ranking, selection or promotion output.

Synthetic verification covers exact identities, both cost profiles, real
Pandas signal integration, family setup timing, gap limits, all four stop and
target rules, net `3R`, shared risk/notional/cash caps, adverse protective fills,
stop-first ambiguity, family structural exits, maximum holds, daily continuity,
immutability and rejection of cross-family evidence.

## Current authorization state

- causal feature component implemented: `true`;
- four causal signal components implemented: `true`;
- execution components implemented: `true`;
- baseline and stress cost profiles implemented: `true`;
- shared safety envelope implemented: `true`;
- protective synthetic execution implemented: `true`;
- discovery runner implemented: `false`;
- dataset opened: `false`;
- development data opened: `false`;
- calibration data opened: `false`;
- evaluation data opened: `false`;
- development run authorized: `false`;
- performance evaluation executed: `false`;
- parameter sweep authorized: `false`;
- automatic ranking authorized: `false`;
- Candidate v2 authorized: `false`;
- bounded forward PAPER authorized: `false`;
- cloud execution authorized: `false`;
- real orders submitted: `false`; and
- live execution authorized: `false`.

## Next controlled boundary

The next stage is `IMPLEMENT_ROUND_1_DEVELOPMENT_DISCOVERY_RUNNER`.

That runner must remain unexecuted and unauthorized when first implemented. It
must bind this exact component, isolate every provider-continuous Development
segment, run all twelve asset-family routes under baseline and stress costs,
emit immutable route/slice evidence, apply only the pre-registered absolute
gates and perform no automatic winner selection. Any Development execution
requires a later explicit one-shot authorization. Calibration and Evaluation
remain closed.
