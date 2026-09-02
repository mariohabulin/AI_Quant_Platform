import os
from pathlib import Path
import sys

import pytest


sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src")))

from kraken_ai_driven_v2_derivatives_context_feasibility_review import (
    EXPECTED_COMPONENT_SHA256,
    EXPECTED_PROTOCOL_SHA256,
    STATUS,
    review_derivatives_context_feasibility,
)


ROOT = Path(__file__).resolve().parents[1]


def test_review_binds_closed_parent_and_new_metadata_component():
    review = review_derivatives_context_feasibility(ROOT)

    assert review["status"] == STATUS
    assert review["parent_commit"] == "cdb1ccc"
    assert review["parent_result_sha256"] == (
        "d76bb013c2124672132868752a5bb350a782eb45ef7f062b78b5edcb6d3b3703"
    )
    assert review["protocol_sha256"] == EXPECTED_PROTOCOL_SHA256
    assert review["component_sha256"] == EXPECTED_COMPONENT_SHA256
    assert review["parent_protocol_sha256_match"] is True
    assert review["parent_component_sha256_match"] is True
    assert review["parent_result_document_sha256_match"] is True
    assert review["protocol_sha256_match"] is True
    assert review["component_sha256_match"] is True


def test_review_keeps_all_learning_and_execution_boundaries_closed():
    review = review_derivatives_context_feasibility(ROOT)

    assert review["public_object_metadata_only"] is True
    assert review["market_values_opened"] is False
    assert review["ohlcvt_values_opened"] is False
    assert review["labels_generated"] is False
    assert review["model_training_executed"] is False
    assert review["automatic_model_selection"] is False
    assert review["calibration_data_opened"] is False
    assert review["evaluation_data_opened"] is False
    assert review["candidate_v2_authorized"] is False
    assert review["bounded_forward_paper_authorized"] is False
    assert review["real_orders_submitted"] is False
    assert review["live_execution_authorized"] is False


def test_review_fails_closed_if_new_component_changes(tmp_path):
    relatives = (
        "KRAKEN_BTC_ETH_XRP_AI_DRIVEN_V2_ALPHA_RESEARCH_LAB_PROTOCOL_V1.md",
        "KRAKEN_AI_DRIVEN_V2_ALPHA_RESEARCH_LAB_ATTEMPT_1_RESULT.md",
        "KRAKEN_BTC_ETH_XRP_AI_DRIVEN_V2_DERIVATIVES_CONTEXT_FEASIBILITY_PROTOCOL_V1.md",
        "src/kraken_ai_driven_v2_alpha_research_lab.py",
        "src/kraken_ai_driven_v2_derivatives_context_feasibility.py",
    )
    for relative in relatives:
        source = ROOT / relative
        target = tmp_path / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(source.read_bytes())
    component = tmp_path / "src" / "kraken_ai_driven_v2_derivatives_context_feasibility.py"
    component.write_text(component.read_text(encoding="utf-8") + "\n# tamper\n", encoding="utf-8")

    with pytest.raises(RuntimeError, match="component"):
        review_derivatives_context_feasibility(tmp_path)
