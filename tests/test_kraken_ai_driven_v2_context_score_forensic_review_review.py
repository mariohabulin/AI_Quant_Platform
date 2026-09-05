import os
from pathlib import Path
import shutil
import sys

import pytest


sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src")))

from kraken_ai_driven_v2_context_score_forensic_review_review import (
    EXPECTED_HASHES,
    STATIC_STATUS,
    review_context_score_forensics,
)


ROOT = Path(__file__).resolve().parents[1]


def test_static_review_binds_result_runner_protocol_and_component():
    result = review_context_score_forensics(ROOT)
    assert result["status"] == STATIC_STATUS
    assert all(result["source_sha256_matches"].values())
    assert result["external_evidence_opened"] is False
    assert result["model_artifacts_unpickled"] is False
    assert result["model_training_executed"] is False
    assert result["automatic_experiment_2_selection"] is False
    assert result["calibration_data_opened"] is False
    assert result["evaluation_data_opened"] is False


def test_static_hash_registry_is_exact_lowercase_sha256():
    assert set(EXPECTED_HASHES) == {
        "attempt_1_result",
        "runner_protocol",
        "runner_component",
        "forensic_protocol",
        "forensic_component",
    }
    assert all(len(value) == 64 and value == value.lower() for value in EXPECTED_HASHES.values())


def test_static_review_rejects_tampered_result_document(tmp_path):
    copy = tmp_path / "copy"
    shutil.copytree(ROOT, copy)
    target = copy / "KRAKEN_AI_DRIVEN_V2_DERIVATIVES_CONTEXT_DEVELOPMENT_LEARNING_ATTEMPT_1_RESULT.md"
    target.write_text(target.read_text(encoding="utf-8") + "tamper\n", encoding="utf-8")
    with pytest.raises(RuntimeError, match="attempt_1_result"):
        review_context_score_forensics(copy)


def test_static_review_rejects_tampered_forensic_component(tmp_path):
    copy = tmp_path / "copy"
    shutil.copytree(ROOT, copy)
    target = copy / "src" / "kraken_ai_driven_v2_context_score_forensic_review.py"
    target.write_text(target.read_text(encoding="utf-8") + "tamper\n", encoding="utf-8")
    with pytest.raises(RuntimeError, match="forensic_component"):
        review_context_score_forensics(copy)
