# Kraken BTC/ETH/XRP AI-Driven v2 Round 1 Causal Signals Protocol v1

## Status

`KRAKEN_AI_V2_ROUND_1_CAUSAL_SIGNALS_IMPLEMENTED_EXECUTION_COMPONENTS_REQUIRED`

Component identities:

- `kraken-ai-v2-round-1-causal-features-v1`; and
- `kraken-ai-v2-round-1-causal-signals-v1`.

This milestone implements one shared causal feature engine. It provides four deterministic signal paths
for the exact hypotheses frozen by hybrid discovery Round 1. It is
a synthetic-only signal milestone. It does not size a position, model a fill,
open a trade, calculate performance or select a strategy.

Reference A remains closed as `NO_TRADE_HOLD_CASH`. Its report is immutable
feedback lineage for the capitulation family only; its signal and execution
identities and failed prior-resistance-room gate are not reused. Nothing in this
milestone authorizes a Candidate v2.

## Parent lock

The component consumes the canonical Round 1 hypothesis and configuration lock
from protocol
`kraken-btc-eth-xrp-ai-driven-v2-hybrid-discovery-round-1-v1`. Family and
hypothesis order are exact:

1. `CAPITULATION_RECOVERY`;
2. `TREND_PULLBACK_CONTINUATION`;
3. `RANGE_MEAN_REVERSION`; and
4. `VOLATILITY_BREAKOUT`.

Unknown families, reordered registrations or a changed Round 1 configuration
fail closed. All emitted evidence carries the registered hypothesis identity.

## Input and continuity boundary

Each call accepts exactly ordered `Open`, `High`, `Low`, `Close`, `Volume`
columns on unique, increasing, timezone-aware UTC-midnight timestamps. Values
must be finite numeric observations with positive prices, nonnegative volume
and valid OHLC geometry.

One call represents one uninterrupted daily segment. A missing provider day or
partition boundary must split the input before feature generation. State never
crosses a gap or partition. Input frames are copied and never mutated.

Completed daily bars only are permitted. Future-bar access: `false`. The
rolling baseline current bar included: `false`. When a current completed-bar quantity
is compared with history, the historical baseline is shifted before rolling.

## Shared feature formulas

The shared engine emits the following deterministic measurements:

- prior close and high are one-bar shifts;
- close return is `close / prior_close - 1`;
- prior 60-close maximum is the maximum of the preceding 60 closes;
- drawdown is `current_close / prior_60_close_max - 1`;
- true range is the maximum of high-low, absolute high-prior-close and absolute
  low-prior-close;
- ATR-14 uses Wilder EWM with `alpha = 1/14`, `adjust = false` and 14-bar
  minimum history; its decision anchor is prior ATR-14;
- ATR ratios compare current completed-bar ATR with shifted prior 60- or
  120-observation ATR medians;
- volume ratio compares current volume with the preceding 30-volume median;
- close location is `(close - low) / (high - low)`;
- EMA-20, EMA-50 and EMA-200 use `adjust = false`, their full-period minimum
  histories and one-bar-shifted decision values;
- EMA-50 slope is `prior_ema50 / prior_ema50_20_bars_ago - 1`;
- ADX-14 uses Wilder-smoothed TR, directional movement and DX, then a one-bar
  shift for the decision value;
- Bollinger midline is the mean of the preceding 20 closes, standard deviation
  uses `ddof = 0`, and lower/upper bands are two deviations from the midline;
- Bollinger width is `(upper - lower) / midline`, compared with a shifted prior
  120-width median;
- RSI-14 uses 14-observation simple average gains and losses on completed bars;
- stochastic `%K` uses the current completed close and 14-bar high/low range;
  `%D` is the three-observation simple average of `%K`;
- Donchian high is the maximum of the preceding 55 closes; and
- structural low is the minimum of the preceding 10 closes.

Unavailable warm-up values remain unavailable. A family cannot produce a
setup, confirmation or entry intent unless every value required for that state
is finite.

## Evidence and intent contract

Each family produces a complete row-wise evidence trail: feature availability,
regime/setup/confirmation booleans, state before and after, transition, action
intent, setup timestamp, setup low, signal-time prior ATR and optional target
anchor.

`ENTER_NEXT_OPEN` means only that a completed-bar signal may be submitted to a
later family execution adapter. It is not an order, fill or position. The
signal engine contains no capital, quantity, commission, spread, slippage,
stop-fill, P&L, drawdown or portfolio state.

