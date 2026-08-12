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
- `Restart=on-failure` is rate-limited. A normal `MAX_BARS` completion does not
  restart. Operator stop/restart uses `SIGINT` and continuity is restored from
  the atomic state file on the next start.
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

The current committed configuration sets `AI_ALPHA_SESSION_BARS=180`, which is
approximately three hours of fresh one-minute PAPER evidence. Changing the
bound requires a reviewed repository change followed by the non-activating
installer; do not edit the deployed file ad hoc. The service remains disabled
at boot and every start remains an explicit operator action.

## Bounded restart/resume gate

Start the configured PAPER service, observe at least one checkpoint, then issue
one controlled restart when restart evidence is part of the active gate:

```bash
systemctl start ai-alpha-paper.service
journalctl -u ai-alpha-paper.service -n 30 --no-pager
systemctl restart ai-alpha-paper.service
journalctl -u ai-alpha-paper.service -n 60 --no-pager
```

The post-restart `SESSION_START` record must contain `resumed=true`. The final
session must end with `MAX_BARS`, `REAL_orders=0`, a PASS forward report and an
OK/WARNING-free Operational Monitoring result before the gate is accepted.

For the current multi-hour gate, require 180/180 processed bars,
`audit_complete=True`, `observed_gap=0.0m`, zero recovery failures,
`MAX_BARS`, `REAL_orders=0` and no `CRITICAL` monitoring decision. Transport
disconnect, reconnect and outage metrics must be retained even when hybrid
recovery preserves continuity; a transport warning is not silently upgraded to
a production-readiness pass.

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
