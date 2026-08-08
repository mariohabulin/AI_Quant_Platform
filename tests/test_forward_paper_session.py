import json

import pandas as pd
import pytest

from src.forward_paper_session import JsonlForwardAudit, run_forward_paper


def trade_message(ts, price="100", size="1"):
    return {
        "channel": "market_trades",
        "events": [{"trades": [{"product_id": "BTC-USD", "price": price, "size": size, "time": ts}]}],
    }


def test_jsonl_audit_appends_parseable_records(tmp_path):
    path = tmp_path / "audit.jsonl"
    audit = JsonlForwardAudit(path)
    audit.append({"type": "TEST", "at": pd.Timestamp("2026-08-08T18:00:00Z")})
    audit.append({"type": "TEST2", "value": 2})
    rows = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]
    assert [row["type"] for row in rows] == ["TEST", "TEST2"]
    assert rows[0]["at"] == "2026-08-08T18:00:00+00:00"


def test_forward_runner_is_bounded_and_audited(tmp_path):
    messages = [
        trade_message("2026-08-08T18:00:10Z", "100"),
        trade_message("2026-08-08T18:01:10Z", "101"),
        trade_message("2026-08-08T18:02:10Z", "102"),
    ]
    audit_path = tmp_path / "forward.jsonl"
    output = []
    result = run_forward_paper(
        transport=messages,
        max_processed_bars=1,
        audit_path=audit_path,
        output=output.append,
        now_fn=lambda: pd.Timestamp("2026-08-08T18:01:20Z"),
    )
    assert result.processed_events == 1
    assert result.paper_orders == 0
    assert result.final_equity == pytest.approx(5000)
    rows = [json.loads(line) for line in audit_path.read_text(encoding="utf-8").splitlines()]
    assert [row["type"] for row in rows] == ["SESSION_START", "PAPER_EVENT", "SESSION_END"]
    assert rows[-1]["real_orders"] == 0
    assert "REAL orders=IMPOSSIBLE" in output[0]


def test_forward_runner_rejects_invalid_bound(tmp_path):
    with pytest.raises(ValueError, match="positive integer"):
        run_forward_paper(transport=[], max_processed_bars=0, audit_path=tmp_path / "x.jsonl")
