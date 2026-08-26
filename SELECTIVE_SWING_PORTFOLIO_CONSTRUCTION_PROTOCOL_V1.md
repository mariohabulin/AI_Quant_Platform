# Selective Swing Portfolio Construction Protocol v1

## Status

`DECLARED_REVIEWED_NOT_EXECUTED`

This protocol formalizes the capital-allocation philosophy shared by the future
listed-equity and crypto research sleeves. It does not select a security,
generate an order, implement pyramiding, implement an intraday strategy, run a
performance evaluation or authorize Candidate v2, PAPER, cloud or live trading.

## Purpose

The portfolio must remain able to participate through many future opportunities
rather than maximize exposure on every signal. Continuous observation, selective
entry, small bounded risk and cash by default take priority over trading
frequency. Capital may be allocated only to independently eligible signals that
exist at the causal decision boundary.

Protocol identity:

- protocol: `selective-swing-portfolio-construction-v1`
- primary long-term market: listed equities
- active secondary market: BTC, ETH and XRP spot research
- equity starting capacity: at most three concurrent positions
- equity future research ceiling: five positions after separate review
- allocation basis: equal capital envelope among eligible signals, `1/n`
- actual sizing: lower of the `1/n` envelope and all risk/exposure limits
- default for unused capital: cash
- operating books: crypto swing, listed-equity CAN SLIM swing and a separately
  governed exceptional intraday contingency
- minimum opportunity screen: approximately `3R` of causal upside must be
  feasible before a normal entry, without forcing an automatic full exit at
  exactly `3R`

## Eligibility before allocation

Allocation cannot create a trade. Each sleeve must first produce its own causal
eligibility decision under a separately frozen strategy protocol.

- The equity sleeve may eventually rank point-in-time CAN SLIM candidates only
  after its fundamentals, historical universe and market-direction contract is
  reviewed.
- The crypto sleeve retains one independent daily signal state for BTC-USD,
  ETH-USD and XRP-USD.
- A cross-asset relationship may later be analyzed diagnostically, but it is not
  an entry rule in this protocol.
- No current or future return may be used to decide which member was eligible at
  the historical boundary.

The AI may rank candidates that already satisfy a frozen eligibility contract.
It may not invent eligibility, lower a gate, use later performance or silently
change live rules.

## Equal-weight eligible allocation

At decision time `t`, let `E_t` be the set of independently eligible assets and
let `n_t = |E_t|`.

If `n_t = 0`, the portfolio remains entirely in cash. Otherwise, the raw capital
envelope for every member is:

`target_envelope_i = portfolio_capital / n_t`

Examples:

- one eligible member: raw envelope up to `1/1`;
- two eligible members: raw envelope up to `1/2` each;
- three eligible members: raw envelope up to `1/3` each.

The raw envelope is not a risk budget and never forces full investment. Actual
position size is:

`min(1/n capital envelope, stop-based risk size, per-position exposure cap,
portfolio open-risk capacity, correlation/sector capacity, available cash)`

Consequently a single eligible asset may receive far less than all available
capital. Any unused amount remains cash. This distinction preserves the user's
`1/n` diversification intent without allowing a distant stop, price gap or one
isolated signal to risk the account.

## Professional portfolio-risk boundary

The future executable allocator requires one shared risk engine above every
strategy book. Strategy eligibility can propose a position; only the risk
engine may approve its size. The engine must calculate risk from the executable
entry to the protective invalidation price and must include gap, spread,
slippage, commission, currency and venue effects appropriate to the instrument.

The following values are provisional research ranges for the initial EUR 5,000
capital scale, not live limits or evidence of safety:

- standard swing risk per new position: approximately `0.25%–0.50%` of current
  portfolio equity;
- total open portfolio risk: approximately `1.00%–1.50%` of current portfolio
  equity;
- rare intraday contingency risk: strictly below the standard swing risk;
- concurrent listed-equity capacity: no more than three positions;
- a correlation cluster may consume less capacity than its nominal position
  count suggests.

Final numeric limits require their own frozen risk protocol, executable gap
policy and PAPER review. A percentage stop is never assumed to guarantee the
same realized loss. If the minimum executable size would violate a risk limit,
the correct position size is zero.

## Three isolated strategy books

The platform maintains three evidence and risk books:

1. `DAILY_CRYPTO_SWING`: independent BTC-USD, ETH-USD and XRP-USD daily signal
   states, combined only after each signal is causally eligible;
