# Strategy Family Screening Protocol v1

## Purpose

This protocol freezes one descriptive development screen for the eight
standalone strategy implementations that have not received a market evaluation.
It is designed to eliminate unsupported mechanisms and identify at most a
research lead from which a new falsifiable hypothesis could later be written.

It is not candidate-v2 evaluation. It produces no leaderboard, winner,
parameter optimization, combined strategy, PAPER authorization or live-trading
authorization.

## Why six-hour candles are the working resolution

The closed Timeframe Sensitivity Study selected no winning timeframe. This
screen nevertheless needs one fixed working resolution before results exist.
Six-hour candles are frozen for development because prior evidence showed:

- one-hour EMA evidence had extreme turnover/cost loss and 93%-98% drawdown
- daily evidence contained very few OOS trades per asset
- six-hour evidence retained materially more trade density than daily data
  without the one-hour turnover level

This is an evidence-density and research-cost choice, not a claim that six-hour
candles are profitable or superior.

## Frozen development data

| Field | Frozen value |
| --- | --- |
| Dataset | Coinbase native BTC/ETH 6h v1 |
| Range | `[2019-01-01, 2026-08-01)` UTC |
| Assets | `BTC-USD`, `ETH-USD` |
| Rows | 11,076 per asset |
| Role | Inspected development evidence only |
| Manifest SHA-256 | `6506dd2700b983a134a132890ef4c4ae6e84c0918ba65a5abff6ab2c204c4e7f` |

The manifest lock revalidates canonical manifest bytes, its sidecar, every CSV
hash, exact UTC grid, row count and OHLCV validity before a future runner may
receive the frames. This historical range can form a hypothesis but can never
be relabeled as unseen candidate-v2 validation.

## Frozen standalone configurations

Exactly one existing default configuration is permitted per strategy:

| Order | Strategy | Family | Parameters |
| ---: | --- | --- | --- |
| 1 | ADX | Trend | period 14, threshold 25 |
| 2 | ATR breakout | Breakout | period 14, multiplier 1 |
| 3 | Bollinger | Mean reversion | period 20, 2 standard deviations |
| 4 | Donchian | Breakout | period 20 |
| 5 | MACD | Trend | 12/26/9 |
| 6 | RSI | Mean reversion | period 14, 30/70 |
| 7 | Stochastic | Mean reversion | 14/3, 20/80 |
| 8 | Supertrend | Trend | period 10, multiplier 3 |

EMA 20/50 is excluded because candidate v1 and the Timeframe Sensitivity Study
already closed that mechanism as rejected. No parameter variants or indicator
combinations are part of this screen.

Each strategy identity includes a deterministic fingerprint over its name,
family, mechanism and exact parameters. A later parameter change creates a
different research experiment.

## Shared evaluation semantics

Every future screen must reuse the candidate-v1 configuration unchanged:

- expanding 2,880-bar training and non-overlapping 720-bar test/step windows
- 70/30 chronological OOS split
- completed-Close observation and following-Open execution
- force-close only at the final Close for deterministic reporting
- initial capital 5,000 and seed `20260822`
- 5,000 falsification simulations at 95% confidence
- minimum 60% positive walk-forward excess rate
- minimum five test windows and 30 unseen walk-forward trades per asset
- maximum 20% OOS drawdown
- exact two-asset scope

Baseline costs remain 0.60% commission per side, 0.05% slippage and 0.10% full
spread. Stress retains 0.60% commission while raising slippage to 0.15% and
full spread to 0.30%.

## Multiple-comparison boundary

Eight mechanisms will inspect the same development data. Their results are
therefore descriptive research evidence, not eight independent confirmatory
tests. Protocol v1 prohibits a score, return ranking, winner, tie-break and
formal validation claim.

Only these outcomes are allowed per strategy:

- `SCREEN_OUT`: baseline or stress multi-asset classification is rejected
- `MECHANISM_RETAINS_INTEREST`: baseline and stress are both multi-asset
  validated and the frozen evidence-volume/drawdown gates pass
- `INCONCLUSIVE`: neither of the above conditions is complete

Several strategies may retain interest or none may do so. A retained mechanism
is not automatically chosen. It may only support writing one separate,
structurally justified hypothesis that must receive a new immutable identity
and genuinely unseen future validation.

## Current non-execution commands

After Windows reproduction and Git integration, print the declaration:

```powershell
python src/strategy_family_screening.py
```

Revalidate and bind the existing canonical development dataset without running
the screen:

```powershell
python src/strategy_family_screening.py `
    --manifest data/research/first_candidate_v1/manifest.json
```

Both commands report `screening_executed=false` and
`performance_evaluation_executed=false`. A screening runner and canonical
evidence recorder require a later separately reviewed patch and explicit
command.

The separately prepared runner preserves this declaration unchanged. It is a
one-shot atomic recorder with no parameter or ranking path and must receive its
own Windows reproduction plus reviewed commit/push before execution.

Local TDD passes 15/15 new protocol tests, 233/233 focused research/integration
tests and the complete 788/788 suite. Windows reproduction and exact Git
integration remain required before the data-lock command may be used.

Candidate v2, optimization, bounded forward PAPER and live execution remain
unauthorized regardless of any later development-screen result.
