# Roadmap

## Completed

- Built and tested the reusable research, risk, paper-trading and monitoring core.
- Locked the Kraken BTC/ETH/XRP archive and separated Development, Calibration and Evaluation.
- Rejected the Kraken 12-hour AI/regime-gated path: no viable hypothesis; `HOLD_CASH`.
- Rejected Weekly Persistent-UP Momentum V1 on 341 valid events: no asset passed all gates; `HOLD_CASH`.
- Audited zero-cost US equity sources and found six missing point-in-time capabilities.
- Sent Alpaca support a written request covering delisted history, identifiers, storage rights and Croatian eligibility.
- Removed closed experiment machinery from the active tree; full history remains at commit `2aaef5420915ffdd386c5fac7295f87ef1045e8d`.

## Current decision

Pause research expansion. Do not create another crypto variation, runner, protocol or evidence wrapper.

## Next

1. Review Alpaca's written answer when it arrives.
2. Decide `GO`, `PIVOT`, or `STOP` for the whole project.
3. If `GO`, prove one minimum data path before writing strategy-specific infrastructure.
4. Open Calibration, Evaluation, paper trading or live trading only under separate explicit authorization.
