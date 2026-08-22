# First Strategy Candidate v1 — Pre-registration

## Status

`DATASET_LOCK_PENDING`. No performance evaluation has been executed or
inspected. Changing any frozen field below creates a new candidate ID.

## Candidate

| Field | Frozen value |
| --- | --- |
| Candidate ID | `ema-crossover-20-50-btc-eth-native-6h-v1` |
| Strategy | existing `ema_crossover` implementation |
| Parameters | fast EMA 20; slow EMA 50 |
| Direction | long-only spot |
| Leverage | none |
| Assets | `BTC-USD`, `ETH-USD` |
| Timeframe | native Coinbase 6-hour candles |
| Signal observation | completed bar Close |
| Execution | following bar Open |
| Terminal reporting | force-close at final Close |
| Initial research capital | 5,000 |
| Optimization | prohibited for this candidate |
| Live execution | unauthorized |

Hypothesis: a frozen long-only EMA 20/50 crossover on native Coinbase
six-hour spot candles will retain positive unseen absolute and buy-and-hold
excess return across BTC-USD and ETH-USD after low-volume taker costs and an
adverse execution-cost stress profile.

## Dataset contract

- source: unauthenticated Coinbase Exchange public REST product candles
- range: `2019-01-01T00:00:00Z` inclusive to `2026-08-01T00:00:00Z` exclusive
- native granularity: `21600` seconds (6 hours)
- expected continuous rows: 11,076 per asset
- response: `[time, low, high, open, close, volume]`
- maximum provider response: 300 candles; acquisition chunks below this bound
- canonical files: UTF-8, LF, UTC timestamps, fixed column order, `.17g` floats
- acceptance: exact continuous grid, valid OHLCV geometry, no conflicting
  duplicate, SHA-256 for every CSV and the canonical manifest

Coinbase documents 6-hour candles as a native granularity and limits one
request to 300 candles:
<https://docs.cdp.coinbase.com/api-reference/exchange-api/rest-api/products/get-product-candles>

The candidate cannot be finalized until the manifest and both local CSV files
exist and all hashes, row counts, asset scope and time-grid checks pass.

## Cost contract

| Profile | Commission per side | Slippage per side | Full spread | Modeled one-way friction |
| --- | ---: | ---: | ---: | ---: |
| Baseline | 0.60% | 0.05% | 0.10% | 0.70% |
| Stress | 0.60% | 0.15% | 0.30% | 0.90% |

Market orders are treated as taker orders. The 0.60% baseline commission uses
Coinbase's published low-volume taker tier rather than assuming a future
discount. Coinbase states that market orders consume liquidity and its public
Exchange schedule lists 60 basis points for the $0–$10K tier:
<https://help.coinbase.com/exchange/trading-and-funding/exchange-fees>

Actual account fees must be queried and frozen again before any future live
broker integration. This research profile is deliberately conservative and is
not a promise about future venue pricing.

## Validation contract

- expanding walk-forward: 2,880 train bars, 720 unseen test bars, 720-bar step
- chronological OOS split: 70/30
- random seed: `20260822`
- statistical simulations: 5,000 at 95% confidence
- both assets must validate; no rejected asset is allowed
- at least five non-overlapping windows and 30 unseen completed trades per asset
- maximum unseen OOS drawdown: 20% under baseline and stress
- baseline and stress multi-asset results must both be `VALIDATED` for
  `PAPER_CANDIDATE`

The next action is dataset acquisition and SHA-256 lock. It is not strategy
evaluation, parameter tuning, forward PAPER or live trading.

## Controlled commands after repository integration

Print the frozen declaration without downloading data or evaluating results:

```powershell
python src/first_strategy_candidate.py
```

Acquire and lock the exact dataset into an ignored local research directory:

```powershell
python src/coinbase_research_dataset.py --output data/research/first_candidate_v1
python src/first_strategy_candidate.py --manifest data/research/first_candidate_v1/manifest.json
```

The second command rechecks canonical manifest bytes, its SHA-256 sidecar,
per-asset hashes, row counts, exact UTC grid and OHLCV validity. It prints the
locked candidate identity and explicitly reports `evaluation_executed=false`.
These commands must be run only after focused/full Windows reproduction and Git
integration. Evaluation is a later, separately reviewed command.