2. `POINT_IN_TIME_CAN_SLIM_SWING`: listed-equity growth and leadership research
   using only information available at the historical decision time;
3. `EXCEPTIONAL_INTRADAY_BREAKOUT_CONTINGENCY`: one rare, smaller-risk,
   same-session event hypothesis.

The books may share infrastructure but may not share alpha claims, thresholds,
performance evidence or authorization. Failure or success in one book cannot
promote another. Combined portfolio evaluation is permitted only after each
book has independent evidence.

## Required no-trade state

`NO_TRADE_HOLD_CASH` is a first-class outcome, not a failed search. A future
allocator must refuse a new position when any applicable condition is true:

- no independently eligible causal signal exists;
- the market-regime gate for the strategy book fails;
- the proposed stop is absent, non-executable or too distant for minimum size;
- portfolio open-risk, sector, correlation or cash capacity is unavailable;
- liquidity, spread, slippage or venue availability exceeds the frozen budget;
- required market, fundamental, corporate-action or news data is missing,
  stale, revised without provenance or outside its point-in-time boundary;
- the causal price path does not leave approximately `3R` of feasible upside
  before material resistance or another pre-registered exit constraint;
- a portfolio loss-stop, evidence-drift stop or operational safety stop is
  active.

The agent may not weaken a no-trade gate merely to produce activity.

## Reward and exit governance

The intended `1:3` risk/reward relationship is an entry-quality screen, not a
promise and not a mandatory full take-profit at exactly `3R`. A future strategy
protocol must separately freeze whether it uses full exits, partial realization
or a structure-based trailing remainder. Every method must preserve the
original invalidation price, avoid widening risk after entry and include the
effect of costs.

A favorable move alone does not authorize holding forever. Every strategy must
define signal failure, protective invalidation, maximum holding time and any
volume, momentum or market-regime exit before performance is run.

## Daily crypto setup reconstruction boundary

The user's observed crypto process is retained as a sequence for blinded
hypothesis reconstruction, not as an implemented strategy:

1. exceptional decline relative to the asset's own causal volatility history;
2. exceptional volume relative to its own lagged daily volume history;
3. stabilization or absorption rather than immediate falling-price entry;
4. causal confirmation of recovery before entry eligibility;
5. a predefined structural invalidation and executable next-boundary entry;
6. exit evidence such as structural failure, climactic adverse volume,
   momentum failure, parabolic extension or maximum holding time.

Words such as `exceptional`, `large` and `confirmation` require a small
pre-registered catalog after blinded replay. BTC, ETH and XRP remain one crypto
risk family even when their short-term paths differ. XRP decoupling, inverse
movement and lead/lag behavior are diagnostic hypotheses until measured on
locked data; none is an automatic rotation rule.

## Initial equity concentration

The listed-equity sleeve begins with at most three concurrent positions. Three
is sufficiently selective for the intended capital scale and keeps every
candidate understandable and auditable. Five is a future research ceiling, not
current authorization. Expansion requires separate evidence covering costs,
liquidity, sector concentration, operational capacity and portfolio risk.

Owning three securities does not guarantee diversification. Stocks in the same
industry or driven by the same market factor may belong to one correlation-risk
cluster. A future executable allocator must therefore enforce sector,
industry, market-regime and measured-correlation limits in addition to `1/n`.

## Membership changes and freed capital

When a position loses eligibility or triggers a frozen exit, its exposure is
removed at the next permitted executable boundary. The released capital is not
automatically transferred to assets that have already risen.

Increasing a surviving position requires a fresh causal add-on signal and every
risk/correlation gate. Without that new evidence, released capital stays in
cash. Every membership change and permitted rebalance must include commissions,
spread, slippage, tax and currency effects applicable to the future venue.

This prevents a causal `1/n` process from becoming hindsight winner chasing.

## Winner-only pyramiding boundary

Pyramiding is not implemented or authorized by this document. A future separate
protocol may add to a position only when all of the following are true:

- the existing position is profitable;
- a fresh, pre-registered causal add-on structure is complete;
- the new addition is smaller than the preceding tranche;
- vertical price extension alone is not treated as confirmation;
- the stop and total position risk are recomputed;
- portfolio open risk, sector and correlation limits still pass;
- transaction costs remain inside the future budget.

Adding to a losing position or averaging down is prohibited. Capital freed by a
loser does not itself create permission to pyramid a winner.

## Rare exceptional intraday equity contingency

