# Kraken BTC/ETH/XRP AI-Driven v2 Round 2 Causal Signals Protocol v1

## Status

`KRAKEN_AI_V2_ROUND_2_CAUSAL_SIGNALS_IMPLEMENTED_EXECUTION_COMPONENTS_REQUIRED`

Component identities:

- `kraken-ai-v2-round-2-causal-features-v1`; and
- `kraken-ai-v2-round-2-causal-signals-v1`.

This milestone implements one shared causal feature engine and three exact
state-machine signal paths frozen by hybrid discovery Round 2. It is synthetic
only. It does not size a position, calculate a fill, open a trade, evaluate
performance or select a route.

Round 1 remains closed against report SHA-256
`3ce14fda95f657c0b671b74c702d55ec4102da303e9e033ebaf0e02ff5c2fa9b`.
Its rerun authorization remains false. Round 2 signal implementation cannot
change Round 1 failure attribution, the Round 2 manifest or any interest gate.

## Parent configuration lock

The component consumes exact configuration SHA-256 from protocol
`kraken-btc-eth-xrp-ai-driven-v2-hybrid-discovery-round-2-v1`. Family and
hypothesis order are:

1. `CAPITULATION_RECOVERY` — BTC, ETH and XRP;
2. `VOLATILITY_BREAKOUT` — BTC and ETH; and
3. `TREND_PULLBACK_CONTINUATION` — BTC and ETH.

Unknown families, reordered hypotheses, changed asset scopes or a modified
Round 2 configuration fail closed. Asset routing remains a later runner
responsibility; this component implements the registered family paths only.

## Input and continuity boundary

Each call accepts exact ordered `Open`, `High`, `Low`, `Close`, `Volume`
columns on unique, increasing, timezone-aware UTC-midnight daily timestamps.
Prices must be positive finite numbers, volume must be finite and nonnegative,
and OHLC geometry must be valid.

One call represents one uninterrupted daily segment. A provider gap or
partition boundary must split input before feature generation. Feature, setup,
retest, MACD memory and signal state never cross that boundary. Inputs are
copied and not mutated.

Completed daily bars only are used. Future-bar access is `false`.
The rolling baseline current bar included is `false`. Every prior high,
channel, median, EMA/ADX decision anchor and prior MACD value is shifted before
use.

## Shared causal feature formulas

The engine emits deterministic Round 2 measurements:

- previous close is a one-bar shift;
- prior two- and three-high values are maxima of the preceding two and three
  completed highs;
- prior 40-close maximum excludes the current bar;
- true range is the maximum of high-low, absolute high-prior-close and absolute
  low-prior-close;
- ATR-14 is Wilder EWM with `alpha = 1/14`, `adjust = false` and 14-bar minimum
  history; the signal anchor is prior ATR-14;
- ATR-normalized drawdown is `(current close - prior 40-close maximum) /
  prior ATR-14`;
- ATR-normalized one-bar price change is `(current close - prior close) /
  prior ATR-14`;
- true-range expansion is current true range divided by prior ATR-14;
- current ATR-14 is compared with the shifted prior 60-ATR median;
- volume ratio compares current volume with the preceding 30-volume median;
- close location is `(close - low) / (high - low)`;
- EMA-20, EMA-50 and EMA-200 use `adjust = false`, full-period minimum history
  and one-bar-shifted decision values;
- EMA-50 slope compares prior EMA-50 with its value 20 completed bars earlier;
- ADX-14 uses Wilder-smoothed TR, directional movement and DX, then shifts one
  bar for the decision value;
- MACD uses current completed-bar EMA-12 minus EMA-26, with EMA-9 signal and
  histogram; both current histogram and its one-bar shift are exposed;
- Donchian breakout level is the maximum of the preceding 55 closes; and
- structural low is the minimum of the preceding 10 closes.

Unavailable warm-up values remain unavailable. No backfill, future fill or
cross-gap carry is permitted.

## Evidence and intent contract

Every family produces a complete row-wise trail containing feature
availability, regime/setup/signal flags, state before/after, transition,
following-open intent, setup timestamp and low, signal-time prior ATR, frozen
setup level, state age, retest observation and MACD nonpositive memory.

