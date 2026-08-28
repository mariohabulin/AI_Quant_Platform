import json
import os
import sys
from copy import deepcopy
from pathlib import Path

import pandas as pd
import pytest

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src")))

from kraken_blinded_replay_review import (
    CONTEXT_BARS,
    DATASET_ID,
    DATASET_LOCK_EVIDENCE_NORMALIZED_SHA256,
    DATASET_MANIFEST_SHA256,
    DECISION_BARS,
    EPISODE_ROWS,
    EVIDENCE_COMPONENT_NORMALIZED_SHA256,
    EXPECTED_MISSING_TIMESTAMPS,
    EXPECTED_OBSERVED_ROWS,
    REPLAY_COMPONENT_NORMALIZED_SHA256,
    REVIEW_PROTOCOL_ID,
    REVIEW_PROTOCOL_NORMALIZED_SHA256,
    KrakenBlindedReplayPreflight,
    load_dataset_lock_evidence,
    load_replay_review_protocol,
    load_reviewed_component,
    main,
    normalized_text_sha256,
    review_declaration,
)

ROOT = Path(__file__).resolve().parents[1]
LOCK_EVIDENCE = ROOT / "KRAKEN_BTC_ETH_XRP_DAILY_DATASET_LOCK_EVIDENCE_V2.md"
REVIEW_PROTOCOL = ROOT / "KRAKEN_BTC_ETH_XRP_BLINDED_REPLAY_REVIEW_PROTOCOL_V1.md"
REPLAY_COMPONENT = ROOT / "src" / "blinded_daily_replay.py"
EVIDENCE_COMPONENT = ROOT / "src" / "blinded_replay_evidence.py"
PREFLIGHT_EVIDENCE = (
    ROOT / "KRAKEN_BTC_ETH_XRP_BLINDED_REPLAY_PREFLIGHT_EVIDENCE_V1.md"
)
PREFLIGHT_EVIDENCE_NORMALIZED_SHA256 = (
    "ca5958b01370c222efd28c5149bb7a04e7627e0b71eef720db73116c7ccdfdf3"
)


def canonical_rows(asset):
    gaps = set(EXPECTED_MISSING_TIMESTAMPS[asset])
    rows = []
    for timestamp in pd.date_range(
        "2019-01-01T00:00:00Z", "2026-03-31T00:00:00Z", freq="D", tz="UTC"
    ):
        value = timestamp.strftime("%Y-%m-%dT%H:%M:%SZ")
        if value not in gaps:
            rows.append([value, "100", "101", "99", "100.5", "10"])
    assert len(rows) == EXPECTED_OBSERVED_ROWS[asset]
    return rows


class FakeLocked:
    def __init__(self):
        self.manifest_sha256 = DATASET_MANIFEST_SHA256
        self.assets = {
            asset: canonical_rows(asset)
            for asset in ("BTC-USD", "ETH-USD", "XRP-USD")
        }
        self.manifest = {
            "dataset_id": DATASET_ID,
            "source_mode": "OFFICIAL_OHLCVT_ARCHIVES_ONLY",
            "network_requests_executed": False,
            "assets": {
                asset: {
                    "missing_timestamps": list(EXPECTED_MISSING_TIMESTAMPS[asset])
                }
                for asset in self.assets
            },
        }


def test_review_contracts_and_components_are_exact_hash_bound():
    _, lock_digest = load_dataset_lock_evidence(LOCK_EVIDENCE)
    _, protocol_digest = load_replay_review_protocol(REVIEW_PROTOCOL)

    assert lock_digest == DATASET_LOCK_EVIDENCE_NORMALIZED_SHA256
    assert protocol_digest == REVIEW_PROTOCOL_NORMALIZED_SHA256
    assert normalized_text_sha256(REPLAY_COMPONENT) == REPLAY_COMPONENT_NORMALIZED_SHA256
    assert normalized_text_sha256(EVIDENCE_COMPONENT) == (
        EVIDENCE_COMPONENT_NORMALIZED_SHA256
    )
    assert load_reviewed_component(
        REPLAY_COMPONENT,
        REPLAY_COMPONENT_NORMALIZED_SHA256,
        "Replay component",
    ) == REPLAY_COMPONENT_NORMALIZED_SHA256


