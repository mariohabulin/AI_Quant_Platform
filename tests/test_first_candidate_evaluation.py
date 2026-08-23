import hashlib
import json
import os
from pathlib import Path
import sys
from types import SimpleNamespace

import numpy as np
import pandas as pd
import pytest

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src")))

import first_candidate_evaluation as evaluation_module
from first_candidate_evaluation import (
    CHECKSUM_FILENAME,
    EVALUATION_DIRECTORY_NAME,
    EXPECTED_MANIFEST_SHA256,
    REPORT_FILENAME,
    STAGING_DIRECTORY_NAME,
    FirstCandidateEvaluationRunner,
    RecordedFirstCandidateEvaluation,
    main,
)


class SerializableRecord:
    def __init__(self, payload):
        self.payload = payload

    def as_dict(self):
        return dict(self.payload)


class FakePreregistration:
    def __init__(self):
        self.calls = []
        self.locked = SimpleNamespace(
            strategy_engine=object(),
            candidate=SerializableRecord(
                {
                    "candidate_id": "ema-crossover-20-50-btc-eth-native-6h-v1",
                    "strategy_name": "ema_crossover",
                }
            ),
            configuration=SerializableRecord(
                {
                    "train_size": 2880,
                    "test_size": 720,
                    "random_seed": 20260822,
                }
            ),
            assets={"BTC-USD": object(), "ETH-USD": object()},
            manifest_sha256=EXPECTED_MANIFEST_SHA256,
        )

    def lock(self, manifest_path):
        self.calls.append(Path(manifest_path))
        return self.locked


def protocol_report(status="PAPER_CANDIDATE", live_authorized=False):
    return {
        "status": status,
        "gates": {"baseline_validated": True, "cost_stress_validated": True},
        "failed_gates": [],
        "baseline_evaluation": {"classification": {"status": "VALIDATED"}},
        "cost_stress_evaluation": {
            "classification": {"status": "VALIDATED"}
        },
        "live_execution_authorized": live_authorized,
    }


class RecordingProtocol:
    instances = []
    result = protocol_report()

    def __init__(self, strategy_engine, candidate, configuration):
        self.strategy_engine = strategy_engine
        self.candidate = candidate
        self.configuration = configuration
        self.calls = []
        type(self).instances.append(self)

    def run(self, assets):
        self.calls.append(assets)
        return dict(type(self).result)


@pytest.fixture(autouse=True)
def reset_recording_protocol():
    RecordingProtocol.instances = []
    RecordingProtocol.result = protocol_report()


def test_runner_records_one_canonical_report_and_checksum(tmp_path):
    preregistration = FakePreregistration()
    manifest_path = tmp_path / "manifest.json"
    manifest_path.write_text("{}\n", encoding="utf-8")
    runner = FirstCandidateEvaluationRunner(
        preregistration=preregistration,
        protocol_factory=RecordingProtocol,
    )

    recorded = runner.run(manifest_path)

    assert len(preregistration.calls) == 1
    assert len(RecordingProtocol.instances) == 1
    assert RecordingProtocol.instances[0].calls == [preregistration.locked.assets]
    assert recorded.outcome == "PAPER_CANDIDATE"
    assert recorded.report_path.name == REPORT_FILENAME
    assert recorded.checksum_path.name == CHECKSUM_FILENAME

    report_bytes = recorded.report_path.read_bytes()
    payload = json.loads(report_bytes)
    assert report_bytes.endswith(b"\n")
    assert payload["manifest_sha256"] == EXPECTED_MANIFEST_SHA256
    assert payload["protocol_report"]["status"] == "PAPER_CANDIDATE"
    assert payload["evaluation_executed"] is True
    assert payload["bounded_forward_paper_review_eligible"] is True
    assert payload["bounded_forward_paper_authorized"] is False
    assert payload["optimization_authorized"] is False
    assert payload["live_execution_authorized"] is False

    expected_hash = hashlib.sha256(report_bytes).hexdigest()
    assert recorded.report_sha256 == expected_hash
    assert recorded.checksum_path.read_bytes() == (
        f"{expected_hash}  {REPORT_FILENAME}\n".encode("ascii")
    )


def test_existing_evidence_refuses_repeat_before_dataset_lock(tmp_path):
    preregistration = FakePreregistration()
    (tmp_path / EVALUATION_DIRECTORY_NAME).mkdir()
    runner = FirstCandidateEvaluationRunner(
        preregistration=preregistration,
        protocol_factory=RecordingProtocol,
    )

    with pytest.raises(FileExistsError, match="already exists"):
        runner.run(tmp_path / "manifest.json")

    assert preregistration.calls == []
    assert RecordingProtocol.instances == []


def test_incomplete_staging_directory_refuses_automatic_retry(tmp_path):
    preregistration = FakePreregistration()
    (tmp_path / STAGING_DIRECTORY_NAME).mkdir()
    runner = FirstCandidateEvaluationRunner(
        preregistration=preregistration,
        protocol_factory=RecordingProtocol,
    )

    with pytest.raises(FileExistsError, match="incomplete"):
        runner.run(tmp_path / "manifest.json")

    assert preregistration.calls == []
    assert RecordingProtocol.instances == []