`ENTER_NEXT_OPEN` is a research intent only. It is not an order, approval,
quantity, fill or position. The engine contains no cash, risk sizing,
commission, slippage, spread, stop-fill, target-fill, P&L, drawdown, portfolio
allocation or performance ranking.

## ATR-normalized capitulation recovery path

Flat state arms when all registered setup conditions hold:

- close is at least six prior ATR below the preceding 40-close high;
- one-bar price change is at most `-1.50` prior ATR;
- true range is at least `1.75` prior ATR;
- volume ratio is at least `1.50`; and
- close location is no higher than `0.35`.

The setup bar has age zero. A confirmation cannot occur on the setup bar or the
first following completed bar. At least two completed post-setup bars must
elapse. From age two through age seven, confirmation requires close location at
least `0.60`, close above the preceding two-high maximum and volume ratio at
least `0.80`.

A new qualifying shock while armed replaces the setup and resets age. The
running setup low is the minimum observed low. A completed close below the
previous running setup low invalidates the path. Missing confirmation features
fail closed; age eight expires. Successful confirmation emits setup timestamp,
running low and current signal-time prior ATR, then returns to flat.

No Reference-A resistance-room gate exists.

## Breakout-retest continuation path

Flat state arms when current ATR is at least `1.10` its shifted prior 60-ATR
median, prior ADX-14 is at least `20`, close exceeds the preceding 55-close
channel, volume ratio is at least `1.25` and close location is at least `0.70`.

That breakout bar never emits entry intent. It freezes the channel level and
setup-time prior ATR. During the following five completed bars, price must
trade to no more than `0.25` setup ATR above the level and close at or above
the level. That bar records the retest but still cannot confirm.

Only a later completed bar may confirm. It must close above the preceding high
with volume ratio at least `1.00`. The running retest low becomes the stop
anchor and the signal row supplies its prior ATR. A completed close below the
frozen breakout level invalidates immediately. Age six expires; missing active
features fail closed.

This ordered setup -> retest -> confirmation state machine structurally
prevents reuse of the Round 1 direct-breakout entry.

## Multi-bar MACD trend-resumption path

The causal trend regime requires prior EMA-50 above prior EMA-200, positive
20-bar EMA-50 slope and prior ADX-14 at least `20`. A setup requires low within
`0.50` prior ATR of prior EMA-20, close above prior EMA-50 and volume ratio no
higher than `1.00`.

The setup opens a two-to-five-bar state. The MACD histogram must be nonpositive
on the setup or a later pullback bar. Confirmation is allowed only from age two
through age five and requires a real zero cross: prior histogram at or below
zero, current completed histogram above zero, close above the preceding
three-high maximum and volume ratio at least `1.00`.

A zero cross at age one is too early and cannot be reused on a later bar without
a new cross. The running pullback low is retained. Loss of the trend regime or
a completed close at/below EMA-50 invalidates. Age six or missing features
expires. Successful confirmation emits the setup timestamp, running low and
signal-time prior ATR, then returns to flat.

## Causality and failure policy

Prefix causality is mandatory: changing observations after a cutoff cannot
alter any feature, state or signal through that cutoff. Mutating a current bar
cannot alter that bar's shifted prior-only baselines. Current completed-bar
MACD, price, volume and close location may change only that bar and later state.

Warm-up, nonfinite input, invalid geometry, timestamp defects, gaps, unknown
families and missing required feature columns fail closed. No setup state may
invent a next open or inspect it during signal creation.

## Current authorization state

- Round 2 feature component implemented: `true`;
- three Round 2 regime components implemented: `true`;
- three Round 2 signal components implemented: `true`;
- Round 2 execution components implemented: `false`;
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
- cloud execution authorized: `false`; and
- live execution authorized: `false`.

## Next controlled boundary

The next stage is
`IMPLEMENT_ROUND_2_FAMILY_EXECUTION_COMPONENTS_SYNTHETIC_ONLY`.

That later milestone may translate a valid `ENTER_NEXT_OPEN` intent into the
three exact family-specific cost-aware entry, stop, target and maximum-hold
plans under the unchanged safety envelope. It must remain synthetic and
separate from any Development runner or execution authorization.