@pytest.mark.parametrize(
    "source, loader, error",
    [
        (LOCK_EVIDENCE, load_dataset_lock_evidence, "Dataset-lock evidence SHA256"),
        (REVIEW_PROTOCOL, load_replay_review_protocol, "protocol SHA256"),
    ],
)
def test_changed_contract_text_is_rejected(tmp_path, source, loader, error):
    changed = tmp_path / source.name
    changed.write_text(
        source.read_text(encoding="utf-8") + "changed\n", encoding="utf-8"
    )
    with pytest.raises(RuntimeError, match=error):
        loader(changed)


def test_changed_replay_component_is_rejected(tmp_path):
    changed = tmp_path / "blinded_daily_replay.py"
    changed.write_text(
        REPLAY_COMPONENT.read_text(encoding="utf-8") + "# changed\n",
        encoding="utf-8",
    )
    with pytest.raises(RuntimeError, match="Replay component SHA256"):
        load_reviewed_component(
            changed,
            REPLAY_COMPONENT_NORMALIZED_SHA256,
            "Replay component",
        )


def test_review_declaration_is_bounded_and_executes_nothing():
    declaration = review_declaration(
        LOCK_EVIDENCE,
        REVIEW_PROTOCOL,
        REPLAY_COMPONENT,
        EVIDENCE_COMPONENT,
    )

    assert declaration["status"].endswith("PREFLIGHT_REQUIRED")
    assert declaration["protocol_id"] == REVIEW_PROTOCOL_ID
    assert declaration["dataset_id"] == DATASET_ID
    assert declaration["dataset_manifest_sha256"] == DATASET_MANIFEST_SHA256
    assert declaration["asset_order"] == ["BTC-USD", "ETH-USD", "XRP-USD"]
    assert declaration["episode_count"] == 3
    assert declaration["episodes_per_asset"] == 1
    assert declaration["context_bars"] == CONTEXT_BARS == 30
    assert declaration["decision_bars_per_episode"] == DECISION_BARS == 60
    assert declaration["episode_rows"] == EPISODE_ROWS == 89
    assert declaration["selection_uses_ohlcv"] is False
    assert declaration["durable_decision_required_before_advance"] is True
    assert declaration["preflight_executed"] is False
    assert declaration["selected_timestamps_exposed"] is False
    assert declaration["real_replay_review_eligible"] is False
    assert declaration["real_replay_authorized"] is False
    assert declaration["real_chart_replay_executed"] is False
    assert declaration["performance_evaluation_executed"] is False
    assert declaration["candidate_v2_authorized"] is False
    assert declaration["bounded_forward_paper_authorized"] is False
    assert declaration["live_execution_authorized"] is False


def test_project_documents_record_sealed_preflight_and_next_review_boundary():
    roadmap = (ROOT / "ROADMAP.md").read_text(encoding="utf-8")
    mission = (ROOT / "CURRENT_MISSION.md").read_text(encoding="utf-8")
    architecture = (ROOT / "ARCHITECTURE.md").read_text(encoding="utf-8")
    vision = (ROOT / "VISION.md").read_text(encoding="utf-8")
    log = (ROOT / "LOG.md").read_text(encoding="utf-8")
    evidence = PREFLIGHT_EVIDENCE.read_text(encoding="utf-8")

    assert "[x] Execute one sealed preflight" in roadmap
    assert "one-episode-at-a-time" in roadmap
    assert "explicitly decide" in roadmap
    assert "SEALED PREFLIGHT PASS" in mission
    assert "Kraken Bounded Blinded Replay Review Boundary v1" in architecture
    assert "selected timestamps" in vision
    assert "Sealed Preflight Completed" in log
    for text in (roadmap, mission, architecture, log):
        assert "Candidate v2" in text
        assert "live" in text.lower()
    assert "fabricated" in vision
    assert "performance result" in vision
    assert normalized_text_sha256(PREFLIGHT_EVIDENCE) == (
        PREFLIGHT_EVIDENCE_NORMALIZED_SHA256
    )
    assert "KRAKEN_BLINDED_REPLAY_PREFLIGHT_PASS" in evidence
    assert "3e805044356777f0bdfa2901db267d714c1e14d11415dd4686acaaaed92f1042" in (
        evidence
    )
    assert "selected timestamps exposed: `false`" in evidence
    assert "real replay authorized: `false`" in evidence
    assert "T00:00:00Z" not in evidence


