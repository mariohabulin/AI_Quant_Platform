import hashlib
import json
import os
import sys
from pathlib import Path

import pandas as pd
import pytest

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src")))

from blinded_daily_replay import BlindedReplayView
from kraken_blinded_replay_review import (
    DATASET_ID,
    DATASET_MANIFEST_SHA256,
    EXPECTED_MISSING_TIMESTAMPS,
    EXPECTED_OBSERVED_ROWS,
)
from kraken_blinded_replay_runner import (
    CATALOG_CHECKSUM_FILENAME,
    CATALOG_DIRECTORY_NAME,
    CATALOG_FILENAME,
    CONTEXT_BARS,
    DECISION_BARS,
    EPISODE_SPECS,
    EXECUTION_PROTOCOL_NORMALIZED_SHA256,
    OPERATOR_AUTHORIZATION_PHRASE,
    PREFLIGHT_EVIDENCE_NORMALIZED_SHA256,
    SELECTION_SCHEDULE_SHA256,
    KrakenBlindedReplayCatalogLock,
    KrakenSupervisedBlindedReplayRunner,
    MatplotlibReplayRenderer,
    execution_declaration,
    load_execution_protocol,
    load_preflight_evidence,
    main,
)
from kraken_daily_dataset import ASSET_ORDER
from research_evidence import canonical_json_bytes

ROOT = Path(__file__).resolve().parents[1]
PREFLIGHT_EVIDENCE = ROOT / "KRAKEN_BTC_ETH_XRP_BLINDED_REPLAY_PREFLIGHT_EVIDENCE_V1.md"
EXECUTION_PROTOCOL = (
    ROOT / "KRAKEN_BTC_ETH_XRP_SUPERVISED_BLINDED_REPLAY_PROTOCOL_V1.md"
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
            asset: canonical_rows(asset) for asset in ("BTC-USD", "ETH-USD", "XRP-USD")
        }
        self.manifest = {
            "dataset_id": DATASET_ID,
            "source_mode": "OFFICIAL_OHLCVT_ARCHIVES_ONLY",
            "network_requests_executed": False,
            "assets": {
                asset: {"missing_timestamps": list(EXPECTED_MISSING_TIMESTAMPS[asset])}
                for asset in self.assets
            },
        }


class FakeDatasetLock:
    calls = 0

    def lock(self, _path):
        type(self).calls += 1
        return FakeLocked()


def all_skip_input():
    answers = iter(
        value
        for _ in range(DECISION_BARS)
        for value in ("SKIP", "No reviewed entry condition.")
    )
    return lambda _prompt: next(answers)


def run_episode(root, renderer=None, input_fn=None, output_fn=None):
    return KrakenSupervisedBlindedReplayRunner(
        dataset_lock_factory=FakeDatasetLock
    ).run_next(
        Path(root).parent / "synthetic-lock",
        root,
        authorization=OPERATOR_AUTHORIZATION_PHRASE,
        renderer=renderer if renderer is not None else (lambda _view: None),
        input_fn=input_fn if input_fn is not None else all_skip_input(),
        output_fn=output_fn if output_fn is not None else (lambda _message: None),
    )


def test_execution_contracts_are_exact_hash_bound():
    _, preflight_digest = load_preflight_evidence(PREFLIGHT_EVIDENCE)
    _, execution_digest = load_execution_protocol(EXECUTION_PROTOCOL)

    assert preflight_digest == PREFLIGHT_EVIDENCE_NORMALIZED_SHA256
    assert execution_digest == EXECUTION_PROTOCOL_NORMALIZED_SHA256


@pytest.mark.parametrize(
    "source,loader,error",
    [
        (
            PREFLIGHT_EVIDENCE,
            load_preflight_evidence,
            "Sealed-preflight evidence SHA256",
        ),
        (
            EXECUTION_PROTOCOL,
            load_execution_protocol,
            "Supervised-replay protocol SHA256",
        ),
    ],
)
def test_changed_execution_contract_is_rejected(tmp_path, source, loader, error):
    changed = tmp_path / source.name
    changed.write_text(
        source.read_text(encoding="utf-8") + "changed\n",
        encoding="utf-8",
    )
    with pytest.raises(RuntimeError, match=error):
        loader(changed)


