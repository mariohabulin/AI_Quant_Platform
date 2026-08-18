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

The current committed configuration sets `AI_ALPHA_SESSION_BARS=1440`, which is
approximately twenty-four hours of fresh one-minute PAPER evidence. This
duration increase is authorized by the successful 720-bar gate; it does not
change market-data handling, Strategy, Risk or execution behavior. Changing the
bound requires a reviewed repository change followed by the non-activating
installer; do not edit the deployed file ad hoc. The service remains disabled
at boot and every start remains an explicit operator action.

## Bounded restart/resume gate

Start the configured PAPER service, observe at least one checkpoint, then issue
one controlled restart when restart evidence is part of the active gate:

```bash
if reset_output="$(systemctl reset-failed ai-alpha-paper.service 2>&1)"; then
    :
elif printf '%s\n' "${reset_output}" | \
        grep -Fq "Unit ai-alpha-paper.service not loaded"; then
    load_state="$(systemctl show ai-alpha-paper.service \
        --property=LoadState --value)"
    if [ "${load_state}" != "loaded" ]; then
        printf '%s\n' "Installed PAPER unit is not loadable." >&2
        exit 1
    fi
    printf '%s\n' \
        "PAPER unit was unloaded; no retained start-limit counter exists."
else
    printf '%s\n' "${reset_output}" >&2
    exit 1
fi
systemctl start ai-alpha-paper.service
journalctl -u ai-alpha-paper.service -n 30 --no-pager
systemctl restart ai-alpha-paper.service
journalctl -u ai-alpha-paper.service -n 60 --no-pager
```

The guarded `reset-failed` attempt explicitly opens a fresh two-start
supervision budget: the initial start plus no more than one automatic failure
restart. systemd may garbage-collect a successful inactive unit; unloading also
flushes its start-rate counters. On the validated host this state is reported
exactly as `Unit ai-alpha-paper.service not loaded`. Only that exact branch may
continue after confirming that the installed unit file resolves with
`LoadState=loaded`, because no retained start-limit counter remains to reset.
Any other `reset-failed` error aborts activation. Do not replace this guard with
`|| true` or otherwise hide permission, configuration or manager failures.

Do not reset the budget while the gate is running. A new manual gate requires
another explicit review and the guarded reset procedure after the prior service
is inactive. A deliberate `systemctl restart` also consumes the second start,
so it leaves no automatic recovery start in that same reviewed budget.

The post-restart `SESSION_START` record must contain `resumed=true`. The final
session must end with `MAX_BARS`, `REAL_orders=0`, a PASS forward report and an
OK/WARNING-free Operational Monitoring result before the gate is accepted.

An unexpected process failure must append `PROCESS_INCIDENT`. Before restart it
is classified as `CRITICAL / FAILED / PROCESS_FAILURE`; after restart it remains
visible as `PREVIOUS_PROCESS_FAILURE WARNING` throughout that recovery attempt.
A later healthy session is not allowed to erase the incident from append-only
audit evidence.

Every inbound Coinbase envelope carrying `sequence_num` is checked against one
connection-local stream before channel routing and before OHLCV aggregation. A
validated CPX22 read-only probe observed `market_trades=0`, two `subscriptions`
acknowledgements at `1/2`, `market_trades=3`, `heartbeats=4` and then every
cross-channel sequence through 39. Do not filter sequence observation to the
trade channel. Only `market_trades` payloads may enter aggregation.

A lower or equal sequence is discarded as a complete provider message and
recorded as `PROVIDER_MESSAGE_REPLAY_DROPPED`; the forward report exposes the
total as `message_replay_drops`. After a sequence-integrity reconnect, any
completed minute that began before the socket's trusted live boundary is
discarded as `PROVIDER_SEQUENCE_BOUNDARY_BAR_DROPPED`, exposed as
`sequence_boundary_drops`, and reconstructed through exact REST continuity
before a later fully observed live bar may trade. These handled records do not
enter Feed Health, Strategy, Risk or PaperBroker and do not by themselves make
monitoring non-OK.

