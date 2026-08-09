"""Deterministic report for the latest forward-paper JSONL session.

The reporter is intentionally read-only. It summarizes the latest SESSION_START
through SESSION_END block and fails closed on malformed/incomplete audit data.
"""
from dataclasses import asdict, dataclass
import argparse
import json
from pathlib import Path
import sys


@dataclass(frozen=True)
class ForwardSessionReport:
    status: str
    processed_events: int
    rejected_events: int
    rebase_events: int
    paper_orders: int
    buy_signals: int
    sell_signals: int
    hold_signals: int
    filled_orders: int
    risk_allow: int
    risk_reduce: int
    risk_reject: int
    start_equity: float
    final_equity: float
    net_pnl: float
    max_drawdown: float
    final_position: float
    real_orders: int
    audit_complete: bool
    end_reason: str


def _read_rows(path):
    path = Path(path)
    if not path.exists() or not path.is_file():
        raise RuntimeError("Forward audit file does not exist.")
    rows = []
    for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        if not line.strip():
            continue
        try:
            row = json.loads(line)
        except json.JSONDecodeError as exc:
            raise RuntimeError(f"Forward audit contains invalid JSON at line {number}.") from exc
        if not isinstance(row, dict) or "type" not in row:
            raise RuntimeError(f"Forward audit record at line {number} is invalid.")
        rows.append(row)
    if not rows:
        raise RuntimeError("Forward audit is empty.")
    return rows


def _latest_session(rows):
    starts = [i for i, row in enumerate(rows) if row.get("type") == "SESSION_START"]
    if not starts:
        raise RuntimeError("Forward audit has no SESSION_START record.")
    start = starts[-1]
    session = rows[start:]
    ends = [i for i, row in enumerate(session) if row.get("type") == "SESSION_END"]
    if not ends:
        raise RuntimeError("Latest forward session is incomplete: SESSION_END is missing.")
    end = ends[0]
    trailing_session_start = any(row.get("type") == "SESSION_START" for row in session[1:end + 1])
    if trailing_session_start:
        raise RuntimeError("Forward audit session boundaries are inconsistent.")
    return session[:end + 1]


def build_forward_session_report(audit_path="runtime/forward_paper_audit.jsonl"):
    rows = _latest_session(_read_rows(audit_path))
    paper = [row for row in rows if row.get("type") == "PAPER_EVENT"]
    rejected = [row for row in rows if row.get("type") == "REJECTED_BAR"]
    rebases = [row for row in rows if row.get("type") in {"RESTART_REBASE", "RECONNECT_REBASE"}]
    end = rows[-1]

    if not paper:
        raise RuntimeError("Latest forward session has no PAPER_EVENT records to report.")

    snapshots = [row.get("snapshot", {}) for row in paper]
    events = [row.get("event", {}) for row in paper]
    equities = [float(snapshot["equity"]) for snapshot in snapshots]
    start_equity = equities[0]
    peak = equities[0]
    max_drawdown = 0.0
    for equity in equities:
        peak = max(peak, equity)
        if peak > 0:
            max_drawdown = max(max_drawdown, (peak - equity) / peak)

    signals = [int(event.get("signal", 0)) for event in events]
    risk_statuses = [str(event.get("risk_status", "")) for event in events]
    statuses = [str(event.get("status", "")) for event in events]
    real_orders_values = [int(row.get("real_orders", 0)) for row in rows if "real_orders" in row]
    real_orders = max(real_orders_values, default=0)
    final_equity = float(end.get("equity", equities[-1]))
    final_position = float(end.get("position", snapshots[-1].get("position_quantity", 0.0)))

    processed = int(end.get("processed_events", len(paper)))
    rejected_count = int(end.get("rejected_events", len(rejected)))
    complete = (
        rows[0].get("type") == "SESSION_START"
        and end.get("type") == "SESSION_END"
        and processed == len(paper)
        and rejected_count == len(rejected)
        and real_orders == 0
    )
    status = "PASS" if complete else "FAIL"

    return ForwardSessionReport(
        status=status,
        processed_events=processed,
        rejected_events=rejected_count,
        rebase_events=len(rebases),
        paper_orders=int(end.get("paper_orders", max((row.get("paper_orders", 0) for row in paper), default=0))),
        buy_signals=sum(signal > 0 for signal in signals),
        sell_signals=sum(signal < 0 for signal in signals),
        hold_signals=sum(signal == 0 for signal in signals),
        filled_orders=sum(status == "FILLED" for status in statuses),
        risk_allow=sum(status == "ALLOW" for status in risk_statuses),
        risk_reduce=sum(status == "REDUCE" for status in risk_statuses),
        risk_reject=sum(status == "REJECT" for status in risk_statuses),
        start_equity=start_equity,
        final_equity=final_equity,
        net_pnl=final_equity - start_equity,
        max_drawdown=max_drawdown,
        final_position=final_position,
        real_orders=real_orders,
        audit_complete=complete,
        end_reason=str(end.get("reason", "UNKNOWN")),
    )


def format_forward_session_report(report):
    return "\n".join([
        f"Extended Forward Session Report | status={report.status} | audit_complete={report.audit_complete}",
        f"bars: processed={report.processed_events} rejected={report.rejected_events} rebases={report.rebase_events}",
        f"signals: BUY={report.buy_signals} SELL={report.sell_signals} HOLD={report.hold_signals}",
        f"risk: ALLOW={report.risk_allow} REDUCE={report.risk_reduce} REJECT={report.risk_reject}",
        f"orders: paper={report.paper_orders} filled={report.filled_orders} REAL={report.real_orders}",
        f"equity: start={report.start_equity:.2f} final={report.final_equity:.2f} net_pnl={report.net_pnl:.2f} max_drawdown={report.max_drawdown:.4%}",
        f"final_position={report.final_position:.8f} end_reason={report.end_reason}",
    ])


def main(argv=None):
    parser = argparse.ArgumentParser(description="Report the latest audited forward-paper session.")
    parser.add_argument("--audit", default="runtime/forward_paper_audit.jsonl")
    parser.add_argument("--json", action="store_true", help="emit machine-readable JSON")
    args = parser.parse_args(argv)
    try:
        report = build_forward_session_report(args.audit)
    except Exception as exc:
        print(f"Forward session report failed safely: {type(exc).__name__}: {exc}", file=sys.stderr)
        return 1
    if args.json:
        print(json.dumps(asdict(report), sort_keys=True))
    else:
        print(format_forward_session_report(report))
    return 0 if report.status == "PASS" else 2


if __name__ == "__main__":
    raise SystemExit(main())
