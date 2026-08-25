# Trend Pullback and Volume Re-expansion Protocol v1

## Status

This document pre-registers a structurally new development hypothesis. It is
not Candidate v2, does not execute performance and does not reopen the closed
Alpha Discovery v1 impulse-entry catalog.

The protocol is bound to:

- the inspected native Coinbase six-hour BTC-USD and ETH-USD dataset manifest
  SHA-256 `6506dd2700b983a134a132890ef4c4ae6e84c0918ba65a5abff6ab2c204c4e7f`;
- the closed canonical Alpha Discovery v1 report SHA-256
  `2fc8f4d1a5d690c072408bc2d299516904feb58b2e2f40345983641bf26ed678`;
- the report's exact `SCREEN_OUT`, zero-selected-window and seven-window
  `HOLD_CASH` result; and
- the exact observed inner-gate counts, including universal stress-return and
  baseline/stress persistence failure.

Any evidence, identity, gate-count, authorization or canonical-byte drift
fails closed.

## Falsifiable mechanism

The previous catalog entered an already-developed bullish ADX impulse while
relative volume was high. Its risk, cost, turnover and drawdown controls worked,
but its net absolute return and temporal persistence did not.

The new hypothesis is narrower:

> Within a causal bullish trend, a controlled pullback toward EMA 50 on
> contracting or normal relative volume, followed by price recovery and volume
> re-expansion, will persist after baseline and stressed execution costs better
> than entering an already-developed high-volume impulse.

This is a new entry-timing mechanism, not a parameter adjustment to the closed
impulse catalog.

## Causal state sequence

All state is observed from completed bars only. No future bar is available.

1. Trend structure: Close is above EMA 200 and the four-bar EMA 50 slope is
   positive.
2. Prior strength: ADX reached 25 during the preceding eight completed bars.
3. Pullback: price returns within a frozen ATR distance of EMA 50 while
   relative volume is no greater than 1.0.
4. Recovery trigger: Close exceeds the previous High and EMA 50, `+DI > -DI`,
   ADX remains at least 20 and relative volume re-expands above its frozen
   threshold.
5. Entry: the following bar Open.
6. Exit: a static 2 ATR stop, a 3R target, or a completed-bar signal exit when
   Close loses EMA 50, ADX falls below 15 or `+DI` no longer exceeds `-DI`.

Relative volume uses a 20-bar trailing baseline lagged by one bar. OBV is not
an entry gate because the closed evidence did not support a stable universal
OBV rule.

## Four-member bounded catalog

The only ablations are pullback depth and recovery-volume strength:

| Parameter-set ID | Pullback distance | Trigger relative volume |
| --- | ---: | ---: |
| `pb0p5-rv1p2-2atr-static3r` | 0.5 ATR | 1.2 |
| `pb0p5-rv1p5-2atr-static3r` | 0.5 ATR | 1.5 |
| `pb1p0-rv1p2-2atr-static3r` | 1.0 ATR | 1.2 |
| `pb1p0-rv1p5-2atr-static3r` | 1.0 ATR | 1.5 |

Every other strategy, risk and execution value is shared. The canonical
catalog SHA-256 is
`952046ddb7a9f9a85a8976f3ccafe43a017a745c887e592a44c39c2146ba8e00`.

There is no break-even variant, broad parameter sweep, indicator leaderboard,
shorting or leverage. Risk remains 0.50% of equity per trade with at most 50%
position exposure.

## Future development boundary

A later, separately reviewed implementation may reuse the prior chronological
shape: 5,760/720/720 outer train/test/step and 2,880/720/720 inner
train/validation/step, with at most four recent inner windows. Selection must
use the complete shared BTC/ETH catalog under Coinbase baseline and stress.

The existing minimum trades, 60% inner persistence, 20% drawdown, 12x annual
turnover and 10% annual baseline-cost limits remain intact. No eligible member
must produce `HOLD_CASH`; outer evidence must be unavailable to selection and a
global hindsight leaderboard remains prohibited.

The state machine, executable strategy and nested runner each require a
separate review. Until all exist, runner execution is unauthorized.

## Authorization boundary

Protocol declaration and evidence locking execute no performance, calibration,
selection or optimization. Candidate v2, bounded PAPER review, PAPER, cloud and
live authorization remain false. A future development result may only form a
hypothesis for a separately frozen candidate tested on genuinely unseen data.
