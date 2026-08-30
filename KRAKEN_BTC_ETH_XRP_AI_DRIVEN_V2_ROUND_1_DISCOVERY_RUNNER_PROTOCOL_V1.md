# Kraken BTC/ETH/XRP AI-Driven V2 Round 1 Discovery Runner Protocol V1

Protocol ID: `kraken-btc-eth-xrp-ai-driven-v2-round-1-discovery-runner-v1`

Status: `IMPLEMENTED_REVIEWED_NO_RUN_AUTHORIZATION`

## Purpose

This protocol freezes a one-shot, Development-only discovery runner for the
four pre-registered Round 1 families across BTC-USD, ETH-USD and XRP-USD. It
creates twelve asset-family route reports under both frozen cost profiles. It
does not create a leaderboard, choose a strategy, authorize Candidate v2 or
open Calibration or Evaluation.

## Frozen route semantics

- Route order is asset-major BTC, ETH, XRP and then capitulation recovery,
  trend-pullback continuation, range mean reversion and volatility breakout.
- Each path receives an independent USD 5,000 research ledger. These ledgers
  make absolute route gates comparable; they
  are not simultaneous portfolio allocations.
- Baseline and stress paths consume the same deterministic causal signal
  contract and their respective frozen adverse execution-cost profiles.
- A trade belongs to the chronological Development slice containing its entry
  timestamp. Positions may cross slice boundaries because slices are reporting
  windows, not context resets.
- A known daily gap resets feature and signal state. Pending entries are
  canceled. An open position at a gap halts that route/profile as inconclusive
  and remains unresolved.
- At the Development terminal boundary, an open position remains unresolved.
  Synthetic terminal force-close is prohibited.
- Existing-position exits occur before a pending entry at the same open.
  Entry-bar protective handling remains mandatory and same-bar stop/target
  ambiguity remains stop-first.

## Frozen route and round gates

All pre-registered absolute gates apply without ranking. Minimum trade and
slice counts, nonnegative-slice coverage, unresolved-position count and the
largest-trade share limit must pass in both baseline and stress profiles.
Baseline/stress expectancy, profit factor and marked drawdown use their named
profile thresholds. A no-trade slice does not count as nonnegative.

A route failing any gate is `HOLD_CASH`. Round interest requires at least two
eligible routes spanning at least two assets. Multiple eligible families for
one asset require `SEPARATE_PORTFOLIO_REVIEW_REQUIRED`; the runner cannot pick
a winner or combine routes.

## Data and evidence boundary

The runner reuses the exact locked Development reader. Full source files are
hashed as opaque bytes, while only rows before `2024-04-01T00:00:00Z` may be
parsed. Calibration and Evaluation parsed-row counts must remain zero.

One execution requires exact phrase
`EXECUTE_KRAKEN_AI_V2_ROUND_1_DISCOVERY_ONCE`, an external dataset directory
and a disjoint external evidence root. Final or staging evidence presence
blocks a repeat. Canonical JSON plus SHA-256 sidecar are written in staging,
renamed atomically and independently locked.

## Explicit nonauthorization at review

- discovery runner implemented: `true`
- one-shot evidence lock implemented: `true`
- development data opened: `false`
- development run authorized: `false`
- performance evaluation executed: `false`
- calibration data opened: `false`
- evaluation data opened: `false`
- automatic ranking generated: `false`
- automatic strategy selection: `false`
- Candidate v2 authorized: `false`
- real orders submitted: `false`
- PAPER, cloud and live authorized: `false`

Reference A remains closed immutable feedback lineage. Implementing and
reviewing this runner is not permission to execute it. One real Development
discovery run requires a separate operator decision after Windows regression,
hash-bound review, commit and clean-worktree verification.
