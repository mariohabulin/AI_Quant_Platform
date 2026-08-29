# Kraken BTC/ETH/XRP AI-Driven v2 Risk and Execution Protocol v1

## Status

`AI_DRIVEN_V2_RISK_EXECUTION_REVIEWED_SYNTHETIC_TESTS_ONLY`

This protocol converts completed-bar state intents into deterministic synthetic
next-open plans. It freezes entry, cost-aware sizing, gap, structural stop,
causal reward-room, protective-exit and maximum-hold semantics before any real
Kraken data or performance is inspected. It submits no order, accesses no
account, asserts no actual fee tier and does not authorize Candidate v2, PAPER,
cloud or live operation.

## Frozen identity and prerequisites

- risk/execution protocol ID:
  `kraken-btc-eth-xrp-ai-driven-v2-risk-execution-v1`;
- reference policy ID:
  `kraken-ai-v2-risk-execution-reference-a-v1`;
- state protocol ID:
  `kraken-btc-eth-xrp-ai-driven-v2-state-machine-v1`;
- state parameter-set ID:
  `kraken-ai-v2-ccvr-reference-a-v1`;
- dataset ID:
  `kraken-spot-btc-eth-xrp-native-1d-20190101-20260401-archive-only-v2`;
- dataset manifest SHA-256:
  `8c91b42f2bc0c16a0ef0c6b4373572ac53fbf7f5937d4ebbbe75a0d39483df1c`;
- supervised v1 BTC evidence SHA-256:
  `56710a21a423a63963e5c97ab6ca956021f9cd7a7d494c3f29a197068367ff60`;
- state protocol normalized SHA-256:
  `816553684ae3ab6a93b5f0499b61224eebc2bb9808d85d0c1e5c78247931e792`;
- state component normalized SHA-256:
  `72339aaaa21346e5ac0001581eb0a363c7e1a5743f22e0c322ddfa2ac3f7f326`;
- signal role: `COMPLETED_BAR_INTENT`;
- execution role: `SYNTHETIC_RESEARCH_FILL_ONLY`;
- future-bar access: `PROHIBITED_BEYOND_CURRENT_EXECUTION_BAR`.

The external archive-only dataset remains closed during this milestone. The
BTC supervised v1 interval is inspected context and can never become unseen
evaluation evidence.

## Frozen portfolio-risk limits

Reference policy A uses:

- current-equity risk per new crypto position: `0.005` (`0.50%`);
- maximum total open crypto risk: `0.015` (`1.50%`);
- maximum one-position notional fraction: `1/3` of current equity;
- maximum concurrent crypto positions: `3`;
- minimum net reward/risk at causal resistance: `3.0`;
- maximum upward next-open gap: `0.5` times the signal bar's causal prior ATR;
- maximum holding time: `20` completed bars, counting the entry bar as one.

The trade risk budget is the lower of `0.50%` of equity and remaining capacity
under the `1.50%` total-open-risk ceiling. Final units are the minimum of
cost-aware stop-risk size, the one-third notional cap and available-cash size.
If no positive unit size remains, the result is `NO_TRADE_HOLD_CASH`.

This milestone has no portfolio correlation or cross-sleeve allocator. The
three-position and total-risk inputs must be supplied causally by a future
portfolio layer; missing or invalid capacity fails closed.

## Frozen adverse taker cost model

Cost profile ID is `kraken-tier1-taker-adverse-20260829-v1`:

- venue: `Kraken Pro Spot`;
- order role: `TAKER`;
- commission per side: `0.008` (`0.80%`);
- assumed slippage per side: `0.0015` (`0.15%`);
- assumed full spread: `0.0030` (`0.30%`);
- adverse price adjustment per side:
  `slippage + full_spread / 2 = 0.0030` (`0.30%`).

Kraken's official Spot fee schedule reviewed on `2026-08-29` lists Tier 1 at
`0.40%` maker and `0.80%` taker:
`https://www.kraken.com/features/fee-schedule`.

Only the `0.80%` taker commission is an observed venue schedule value. Spread
and slippage are conservative research assumptions, not historical quotes.
Actual account tier, assets-on-platform qualification, pair-specific minimum,
current spread, order-book depth, market impact, partial fills and outage
behavior must be independently reverified before deployment. Maker execution
is prohibited because no causal placement/non-fill/partial-fill model exists.

Synthetic adverse fills are:

- buy fill: `market_reference * (1 + 0.0030)`;
- sell fill: `market_reference * (1 - 0.0030)`;
- commission: `adjusted_fill * units * 0.008`.

## Entry boundary

Only a row with all exact state evidence below may create a pending entry plan:

- state transition: `CONFIRMATION_LONG`;
- state after: `LONG`;
- action intent: `ENTER_NEXT_OPEN`;
- fixed setup low available and positive;
- prior ATR mean available and positive;
- prior 30-bar close high available and positive;
- signal timestamp and next timestamp are consecutive UTC-midnight days.

At the next raw daily open, entry fails closed in this order:

1. invalid or unavailable portfolio inputs;
2. three-position capacity already full;
3. total-open-risk capacity exhausted;
4. raw open at or below the fixed setup low;
5. upward gap above `signal_close + 0.5 * prior_ATR`;
6. cost-adjusted entry not above the fixed setup low;
7. causal resistance not above the entry;
8. net reward/risk to causal resistance below `3.0`;
9. no positive cost-aware size under risk, notional and cash caps.

An approved result is still `APPROVED_SYNTHETIC_ENTRY_PLAN`, never an order.
The structural stop trigger is the exact state-machine setup low. It is not
widened after a gap. The initial target trigger is the signal bar's causal prior
30-bar close high, which acts as already-known material resistance rather than
an invented `3R` price.

## Cost-aware risk and reward

For one unit:

- entry cash outflow is adjusted buy fill plus entry commission;
- conservative stop proceeds are adjusted sell fill at the structural stop
  minus exit commission;
- net risk is entry cash outflow minus conservative stop proceeds;
- causal-resistance proceeds are adjusted sell fill at the frozen prior close
  high minus exit commission;
- net reward is causal-resistance proceeds minus entry cash outflow;
- net reward/risk is `net_reward / net_risk`.

The `3.0` gate uses these cost-aware values. The generic `RiskEngine` receives
an effective stop that represents the complete per-unit risk, retains its
`1e-12` equality tolerance where applicable and supplies deterministic
risk/exposure sizing. The adapter then applies available-cash and total-open-
risk caps. Fees are never ignored or added after sizing.

## Protective execution boundary

An approved synthetic plan may create one synthetic research position. The
existing `ProtectiveExitPolicy` supplies reviewed conservative long-only OHLC
ordering, while this adapter applies the frozen Kraken adverse sell cost.

Every open bar follows this priority:

1. stop gap at or below the stop exits from the raw open reference;
2. target gap at or above resistance exits only from the frozen target
   reference, receiving no optimistic gap improvement;
3. if neither protective gap exists, a previously scheduled state or maximum-
   hold exit uses the raw open reference;
4. otherwise the position remains eligible for intrabar protection.

Intrabar ordering is:

1. stop touch;
2. target touch;
3. hold.

If one daily bar touches both stop and target, stop wins and the evidence marks
the conflict. Entry-bar protection is mandatory. Every exit applies adverse
sell price adjustment and taker commission. No return or P&L is calculated in
this milestone.

## Completed-bar exit scheduling

After a bar survives open and intrabar protection:

- `EXIT_NEXT_OPEN` schedules a state-signal exit;
- when completed bars held reaches `20`, a maximum-hold exit is scheduled;
- if both occur together, evidence records both;
- an exit scheduled at one close cannot fill before the following open.

The reference policy has no break-even stop, trailing stop, partial exit,
pyramiding, averaging down or target extension. The fixed structural stop is
never widened.

## Synthetic verification requirements

Tests must prove:

- exact immutable policy and cost identity;
- next-day timestamp and exact state-intent requirements;
- stop-gap and upward-gap entry rejection;
- cost-aware `3R` room rejection and equality tolerance;
- risk, total-open-risk, one-third notional and cash sizing caps;
- no positive size produces `NO_TRADE_HOLD_CASH`;
- fixed stop and prior-high target cannot drift;
- protective gap priority over scheduled exits;
- conservative target-gap and same-bar stop-first behavior;
- entry-bar protection and adverse sell costs;
- state, maximum-hold and combined next-open scheduling;
- no source mutation, real order, account access, P&L or performance output.

## Next boundary

After Windows integration and full regression, freeze a development/evaluation
partition protocol for the existing locked dataset. Only then may a separately
reviewed one-shot runner execute the complete frozen feature, state, risk and
synthetic execution path on development data. Evaluation, Candidate v2, PAPER,
cloud and live remain separate later authorizations.

## Authorization state

- causal feature component implemented: `true`;
- deterministic state machine implemented: `true`;
- synthetic risk/execution adapter implemented: `true`;
- adverse taker cost model frozen: `true`;
- real account fee tier verified: `false`;
- venue minimum-order rules implemented: `false`;
- real orders or fills executed: `false`;
- external dataset opened: `false`;
- performance evaluation executed: `false`;
- optimization authorized: `false`;
- Candidate v2 authorized: `false`;
- bounded forward PAPER authorized: `false`;
- cloud execution authorized: `false`;
- live execution authorized: `false`.