def test_review_declaration_opens_no_dataset_and_authorizes_nothing():
    declaration = execution_declaration()

    assert declaration["status"].endswith("OPERATOR_AUTHORIZATION_REQUIRED")
    assert declaration["selection_schedule_sha256"] == SELECTION_SCHEDULE_SHA256
    assert declaration["asset_order"] == ["BTC-USD", "ETH-USD", "XRP-USD"]
    assert declaration["episode_count"] == 3
    assert declaration["episodes_per_invocation"] == 1
    assert declaration["context_bars"] == CONTEXT_BARS == 30
    assert declaration["decision_bars_per_episode"] == DECISION_BARS == 60
    assert declaration["sealed_preflight_completed"] is True
    assert declaration["supervised_replay_review_eligible"] is True
    assert declaration["operator_authorization_supplied"] is False
    assert declaration["dataset_opened"] is False
    assert declaration["participant_view_created"] is False
    assert declaration["real_replay_authorized"] is False
    assert declaration["real_chart_replay_executed"] is False
    assert declaration["performance_evaluation_executed"] is False
    assert declaration["candidate_v2_authorized"] is False
    assert declaration["live_execution_authorized"] is False


def test_exact_authorization_is_required_before_output_or_dataset_access(tmp_path):
    FakeDatasetLock.calls = 0
    root = tmp_path / "evidence"

    with pytest.raises(PermissionError, match="authorization"):
        KrakenSupervisedBlindedReplayRunner(
            dataset_lock_factory=FakeDatasetLock
        ).run_next(
            tmp_path / "synthetic-lock",
            root,
            authorization="YES",
            renderer=lambda _view: None,
            input_fn=all_skip_input(),
            output_fn=lambda _message: None,
        )

    assert FakeDatasetLock.calls == 0
    assert not root.exists()


@pytest.mark.parametrize(
    "dataset,evidence",
    [
        (ROOT / "locked-data", Path("external-evidence")),
        (Path("external-data"), ROOT / "replay-evidence"),
    ],
)
def test_dataset_and_evidence_must_remain_outside_repository(
    tmp_path, dataset, evidence
):
    dataset = dataset if dataset.is_absolute() else tmp_path / dataset
    evidence = evidence if evidence.is_absolute() else tmp_path / evidence
    with pytest.raises(ValueError, match="outside the repository"):
        KrakenSupervisedBlindedReplayRunner(
            dataset_lock_factory=FakeDatasetLock
        ).run_next(
            dataset,
            evidence,
            authorization=OPERATOR_AUTHORIZATION_PHRASE,
            renderer=lambda _view: None,
            input_fn=all_skip_input(),
            output_fn=lambda _message: None,
        )


def test_one_invocation_runs_only_btc_and_persists_before_each_advance(tmp_path):
    views = []
    result = run_episode(tmp_path / "evidence", renderer=views.append)

    assert result["status"].endswith("EPISODE_COMPLETED")
    assert result["asset"] == "BTC-USD"
    assert result["episode_ordinal"] == 1
    assert result["decision_count"] == DECISION_BARS
    assert result["catalog_completed"] is False
    assert result["operator_authorization_consumed"] is True
    assert result["additional_replay_authorized"] is False
    assert result["real_chart_replay_executed"] is True
    assert result["performance_evaluation_executed"] is False
    assert len(views) == DECISION_BARS
    assert [view.sequence for view in views] == list(range(DECISION_BARS))
    assert all(len(view.bars) == CONTEXT_BARS for view in views)
    assert all(view.bars.index[-1] == view.timestamp for view in views)
    assert (tmp_path / "evidence" / EPISODE_SPECS[0].directory_name).exists()
    assert not (tmp_path / "evidence" / EPISODE_SPECS[1].directory_name).exists()


def test_invalid_action_is_reprompted_without_consuming_a_decision(tmp_path):
    values = ["INVALID", "SKIP", "Causal reason."]
    values.extend(
        value for _ in range(DECISION_BARS - 1) for value in ("SKIP", "Causal reason.")
    )
    answers = iter(values)
    output = []

    result = run_episode(
        tmp_path / "evidence",
        input_fn=lambda _prompt: next(answers),
        output_fn=output.append,
    )

    assert result["decision_count"] == DECISION_BARS
    assert any("Invalid action" in message for message in output)


def test_chart_renderer_uses_only_in_memory_visible_bars(tmp_path, monkeypatch):
    import matplotlib

    matplotlib.use("Agg", force=True)
    index = pd.date_range("2025-01-01T00:00:00Z", periods=30, freq="D", tz="UTC")
    close = pd.Series(range(100, 130), index=index, dtype=float)
    bars = pd.DataFrame(
        {
            "Open": close - 0.5,
            "High": close + 1.0,
            "Low": close - 1.0,
            "Close": close,
            "Volume": 1000.0,
        },
        index=index,
    )
    view = BlindedReplayView("BTC-USD", 0, index[-1], "FLAT", bars)
    monkeypatch.chdir(tmp_path)
    renderer = MatplotlibReplayRenderer()

    renderer(view)

    assert len(renderer._price_axis.patches) == 30
    assert len(renderer._volume_axis.patches) == 30
    assert list(tmp_path.iterdir()) == []
    renderer.close()