The user has identified a separate rare opportunity: a listed stock sometimes
breaks explosively upward from a prolonged sideways position, with an observed
move on the order of 20–30% or more. The platform may research this later as:

`Exceptional Sideways Breakout Contingency v1`

The observed percentage is descriptive and is not a frozen entry threshold.
This contingency is not general day trading, scalping or permission to chase a
vertical market order. It is a separate event-driven hypothesis and remains
unimplemented.

Before any performance test, its own protocol must define and audit:

- a causal minimum sideways-base duration and compression structure;
- the reference price from which an exceptional move is measured;
- real-time point-in-time intraday prices and volume;
- relative volume, liquidity and minimum executable notional;
- spread, slippage, commissions, volatility halts and reopening behavior;
- news, earnings and corporate-action timestamp treatment;
- confirmation after the initial vertical move rather than hindsight entry;
- a maximum permitted extension and no-chase condition;
- an executable entry, predefined stop and failed-breakout exit;
- mandatory same-session flattening and maximum holding time;
- a risk budget strictly smaller than a normal swing trade;
- at most one simultaneous contingency position;
- no pyramiding before independent validation;
- development, unseen validation and falsification boundaries.

If these inputs cannot be reconstructed without leakage, the opportunity is
not backtestable and remains observation-only. The future contingency must keep
its evidence separate from CAN SLIM so an exceptional price jump cannot be
retroactively relabeled as a faithful CAN SLIM trade.

## Relationship to CAN SLIM

A proper breakout by a point-in-time CAN SLIM-qualified company remains part of
the future CAN SLIM sleeve. A stock that lacks the complete CAN SLIM identity but
meets a separately frozen exceptional-breakout contract belongs only to the
rare contingency sleeve. The two may share risk and execution infrastructure;
they may not share performance claims or silently transfer thresholds.

Faithful CAN SLIM research requires point-in-time earnings, sales, shares,
institutional sponsorship, relative strength, sector/industry leadership,
market direction, corporate actions, publication timestamps and a historical
security universe that retains delisted and failed companies. Later revisions,
today's survivors or a current constituent list may not be projected backward.
Price/volume breakout evidence cannot replace missing fundamental identity.

## Execution realism

Every future evaluation must model the order boundary actually intended for
deployment. At minimum it must include commissions, bid/ask spread, slippage,
gaps through stops, partial or rejected fills, minimum notional, venue outage
and missing-data behavior. The exceptional intraday book additionally requires
quotes or another defensible spread source, volatility-halt and reopening data,
and point-in-time corporate-event timestamps. Daily OHLCV alone cannot prove
that an intraday entry or stop was executable.

## AI learning and rule governance

The live or PAPER agent executes a versioned, frozen decision policy. It may
observe, rank already eligible candidates, size within approved limits, log
decisions and trigger safety stops. It may not learn directly from a live trade,
rewrite thresholds, expand the eligible universe, suppress a loss or deploy a
new model without review.

Learning occurs offline from immutable evidence. Every proposed change creates
a new version, tests, development evaluation, genuinely unseen validation and
an explicit promotion decision. Production evidence may diagnose drift but may
not silently train and redeploy the active policy.

## Required future evidence sequence

1. integrate this declaration without executing allocation or performance;
2. return to the BTC/ETH/XRP provider and historical-availability audit;
3. lock the three-asset daily data boundary before real crypto replay;
4. audit point-in-time equity/fundamental/universe data;
5. separately pre-register CAN SLIM eligibility and sell rules;
6. separately pre-register winner-only pyramiding rules;
7. separately audit intraday data and pre-register the rare contingency;
8. evaluate each signal sleeve before evaluating portfolio allocation;
9. reserve genuinely unseen evidence before any promotion decision.
10. freeze a shared portfolio-risk and no-trade protocol before PAPER;
11. permit offline model improvement only through versioned promotion.

## Authorization state

- portfolio allocation executed: `false`
- risk sizing executed by this protocol: `false`
- stock candidate ranking executed: `false`
- crypto `1/n` allocation executed: `false`
- pyramiding implemented: `false`
- exceptional intraday strategy implemented: `false`
- general day trading authorized: `false`
- scalping authorized: `false`
- performance evaluation executed: `false`
- optimization authorized: `false`
- Candidate v2 authorized: `false`
- bounded forward PAPER review eligible: `false`
- bounded forward PAPER authorized: `false`
- cloud execution authorized: `false`
- live execution authorized: `false`
