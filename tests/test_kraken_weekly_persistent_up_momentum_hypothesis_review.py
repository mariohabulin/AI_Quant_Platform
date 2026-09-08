import os
from pathlib import Path
import shutil
import sys

import pytest


sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src")))

from kraken_weekly_persistent_up_momentum_hypothesis_review import (
    BOUND_PATHS,
    EXPECTED_HASHES,
    STATUS,
    review_weekly_persistent_up_momentum_hypothesis,
)


ROOT = Path(__file__).resolve().parents[1]


def _copy_bound_files(destination):
    for relative in BOUND_PATHS.values():
        source = ROOT / relative
        target = destination / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, target)


def test_static_review_binds_all_sources_and_keeps_execution_closed():
    result = review_weekly_persistent_up_momentum_hypothesis(ROOT)

    assert result["status"] == STATUS
    assert result["source_sha256_matches"] == {name: True for name in EXPECTED_HASHES}
    assert result["prior_daily_rule_rounds_closed"] is True
    assert result["terminal_12h_research_remains_closed"] is True
    assert result["real_market_values_opened_by_review"] is False
    assert result["source_values_opened"] is False
    assert result["development_run_executed"] is False
    assert result["model_training_executed"] is False
    assert result["real_orders_submitted"] is False


def test_static_review_confirms_declarative_component_only():
    safety = review_weekly_persistent_up_momentum_hypothesis(ROOT)[
        "component_static_safety"
    ]

    assert safety == {
        "allowed_imports_only": True,
        "forbidden_data_calls_absent": True,
        "parsed_python_ast": True,
    }


@pytest.mark.parametrize("tampered_name", tuple(BOUND_PATHS))
def test_static_review_rejects_any_bound_source_tamper(tmp_path, tampered_name):
    _copy_bound_files(tmp_path)
    target = tmp_path / BOUND_PATHS[tampered_name]
    target.write_bytes(target.read_bytes() + b"tamper\n")

    with pytest.raises(RuntimeError, match=tampered_name):
        review_weekly_persistent_up_momentum_hypothesis(tmp_path)


def test_bound_sources_are_checkout_stable_across_crlf(tmp_path):
    _copy_bound_files(tmp_path)
    for relative in BOUND_PATHS.values():
        target = tmp_path / relative
        target.write_bytes(target.read_bytes().replace(b"\n", b"\r\n"))

    result = review_weekly_persistent_up_momentum_hypothesis(tmp_path)

    assert result["status"] == STATUS
    assert all(result["source_sha256_matches"].values())