def test_renderer_failure_leaves_incomplete_evidence_and_blocks_retry(tmp_path):
    root = tmp_path / "evidence"

    def fail(_view):
        raise RuntimeError("chart unavailable")

    with pytest.raises(RuntimeError, match="chart unavailable"):
        run_episode(root, renderer=fail)

    staging = root / f".{EPISODE_SPECS[0].directory_name}.staging"
    assert staging.exists()
    with pytest.raises(FileExistsError, match="Incomplete replay evidence"):
        run_episode(root)


def test_three_separate_authorizations_enforce_asset_order_and_lock_catalog(tmp_path):
    root = tmp_path / "evidence"
    first = run_episode(root)
    second = run_episode(root)
    third = run_episode(root)

    assert [first["asset"], second["asset"], third["asset"]] == list(ASSET_ORDER)
    assert first["catalog_completed"] is False
    assert second["catalog_completed"] is False
    assert third["catalog_completed"] is True
    assert len(third["catalog_sha256"]) == 64

    locked = KrakenBlindedReplayCatalogLock().lock(root)
    assert locked.catalog_sha256 == third["catalog_sha256"]
    assert len(locked.episodes) == 3
    assert locked.manifest["decision_count"] == 180
    assert locked.manifest["real_chart_replay_executed"] is True
    assert locked.manifest["supervised_reconstruction_completed"] is True
    assert locked.manifest["source_ohlcv_persisted"] is False
    assert locked.manifest["chart_images_persisted"] is False
    assert locked.manifest["performance_evaluation_executed"] is False
    assert locked.manifest["strategy_selection_executed"] is False
    assert locked.manifest["candidate_v2_authorized"] is False
    assert locked.manifest["live_execution_authorized"] is False


def test_completed_catalog_blocks_additional_replay(tmp_path):
    root = tmp_path / "evidence"
    for _ in EPISODE_SPECS:
        run_episode(root)

    result = run_episode(root)

    assert result["status"].endswith("ALREADY_COMPLETED")
    assert result["episode_count"] == 3
    assert result["additional_replay_authorized"] is False


def test_catalog_lock_rejects_resigned_performance_flag(tmp_path):
    root = tmp_path / "evidence"
    for _ in EPISODE_SPECS:
        run_episode(root)
    catalog_directory = root / CATALOG_DIRECTORY_NAME
    catalog_path = catalog_directory / CATALOG_FILENAME
    payload = json.loads(catalog_path.read_bytes())
    payload["performance_evaluation_executed"] = True
    raw = canonical_json_bytes(payload)
    digest = hashlib.sha256(raw).hexdigest()
    catalog_path.write_bytes(raw)
    (catalog_directory / CATALOG_CHECKSUM_FILENAME).write_bytes(
        f"{digest}  {CATALOG_FILENAME}\n".encode("ascii")
    )

    with pytest.raises(ValueError, match="safety flag"):
        KrakenBlindedReplayCatalogLock().lock(root)


def test_project_documents_keep_real_replay_as_explicit_next_authorization():
    roadmap = (ROOT / "ROADMAP.md").read_text(encoding="utf-8")
    mission = (ROOT / "CURRENT_MISSION.md").read_text(encoding="utf-8")
    architecture = (ROOT / "ARCHITECTURE.md").read_text(encoding="utf-8")
    vision = (ROOT / "VISION.md").read_text(encoding="utf-8")
    log = (ROOT / "LOG.md").read_text(encoding="utf-8")

    assert "one-episode-at-a-time" in roadmap
    assert "SUPERVISED REPLAY PREPARATION" in mission
    assert "Supervised Blinded Replay Execution Boundary v1" in architecture
    assert "one asset episode at a time" in vision
    assert "Supervised Blinded Replay v1" in log
    for text in (roadmap, mission, architecture, log):
        assert "Candidate v2" in text
        assert "live" in text.lower()


def test_review_cli_prints_nonexecuted_declaration(capsys):
    exit_code = main([])
    payload = json.loads(capsys.readouterr().out)

    assert exit_code == 0
    assert payload["status"].endswith("OPERATOR_AUTHORIZATION_REQUIRED")
    assert payload["dataset_opened"] is False
    assert payload["participant_view_created"] is False
    assert payload["real_replay_authorized"] is False
    assert payload["performance_evaluation_executed"] is False
