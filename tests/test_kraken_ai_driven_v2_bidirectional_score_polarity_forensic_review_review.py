import os
from pathlib import Path
import shutil
import sys

import pytest


sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src")))

from kraken_ai_driven_v2_bidirectional_score_polarity_forensic_review_review import (
    EXPECTED_HASHES,
    STATIC_STATUS,
    review_bidirectional_score_polarity_forensics,
)


ROOT = Path(__file__).resolve().parents[1]


def test_static_review_binds_result_runner_review_protocol_and_component():
    result = review_bidirectional_score_polarity_forensics(ROOT)
    assert result["status"] == STATIC_STATUS
    assert all(result["source_sha256_matches"].values())
    assert result["external_evidence_opened"] is False
    assert result["model_artifacts_unpickled"] is False
    assert result["model_training_executed"] is False
    assert result["retrospective_threshold_search_authorized"] is False
    assert result["polarity_flip_authorized"] is False
    assert result["automatic_next_experiment_selection"] is False
    assert result["calibration_data_opened"] is False
    assert result["evaluation_data_opened"] is False


def test_static_hash_registry_is_exact_lowercase_sha256():
    assert set(EXPECTED_HASHES) == {
        "attempt_1_result",
        "runner_protocol",
        "runner_component",
        "runner_review",
        "forensic_protocol",
        "forensic_component",
    }
    assert all(
        len(value) == 64 and value == value.lower()
        for value in EXPECTED_HASHES.values()
    )


def test_static_review_rejects_tampered_result_document(tmp_path):
    copy = tmp_path / "copy"
    shutil.copytree(ROOT, copy)
    target = copy / "KRAKEN_AI_DRIVEN_V2_BIDIRECTIONAL_DEVELOPMENT_LEARNING_ATTEMPT_1_RESULT.md"
    target.write_text(target.read_text(encoding="utf-8") + "tamper\n", encoding="utf-8")
    with pytest.raises(RuntimeError, match="attempt_1_result"):
        review_bidirectional_score_polarity_forensics(copy)


def test_static_review_rejects_tampered_forensic_component(tmp_path):
    copy = tmp_path / "copy"
    shutil.copytree(ROOT, copy)
    target = (
        copy
        / "src"
        / "kraken_ai_driven_v2_bidirectional_score_polarity_forensic_review.py"
    )
    target.write_text(target.read_text(encoding="utf-8") + "tamper\n", encoding="utf-8")
    with pytest.raises(RuntimeError, match="forensic_component"):
        review_bidirectional_score_polarity_forensics(copy)


def test_attempt_1_result_closes_bidirectional_hypothesis_without_rescue():
    result_record = (
        ROOT
        / "KRAKEN_AI_DRIVEN_V2_BIDIRECTIONAL_SCORE_POLARITY_FORENSIC_REVIEW_ATTEMPT_1_RESULT.md"
    ).read_text(encoding="utf-8")

    for marker in (
        "8f51ab4f52725ab7529009a0f9fcc934a3159f69",
        "7176ca3a005b7bdbfbdcbc2259fafd11c154ee45b0517eab26894e675aa26b3f",
        "KRAKEN_AI_V2_BIDIRECTIONAL_SCORE_POLARITY_FORENSIC_REVIEW_PASS",
        "KRAKEN_AI_V2_BIDIRECTIONAL_NO_VIABLE_HYPOTHESIS_HOLD_CASH",
        "680 of 765 positive context SHORT scores",
        "602 of 674 positive control SHORT",
        "There is no threshold reinterpretation",
        "It is not authorized by this result",
        "explicit research stop condition",
    ):
        assert marker in result_record
