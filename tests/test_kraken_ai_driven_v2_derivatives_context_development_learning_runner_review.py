import hashlib
import os
from pathlib import Path
import shutil
import sys

import pytest


sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src")))

from kraken_ai_driven_v2_derivatives_context_development_learning_runner_review import (
    EXPECTED_HASHES,
    STATUS,
    review_context_development_learning_runner,
)


ROOT = Path(__file__).resolve().parents[1]


def test_static_review_binds_all_parent_and_runner_sources():
    result = review_context_development_learning_runner(ROOT)

    assert result["status"] == STATUS
    assert result["runner_protocol_sha256_match"] is True
    assert result["runner_component_sha256_match"] is True
    assert result["dataset_lock_independent_review_passed"] is True
    assert all(result["parent_source_bindings"].values())
    assert result["maximum_fold_model_fits"] == 12
    assert result["model_training_executed"] is False
    assert result["calibration_data_opened"] is False
    assert result["evaluation_data_opened"] is False


def test_expected_hashes_are_real_lowercase_sha256_values():
    assert set(EXPECTED_HASHES) == {
        "hypothesis_protocol",
        "hypothesis_component",
        "hypothesis_review",
        "dataset_protocol",
        "dataset_component",
        "dataset_review",
        "dataset_result",
        "windows_sidecar_incident",
        "runner_protocol",
        "runner_component",
    }
    assert all(len(value) == 64 and value == value.lower() for value in EXPECTED_HASHES.values())


def test_static_review_rejects_tampered_runner_protocol(tmp_path):
    copy = tmp_path / "copy"
    shutil.copytree(ROOT, copy)
    target = copy / "KRAKEN_BTC_ETH_XRP_AI_DRIVEN_V2_DERIVATIVES_CONTEXT_DEVELOPMENT_LEARNING_RUNNER_PROTOCOL_V1.md"
    target.write_text(target.read_text(encoding="utf-8") + "tamper\n", encoding="utf-8")
    with pytest.raises(RuntimeError, match="runner_protocol"):
        review_context_development_learning_runner(copy)


def test_dataset_result_document_is_bound_to_exact_pass():
    path = ROOT / "KRAKEN_AI_DRIVEN_V2_DERIVATIVES_CONTEXT_DATASET_LOCK_ATTEMPT_4_RESULT.md"
    assert hashlib.sha256(path.read_bytes()).hexdigest() == EXPECTED_HASHES["dataset_result"]
    text = path.read_text(encoding="utf-8")
    assert "KRAKEN_AI_V2_DERIVATIVES_CONTEXT_DATASET_LOCK_READER_PASS" in text
    assert "db4dde045d9fce22bee1389fe8c7ad13d3e3ccc5e5c4ace7c433f5461ba11916" in text
    assert "Acquisition is closed" in text or "acquisition is closed" in text
