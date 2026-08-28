import hashlib
import json
import os
import sys

import pandas as pd
import pytest

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src")))

from blinded_daily_replay import BlindedDailyReplaySession
from blinded_replay_evidence import (
    BlindedReplayEvidenceLock,
    DurableBlindedReplayJournal,
)
from research_evidence import canonical_json_bytes

DATASET_ID = "test-kraken-daily-lock-v2"
MANIFEST_SHA256 = "a" * 64
PROTOCOL_ID = "test-bounded-blinded-replay-v1"


def market_frame(rows=32):
    index = pd.date_range("2024-01-01T00:00:00Z", periods=rows, freq="D", tz="UTC")
    close = pd.Series([100.0 + value for value in range(rows)], index=index)
    return pd.DataFrame(
        {
            "Open": close - 0.5,
            "High": close + 1.0,
            "Low": close - 1.0,
            "Close": close,
            "Volume": 1000.0 + pd.Series(range(rows), index=index),
        },
        index=index,
    )


def journal(tmp_path, name="episode"):
    return DurableBlindedReplayJournal(
        tmp_path / name,
        dataset_id=DATASET_ID,
        manifest_sha256=MANIFEST_SHA256,
        protocol_id=PROTOCOL_ID,
        asset="BTC-USD",
        episode_id="btc_episode_1",
    )


def finish(session, actions):
    for action in actions:
        session.record_decision(action, f"Recorded {action} decision.")
        session.advance()


def test_each_decision_is_canonical_chained_and_durable_before_advance(tmp_path):
    evidence = journal(tmp_path)
    session = BlindedDailyReplaySession(
        "BTC-USD", market_frame(), context_bars=30, decision_sink=evidence
    )

    first = session.record_decision("SKIP", "No setup.")
    decision_file = evidence.decision_directory / "000000.json"
    sidecar_file = evidence.decision_directory / "000000.json.sha256"

    assert decision_file.exists()
    payload = json.loads(decision_file.read_bytes())
    digest = hashlib.sha256(decision_file.read_bytes()).hexdigest()
    assert decision_file.read_bytes() == canonical_json_bytes(payload)
    assert sidecar_file.read_bytes() == f"{digest}  000000.json\n".encode("ascii")
    assert payload["decision"] == first.as_dict()
    assert payload["previous_decision_sha256"] is None
    assert payload["future_bars_persisted"] is False

    session.advance()
    second = session.record_decision("SKIP", "Still no setup.")
    second_payload = json.loads(
        (evidence.decision_directory / "000001.json").read_bytes()
    )
    assert second_payload["decision"] == second.as_dict()
    assert second_payload["previous_decision_sha256"] == digest


def test_completed_episode_is_atomically_promoted_without_performance(tmp_path):
    evidence = journal(tmp_path)
    session = BlindedDailyReplaySession(
        "BTC-USD", market_frame(), context_bars=30, decision_sink=evidence
    )
    finish(session, ["SKIP", "SKIP", "SKIP"])

    recorded = evidence.finalize(session.summary())
    raw = recorded.evidence_path.read_bytes()
    payload = json.loads(raw)
    digest = hashlib.sha256(raw).hexdigest()

    assert raw == canonical_json_bytes(payload)
    assert recorded.evidence_sha256 == digest
    assert recorded.checksum_path.read_bytes() == (
        f"{digest}  replay_evidence.json\n".encode("ascii")
    )
    assert recorded.decision_count == 3
    assert recorded.terminal_position_resolution == "FLAT_AT_EPISODE_END"
    assert payload["performance_evaluation_executed"] is False
    assert payload["strategy_selection_executed"] is False
    assert payload["synthetic_exit_inserted"] is False
    assert payload["position_carried_to_another_episode"] is False
    assert not evidence.staging_directory.exists()

    locked = BlindedReplayEvidenceLock().lock(recorded.evidence_path.parent)
    assert locked.evidence_sha256 == recorded.evidence_sha256
    assert len(locked.decisions) == 3
    assert locked.manifest == payload