def test_runner_refuses_any_manifest_other_than_the_exact_frozen_hash(tmp_path):
    preregistration = FakePreregistration()
    preregistration.locked.manifest_sha256 = "c" * 64
    runner = FirstCandidateEvaluationRunner(
        preregistration=preregistration,
        protocol_factory=RecordingProtocol,
    )

    with pytest.raises(ValueError, match="exact frozen"):
        runner.run(tmp_path / "manifest.json")

    assert len(preregistration.calls) == 1
    assert RecordingProtocol.instances == []
    assert not (tmp_path / EVALUATION_DIRECTORY_NAME).exists()
    assert not (tmp_path / STAGING_DIRECTORY_NAME).exists()


def test_runner_fails_closed_on_unsafe_protocol_report(tmp_path):
    preregistration = FakePreregistration()
    RecordingProtocol.result = protocol_report(live_authorized=True)
    runner = FirstCandidateEvaluationRunner(
        preregistration=preregistration,
        protocol_factory=RecordingProtocol,
    )

    with pytest.raises(ValueError, match="deny live execution"):
        runner.run(tmp_path / "manifest.json")

    assert not (tmp_path / EVALUATION_DIRECTORY_NAME).exists()
    assert not (tmp_path / STAGING_DIRECTORY_NAME).exists()


def test_runner_rejects_non_finite_evidence_before_creating_output(tmp_path):
    preregistration = FakePreregistration()
    RecordingProtocol.result = protocol_report()
    RecordingProtocol.result["non_finite"] = float("nan")
    runner = FirstCandidateEvaluationRunner(
        preregistration=preregistration,
        protocol_factory=RecordingProtocol,
    )

    with pytest.raises(ValueError, match="Out of range float values"):
        runner.run(tmp_path / "manifest.json")

    assert not (tmp_path / EVALUATION_DIRECTORY_NAME).exists()
    assert not (tmp_path / STAGING_DIRECTORY_NAME).exists()


def test_runner_canonicalizes_timestamp_and_numpy_evidence(tmp_path):
    preregistration = FakePreregistration()
    timestamp = pd.Timestamp("2024-01-01T06:00:00Z")
    RecordingProtocol.result = protocol_report()
    RecordingProtocol.result["baseline_evaluation"] = {
        "assets": {
            "BTC-USD": {
                "out_of_sample": {
                    "in_sample": {
                        "benchmark": {
                            "entry_index": timestamp,
                            "trade_count": np.int64(3),
                            "excess_return": np.float32(1.25),
                            "valid": np.bool_(True),
                        }
                    }
                }
            }
        }
    }
    runner = FirstCandidateEvaluationRunner(
        preregistration=preregistration,
        protocol_factory=RecordingProtocol,
    )

    recorded = runner.run(tmp_path / "manifest.json")
    payload = json.loads(recorded.report_path.read_bytes())
    benchmark = payload["protocol_report"]["baseline_evaluation"]["assets"][
        "BTC-USD"
    ]["out_of_sample"]["in_sample"]["benchmark"]

    assert benchmark == {
        "entry_index": "2024-01-01T06:00:00+00:00",
        "excess_return": 1.25,
        "trade_count": 3,
        "valid": True,
    }


def test_runner_rejects_missing_timestamp_before_creating_output(tmp_path):
    preregistration = FakePreregistration()
    RecordingProtocol.result = protocol_report()
    RecordingProtocol.result["baseline_evaluation"]["entry_index"] = pd.NaT
    runner = FirstCandidateEvaluationRunner(
        preregistration=preregistration,
        protocol_factory=RecordingProtocol,
    )

    with pytest.raises(ValueError, match="Timestamp evidence must not be missing"):
        runner.run(tmp_path / "manifest.json")

    assert not (tmp_path / EVALUATION_DIRECTORY_NAME).exists()
    assert not (tmp_path / STAGING_DIRECTORY_NAME).exists()


def test_cli_prints_only_persisted_summary(monkeypatch, tmp_path, capsys):
    report_path = tmp_path / EVALUATION_DIRECTORY_NAME / REPORT_FILENAME
    checksum_path = tmp_path / EVALUATION_DIRECTORY_NAME / CHECKSUM_FILENAME

    class FakeRunner:
        def run(self, manifest_path):
            assert Path(manifest_path) == tmp_path / "manifest.json"
            return RecordedFirstCandidateEvaluation(
                report_path=report_path,
                checksum_path=checksum_path,
                report_sha256="b" * 64,
                outcome="RESEARCH_HOLD",
            )

    monkeypatch.setattr(evaluation_module, "FirstCandidateEvaluationRunner", FakeRunner)

    assert main(["--manifest", str(tmp_path / "manifest.json")]) == 0
    output = json.loads(capsys.readouterr().out)

    assert output["status"] == "EVALUATION_RECORDED"
    assert output["outcome"] == "RESEARCH_HOLD"
    assert output["report_sha256"] == "b" * 64
    assert output["evaluation_executed"] is True
    assert output["optimization_authorized"] is False
    assert output["bounded_forward_paper_authorized"] is False
    assert output["live_execution_authorized"] is False
