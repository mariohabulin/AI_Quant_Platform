# AI Quant Platform

A compact, evidence-driven research core for testing trading hypotheses without exposing sealed data early or authorizing live trading.

The project is currently paused pending a direction decision and Alpaca's written response about zero-cost point-in-time US equity data.

Project control lives in five short files:

- [VISION.md](VISION.md) — purpose and non-negotiable rules
- [ARCHITECTURE.md](ARCHITECTURE.md) — active technical structure
- [ROADMAP.md](ROADMAP.md) — completed work and next decision
- [CURRENT_MISSION.md](CURRENT_MISSION.md) — exact current state
- [LOG.md](LOG.md) — concise decision history

Run the retained core tests with:

```bash
python -m pytest -q
```

Large datasets and immutable evidence remain outside Git. The complete pre-cleanup project is recoverable from commit `2aaef5420915ffdd386c5fac7295f87ef1045e8d`.
