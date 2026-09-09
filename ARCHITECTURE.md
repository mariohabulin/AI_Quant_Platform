# Architecture

## Active repository

The active tree contains only reusable components:

- market-data validation and feed health;
- features, regimes, strategies, backtesting, walk-forward and out-of-sample checks;
- risk, protective exits, paper broker and paper-readiness controls;
- operational monitoring, replay consistency and compact research evidence;
- focused tests for the retained core.

The five root documents are the project control plane: `VISION.md`, `ARCHITECTURE.md`, `ROADMAP.md`, `CURRENT_MISSION.md`, and `LOG.md`.

## Data boundary

Large market archives, source locks, trained artifacts and immutable evidence packages stay outside Git. The repository stores code and short state summaries, not raw datasets or generated research reports.

## Research boundary

The generic lifecycle is:

1. Development may inspect only authorized Development data.
2. Calibration and Evaluation remain sealed until separately authorized.
3. A result must include realistic costs, stability checks and a checksum.
4. Paper or live execution requires a new explicit decision.

## History

Commit `2aaef5420915ffdd386c5fac7295f87ef1045e8d` is the complete pre-cleanup archive containing every former protocol, experiment runner, test and tracked result. Deleted active-tree files can be recovered from that commit without keeping them in day-to-day work.