def test_open_terminal_position_remains_unresolved_without_synthetic_exit(tmp_path):
    evidence = journal(tmp_path)
    session = BlindedDailyReplaySession(
        "BTC-USD", market_frame(), context_bars=30, decision_sink=evidence
    )
    finish(session, ["ENTER", "HOLD", "HOLD"])

    recorded = evidence.finalize(session.summary())
    payload = json.loads(recorded.evidence_path.read_bytes())

    assert recorded.terminal_position_state == "LONG"
    assert recorded.terminal_position_resolution == (
        "OPEN_POSITION_UNRESOLVED_AT_EPISODE_END"
    )
    assert payload["synthetic_exit_inserted"] is False
    assert payload["position_carried_to_another_episode"] is False
    assert "profit" not in str(payload).lower()
    assert "return" not in str(payload).lower()


def test_existing_final_or_incomplete_staging_evidence_blocks_retry(tmp_path):
    first = journal(tmp_path)
    with pytest.raises(FileExistsError, match="Incomplete"):
        journal(tmp_path)

    session = BlindedDailyReplaySession(
        "BTC-USD", market_frame(), context_bars=30, decision_sink=first
    )
    finish(session, ["SKIP", "SKIP", "SKIP"])
    first.finalize(session.summary())
    with pytest.raises(FileExistsError, match="already exists"):
        journal(tmp_path)


def test_journal_rejects_wrong_asset_sequence_and_incomplete_finalization(tmp_path):
    evidence = journal(tmp_path)
    wrong_asset = BlindedDailyReplaySession("ETH-USD", market_frame())
    decision = wrong_asset.record_decision("SKIP", "No setup.")
    with pytest.raises(ValueError, match="asset"):
        evidence.append(decision)

    session = BlindedDailyReplaySession("BTC-USD", market_frame())
    decision = session.record_decision("SKIP", "No setup.")
    evidence.append(decision)
    with pytest.raises(ValueError, match="sequence"):
        evidence.append(decision)
    with pytest.raises(ValueError, match="completed"):
        evidence.finalize(session.summary())


def completed_episode(tmp_path):
    evidence = journal(tmp_path)
    session = BlindedDailyReplaySession(
        "BTC-USD", market_frame(), context_bars=30, decision_sink=evidence
    )
    finish(session, ["SKIP", "SKIP", "SKIP"])
    return evidence.finalize(session.summary()).evidence_path.parent


def test_independent_lock_rejects_changed_decision_bytes(tmp_path):
    output = completed_episode(tmp_path)
    decision = output / "decisions" / "000001.json"
    decision.write_bytes(decision.read_bytes().replace(b"Recorded", b"Altered"))

    with pytest.raises(ValueError, match="canonical|SHA-256"):
        BlindedReplayEvidenceLock().lock(output)


def test_independent_lock_rejects_resigned_promotional_manifest(tmp_path):
    output = completed_episode(tmp_path)
    manifest_path = output / "replay_evidence.json"
    payload = json.loads(manifest_path.read_bytes())
    payload["performance_evaluation_executed"] = True
    raw = canonical_json_bytes(payload)
    digest = hashlib.sha256(raw).hexdigest()
    manifest_path.write_bytes(raw)
    (output / "replay_evidence.sha256").write_bytes(
        f"{digest}  replay_evidence.json\n".encode("ascii")
    )

    with pytest.raises(ValueError, match="performance_evaluation_executed"):
        BlindedReplayEvidenceLock().lock(output)


def test_independent_lock_rejects_resigned_unknown_decision_field(tmp_path):
    output = completed_episode(tmp_path)
    decision_path = output / "decisions" / "000002.json"
    decision_payload = json.loads(decision_path.read_bytes())
    decision_payload["profit"] = 1000
    decision_raw = canonical_json_bytes(decision_payload)
    decision_digest = hashlib.sha256(decision_raw).hexdigest()
    decision_path.write_bytes(decision_raw)
    decision_path.with_name("000002.json.sha256").write_bytes(
        f"{decision_digest}  000002.json\n".encode("ascii")
    )

    manifest_path = output / "replay_evidence.json"
    manifest = json.loads(manifest_path.read_bytes())
    manifest["decision_evidence"][2]["sha256"] = decision_digest
    manifest["final_decision_sha256"] = decision_digest
    manifest_raw = canonical_json_bytes(manifest)
    manifest_digest = hashlib.sha256(manifest_raw).hexdigest()
    manifest_path.write_bytes(manifest_raw)
    (output / "replay_evidence.sha256").write_bytes(
        f"{manifest_digest}  replay_evidence.json\n".encode("ascii")
    )

    with pytest.raises(ValueError, match="fields are not exact"):
        BlindedReplayEvidenceLock().lock(output)
