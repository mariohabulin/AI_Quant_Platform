# Kraken BTC/ETH/XRP AI-Driven V2 Round 2 Discovery Runner Protocol V1

Protocol ID: `kraken-btc-eth-xrp-ai-driven-v2-round-2-discovery-runner-v1`

Status: `IMPLEMENTED_REVIEWED_NO_RUN_AUTHORIZATION`

## Purpose

This protocol freezes a one-shot, Development-only discovery runner for the
seven pre-registered Round 2 asset-family routes under both unchanged cost
profiles. It does not create a leaderboard, choose a strategy, authorize
Candidate v2 or open Calibration or Evaluation.

Round 2 is the second of two permitted discovery rounds. Its runner may only
test the three new registered hypotheses and their asymmetric asset scopes. It
cannot restore retired range routes or retired XRP trend/breakout routes.

## Frozen route semantics

The exact asset-major route order is:

1. `BTC-USD|CAPITULATION_RECOVERY`
2. `BTC-USD|VOLATILITY_BREAKOUT`
3. `BTC-USD|TREND_PULLBACK_CONTINUATION`
4. `ETH-USD|CAPITULATION_RECOVERY`
5. `ETH-USD|VOLATILITY_BREAKOUT`
6. `ETH-USD|TREND_PULLBACK_CONTINUATION`
7. `XRP-USD|CAPITULATION_RECOVERY`

- Each route/profile path receives an independent USD 5,000 research ledger.
  These ledgers make absolute route gates comparable; they are not simultaneous
  portfolio allocations.
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
a winner, combine routes or generate automatic ranking.

## Immutable lineage

The runner is bound to Round 2 configuration SHA-256
`2d591b048caa6ad123496b1ce1fcf4e523f924a9985737959d15cc8ddc1820c1`
and immutable Round 1 report SHA-256
`3ce14fda95f657c0b671b74c702d55ec4102da303e9e033ebaf0e02ff5c2fa9b`.
Round 1 and Reference A remain closed and cannot be rerun or reinterpreted by
this runner.

## Data and evidence boundary

The runner reuses the exact locked Development reader. Full source files are
hashed as opaque bytes, while only rows before `2024-04-01T00:00:00Z` may be
parsed. Calibration and Evaluation parsed-row counts must remain zero.

One execution requires exact phrase
`EXECUTE_KRAKEN_AI_V2_ROUND_2_DISCOVERY_ONCE`, an external dataset directory
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

Implementing and reviewing this runner is not permission to execute it. One
real Round 2 Development discovery run requires a separate operator decision
after Windows regression, hash-bound review, commit and clean-worktree
verification.
