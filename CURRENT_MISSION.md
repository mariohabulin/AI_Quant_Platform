# CURRENT MISSION — Paper Trading Foundation

## Objective

Build a deterministic Paper Broker boundary that can execute already-authorized market orders, maintain account/position state and preserve auditable order lifecycle evidence without mixing strategy or risk responsibilities into execution.

## Current Priorities

- add deterministic long-only market BUY/SELL execution
- model commission, slippage and spread consistently with research execution assumptions
- separate order submission from fill/cancel lifecycle
- maintain cash, position quantity, average entry price, realized P&L and account equity
- reject unaffordable BUY orders and oversized SELL orders without mutating account state
- preserve explicit `SUBMITTED / FILLED / REJECTED / CANCELLED` order evidence
- keep Strategy Engine and Risk Engine outside Paper Broker responsibilities
- document deferred paper/live execution capabilities and the reason each is deferred
- keep all automated tests passing

## Definition of Done

Paper Broker v1 provides deterministic market-order lifecycle, execution-cost modelling and auditable account state through a standalone execution boundary suitable for later orchestration by Paper Trading Engine v1.

## Next Mission

Build Paper Trading Engine v1 to orchestrate deterministic market events through Strategy Engine → Risk Engine → Paper Broker. Real streaming data and live broker adapters remain deliberately deferred until the deterministic orchestration path is validated.
