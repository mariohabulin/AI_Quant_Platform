# AI Alpha Cloud Service Supervision

This package installs a bounded PAPER-only forward session and a recurring
read-only Operational Monitoring timer on the validated Ubuntu/systemd host.
It does not install exchange credentials, enable real execution, start a
trading process or enable a boot-time service.

## Safety contract

- The forward service runs as the passwordless, non-login `ai-alpha` system
  identity rather than `root`.
- `src.cloud_readiness` must pass immediately before every process start.
- PAPER mode, disabled real execution and persistent `/var/lib/ai-alpha`
  audit/state paths remain fixed in the reviewed unit.
- The session bound is installed from the committed `ai-alpha-paper.env` as a
  root-owned configuration. The same `AI_ALPHA_SESSION_BARS` value gates both
  Cloud Runtime Readiness and the forward runner, preventing configuration
  drift between validation and execution.
- `Restart=on-failure` permits at most one automatic recovery start after the
  initial reviewed start. `StartLimitIntervalSec=infinity` and
  `StartLimitBurst=2` prevent an unbounded overnight restart loop. A normal
  `MAX_BARS` completion does not restart. Operator stop uses `SIGINT`, closes
  the audit as `OPERATOR_STOP`, and continuity is restored on the next start.
- `ExecStopPost` appends a `PROCESS_INCIDENT` only for a non-successful systemd
  result. The recorder is evidence-only and its own exit status is ignored, so
  it cannot create or suppress a PAPER restart.
- The monitor calls the existing read-only policy every minute. `OK` and
  `WARNING` are accepted unit outcomes; `CRITICAL` remains a systemd failure.
- Journald retains process output and monitoring decisions. External
  notification delivery remains outside this milestone.

## Controlled installation

From `/opt/ai-alpha` as `root`:

```bash
bash deploy/systemd/install.sh
systemctl cat ai-alpha-paper.service
systemctl cat ai-alpha-monitor.service
systemctl cat ai-alpha-monitor.timer
```

Installation deliberately performs no `start`, `restart`, `enable` or
`enable --now`. Activation remains an explicit operator decision after unit
review.

## Reviewed session bound

The current committed configuration sets `AI_ALPHA_SESSION_BARS=720`, which is
approximately twelve hours of fresh one-minute PAPER evidence. Changing the
bound requires a reviewed repository change followed by the non-activating
installer; do not edit the deployed file ad hoc. The service remains disabled
at boot and every start remains an explicit operator action.

## Bounded restart/resume gate

Start the configured PAPER service, observe at least one checkpoint, then issue
one controlled restart when restart evidence is part of the active gate:

```bash
systemctl reset-failed ai-alpha-paper.service
systemctl start ai-alpha-paper.service
journalctl -u ai-alpha-paper.service -n 30 --no-pager
systemctl restart ai-alpha-paper.service
journalctl -u ai-alpha-paper.service -n 60 --no-pager
```

`reset-failed` is required immediately before each reviewed activation because
it explicitly opens a fresh two-start supervision budget: the initial start
plus no more than one automatic failure restart. Do not reset that budget while
the gate is running. A new manual gate requires another explicit review and
reset after the prior service is inactive. A deliberate `systemctl restart`
also consumes the second start, so it leaves no automatic recovery start in
that same reviewed budget.

The post-restart `SESSION_START` record must contain `resumed=true`. The final
session must end with `MAX_BARS`, `REAL_orders=0`, a PASS forward report and an
OK/WARNING-free Operational Monitoring result before the gate is accepted.

An unexpected process failure must append `PROCESS_INCIDENT`. Before restart it
is classified as `CRITICAL / FAILED / PROCESS_FAILURE`; after restart it remains
visible as `PREVIOUS_PROCESS_FAILURE WARNING` throughout that recovery attempt.
A later healthy session is not allowed to erase the incident from append-only
audit evidence.

A trade beyond the reviewed two-second event-time watermark remains fail-closed.
The attempt records `LATE_TRADE_REJECTED` timing evidence, closes as
`ORDERING_FATAL`, exits non-zero and consumes the single automatic recovery
start. Do not widen the reorder window from a generic exception message; review
the recorded trade, watermark and measured lateness first. A controlled
`systemctl stop` instead closes as `OPERATOR_STOP`, returns accepted status 130
and is reported as `WARNING / STOPPED` without stale-running alerts.

For the current overnight gate, do not inject a restart or process failure.
Require 720/720 processed bars, zero rejected bars, `audit_complete=True`,
`observed_gap=0.0m`, zero recovery failures, zero reconnect exhaustion,
100% reconnect success whenever disconnects occur, `MAX_BARS`,
`REAL_orders=0`, systemd `Result=success`, `ExecMainStatus=0`, `NRestarts=0`
and final Operational Monitoring status `OK`. Transport disconnect, reconnect
and outage metrics must be retained even when hybrid recovery preserves
continuity. Any process incident, automatic restart, `CRITICAL` result or
`PREVIOUS_PROCESS_FAILURE` warning makes the soak non-passing until explicitly
reviewed; it is never silently upgraded to an endurance pass.

## Monitoring schedule

Enable only the read-only timer after installation review:

```bash
systemctl enable --now ai-alpha-monitor.timer
systemctl list-timers ai-alpha-monitor.timer --no-pager
journalctl -u ai-alpha-monitor.service -n 30 --no-pager
```

Stop the bounded paper service without disabling monitoring:

```bash
systemctl stop ai-alpha-paper.service
```

Do not enable `ai-alpha-paper.service` at boot during this milestone.