A forward sequence gap on any sequenced channel never reaches aggregation. It
closes the untrusted socket as `PROVIDER_SEQUENCE_GAP`, retains the observed
provider channel and enters the existing bounded reconnect plus exact REST
continuity path. Invalid sequence evidence is classified as
`PROVIDER_SEQUENCE_INVALID`. Missing sequence on a `market_trades` payload is
`PROVIDER_SEQUENCE_MISSING`; a non-market control envelope without the optional
field remains transparent and the next sequenced envelope supplies the
continuity check.
Review all such disconnect causes, recovery evidence and final continuity;
heartbeats alone do not reset this recovery budget—a validly sequenced `market_trades` payload must arrive on the new socket. Reconnect exhaustion
remains `TRANSPORT_FATAL`. This provider-envelope guard
does not authorize widening the two-second event-time window or dropping a
genuinely late trade that arrived in a correctly sequenced message.

An explicit `market_trades` event with `type=snapshot` is provider state, not a
new incremental 250-ms update batch. It is sequence-validated first, then its
trade payload is excluded before OHLCV aggregation and recorded as
`PROVIDER_SNAPSHOT_BOUNDARY`. Snapshot trades never enter Strategy, Risk or
PaperBroker. The in-progress WebSocket minute is reset because its complete
incremental coverage can no longer be proven.

The first completed partial minute before the trusted post-snapshot boundary is
recorded as `PROVIDER_SNAPSHOT_BOUNDARY_BAR_DROPPED` and reconstructed through
the existing exact non-tradable REST path before the next full live bar may
trade. A startup snapshot must preserve the existing `RESTART` boundary and its
larger startup catch-up allowance. Review `snapshot_boundaries` and
`snapshot_boundary_drops` in the forward report; these handled counters do not
fail a gate by themselves when REST recovery is exact, monitoring remains OK and
all other acceptance conditions pass. Any future `LATE_TRADE_REJECTED` should
identify `event_type=update`; an ordering fatal attributed to `snapshot` means
this boundary did not hold and the run must be rejected.

A provider may also emit an in-band nonzero-sequence snapshot and then include
snapshot-era history in a later, correctly sequenced `update`. Every snapshot
therefore establishes a trusted event-time floor at the next full minute.
Subsequent trades strictly before that floor are quarantined before the reorder
heap as `PROVIDER_SNAPSHOT_QUARANTINE_TRADES_DROPPED`; review their snapshot and
message sequences, trade IDs/times and `trusted_live_bucket`. The forward report
totals these rows as `snapshot_quarantine_trades`. They never enter OHLCV, Feed
Health, Strategy, Risk or PaperBroker, and the suppressed boundary minute is
reconstructed only through exact non-tradable REST recovery.

This exception applies only to provider history before the trusted snapshot
floor. A trade at or after the trusted snapshot floor remains subject to the
unchanged two-second event-time rule and is still fatal if it arrives behind an
active later minute. Do not classify arbitrary late updates as snapshot history,
raise the reorder window, or bypass the exact recovery gate.

A trade beyond the reviewed two-second event-time watermark remains fail-closed.
The attempt records `LATE_TRADE_REJECTED` timing evidence, closes as
`ORDERING_FATAL`, exits non-zero and consumes the single automatic recovery
start. Review the recorded trade, `trade_id`, provider message sequence/time,
watermark and measured lateness before classifying the cause. Do not widen the
reorder window from a generic exception message. A controlled
`systemctl stop` instead closes as `OPERATOR_STOP`, returns accepted status 130
and is reported as `WARNING / STOPPED` without stale-running alerts.

For the current 24-hour gate, do not inject a restart or process failure.
Require 1,440/1,440 processed bars, zero rejected bars, `audit_complete=True`,
`observed_gap=0.0m`, zero recovery failures, zero reconnect exhaustion,
100% reconnect success whenever disconnects occur, `MAX_BARS`,
`REAL_orders=0`, systemd `Result=success`, `ExecMainStatus=0`, `NRestarts=0`
and final Operational Monitoring status `OK`. Transport disconnect, reconnect
and outage metrics must be retained even when hybrid recovery preserves
continuity. Any process incident, automatic restart, `CRITICAL` result or
`PREVIOUS_PROCESS_FAILURE` warning makes the soak non-passing until explicitly
reviewed; it is never silently upgraded to an endurance pass. This bounded
24-hour result is operational endurance evidence, not profitability evidence,
and a multi-day soak remains gated until it passes.

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
