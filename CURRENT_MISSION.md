# CURRENT MISSION — Phase 3 Market Regime Detection

## Objective

Explain where a frozen strategy's unseen performance occurs by detecting causal market regimes and conditioning OOS trade evidence on those regimes.

## Current Priorities

- detect trend state as BULLISH / BEARISH / SIDEWAYS
- detect volatility state as LOW / NORMAL / HIGH
- guarantee causal labels with no future leakage
- preserve an explicit UNKNOWN warm-up state
- attribute unseen OOS trades to the regime at trade entry
- report regime-level trade count, net P&L, average P&L and win rate
- keep regime evidence diagnostic; do not select strategies yet
- preserve deterministic behavior and full backward compatibility
- keep all automated tests passing

## Regime Detection v1

Trend uses ATR-normalized fast/slow EMA separation. Volatility uses normalized ATR relative to its trailing median. Thresholds are explicit and configurable.

This layer answers *where* evidence appears. It does not yet claim causality, optimize parameters, allocate capital, or authorize live trading.

## Next Mission

After regime detection is proven, connect regime-conditioned evidence across strategies/assets, then define the Risk Engine before paper trading.

Do not introduce the Strategy Optimizer yet.