## Capitulation recovery path

The flat state arms when all pre-registered event conditions hold: drawdown at
most `-18%`, return at most `-6%`, true-range/prior-ATR at least `1.50`, volume
ratio at least `1.50` and close location at most `0.35`.

An event while armed replaces the previous setup. The running setup low is the
minimum observed low. A completed close below the prior setup low invalidates
the setup. Otherwise, confirmation may occur within the following five
completed bars and requires close location at least `0.65`, positive return,
volume ratio at least `0.80` and close above prior high. A successful
confirmation emits `ENTER_NEXT_OPEN`, the running setup low and signal-time
prior ATR, then returns to flat. Expiry or missing confirmation features emits
no intent.

This path has no Reference-A prior-resistance-room test.

## Trend-pullback continuation path

The regime requires prior EMA-50 above prior EMA-200, positive 20-bar EMA-50
slope and prior ADX-14 at least `20`. A setup requires the low within `0.25`
prior ATR of prior EMA-20, close above prior EMA-50 and volume ratio at most
`0.90`.

Only the immediate next completed bar can confirm that setup. Confirmation
requires the regime to remain true, close above prior high and prior EMA-20,
and volume ratio at least `1.10`. It emits `ENTER_NEXT_OPEN`, setup timestamp,
setup low and signal-time prior ATR. A new setup on that bar rearms; otherwise
the setup expires. There is no multi-bar search after the immediate bar.

## Range mean-reversion path

The range regime requires causal Bollinger width and current ATR each no more
than `1.10` times their shifted prior 120-observation medians. A setup closes
below the prior Bollinger lower band with RSI no greater than `25` and
stochastic `%K` no greater than `20`.

Only the immediate next completed bar can confirm. It must remain in the range
regime, close back above the setup-time lower band, show rising RSI and move
from setup `%K <= %D` to current `%K > %D`. A successful confirmation emits
`ENTER_NEXT_OPEN`, the minimum setup/confirmation low, signal-time prior ATR
and the signal-time prior Bollinger midline as an immutable target anchor. A
new setup rearms; otherwise the setup expires.

The later execution adapter—not this signal component—must reject any entry
whose frozen midline lacks net `3R` room.

## Volatility-breakout path

The expansion regime requires current ATR at least `1.10` its shifted prior
60-ATR median and prior ADX-14 at least `20`. The same completed bar confirms
when close exceeds the preceding 55-close Donchian high, volume ratio is at
least `1.25` and close location is at least `0.70`.

The confirmation emits `ENTER_NEXT_OPEN`, that bar's timestamp and low, and
signal-time prior ATR. There is no armed multi-bar state for breakout.

## Causality and failure policy

Prefix causality is mandatory: changing observations after a cutoff cannot
change any feature or signal row through that cutoff. Mutating the current bar
cannot change that bar's prior-only baselines. Warm-up, nonfinite input,
invalid geometry, timestamp defects, gaps, unknown families and missing
feature columns fail closed.

Trend and range confirmations are deliberately limited to the immediate next
completed bar. Capitulation has its frozen five-bar window. Breakout is a
same-completed-bar signal. Every accepted intent still targets a later next
open and therefore cannot use that open during signal creation.

## Current authorization state

- feature component implemented: `true`;
- four regime components implemented: `true`;
- four signal components implemented: `true`;
- execution components implemented: `false`;
- discovery runner implemented: `false`;
- dataset opened: `false`;
- development data opened: `false`;
- calibration data opened: `false`;
- evaluation data opened: `false`;
- development run authorized: `false`;
- performance evaluation executed: `false`;
- parameter sweep authorized: `false`;
- automatic ranking authorized: `false`;
- automatic strategy selection authorized: `false`;
- Candidate v2 authorized: `false`;
- bounded forward PAPER authorized: `false`;
- cloud execution authorized: `false`; and
- live execution authorized: `false`.

## Next controlled boundary

The next stage is
`IMPLEMENT_ROUND_1_FAMILY_EXECUTION_COMPONENTS_SYNTHETIC_ONLY`.

That milestone may translate a valid `ENTER_NEXT_OPEN` intent into a
family-specific adverse-cost entry/stop/target plan under the already frozen
shared safety envelope. It must be tested with synthetic paths only and remain
separate from any discovery runner or Development authorization.