def test_preflight_reproduces_segments_and_seals_price_independent_schedule():
    locked = FakeLocked()
    preflight = KrakenBlindedReplayPreflight()

    first = preflight.review_locked(locked)
    second = preflight.review_locked(locked)

    assert first == second
    assert first["status"] == "KRAKEN_BLINDED_REPLAY_PREFLIGHT_PASS"
    assert first["dataset_manifest_sha256"] == DATASET_MANIFEST_SHA256
    assert first["selection_uses_ohlcv"] is False
    assert first["selected_timestamps_exposed"] is False
    assert first["selection_schedule_persisted"] is False
    assert len(first["selection_schedule_sha256"]) == 64
    assert first["assets"]["BTC-USD"]["continuous_segment_rows"] == [1916, 730]
    assert first["assets"]["ETH-USD"]["continuous_segment_rows"] == [2647]
    assert first["assets"]["XRP-USD"]["continuous_segment_rows"] == [1226, 1419]
    assert first["assets"]["BTC-USD"]["candidate_episode_count"] == 2470
    assert first["assets"]["ETH-USD"]["candidate_episode_count"] == 2559
    assert first["assets"]["XRP-USD"]["candidate_episode_count"] == 2469
    assert first["real_replay_review_eligible"] is True
    assert first["real_replay_authorized"] is False
    assert first["real_chart_replay_executed"] is False
    assert first["performance_evaluation_executed"] is False
    serialized = json.dumps(first, sort_keys=True).lower()
    assert "end_exclusive" not in serialized
    assert '"start"' not in serialized


@pytest.mark.parametrize(
    "mutator, error",
    [
        (lambda locked: setattr(locked, "manifest_sha256", "0" * 64), "manifest"),
        (
            lambda locked: locked.manifest.update(dataset_id="wrong"),
            "identity",
        ),
        (
            lambda locked: locked.manifest.update(source_mode="REST"),
            "source mode",
        ),
        (
            lambda locked: locked.manifest.update(network_requests_executed=True),
            "network",
        ),
        (
            lambda locked: locked.assets["BTC-USD"].pop(),
            "observed-row",
        ),
        (
            lambda locked: locked.manifest["assets"]["XRP-USD"].update(
                missing_timestamps=[]
            ),
            "gap evidence",
        ),
    ],
)
def test_preflight_fails_closed_for_locked_evidence_drift(mutator, error):
    locked = FakeLocked()
    mutator(locked)
    with pytest.raises(RuntimeError, match=error):
        KrakenBlindedReplayPreflight().review_locked(locked)


def test_price_values_cannot_change_selected_schedule():
    first = FakeLocked()
    changed = deepcopy(first)
    for rows in changed.assets.values():
        for row in rows:
            row[1:] = ["200", "202", "198", "201", "999"]

    first_result = KrakenBlindedReplayPreflight().review_locked(first)
    changed_result = KrakenBlindedReplayPreflight().review_locked(changed)

    assert first_result["selection_schedule_sha256"] == (
        changed_result["selection_schedule_sha256"]
    )


def test_review_cli_prints_only_nonexecuted_declaration(capsys):
    exit_code = main(
        [
            "--dataset-lock-evidence",
            str(LOCK_EVIDENCE),
            "--review-protocol",
            str(REVIEW_PROTOCOL),
            "--replay-component",
            str(REPLAY_COMPONENT),
            "--evidence-component",
            str(EVIDENCE_COMPONENT),
        ]
    )
    payload = json.loads(capsys.readouterr().out)

    assert exit_code == 0
    assert payload["status"].endswith("PREFLIGHT_REQUIRED")
    assert payload["preflight_executed"] is False
    assert payload["real_replay_authorized"] is False
    assert payload["performance_evaluation_executed"] is False
