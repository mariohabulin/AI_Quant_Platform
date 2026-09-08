import os
from pathlib import Path
import shutil
import sys

import pytest


sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src")))

from kraken_weekly_persistent_up_momentum_synthetic_review import (
    BOUND_PATHS,
    EXPECTED_HASHES,
    STATUS,
    review_weekly_persistent_up_momentum_synthetic,
)


ROOT = Path(__file__).resolve().parents[1]


def _copy_bound_files(destination):
    for relative in BOUND_PATHS.values():
        source = ROOT / relative
        target = destination / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, target)


def test_review_binds_every_source_and_keeps_real_execution_closed():
    result = review_weekly_persistent_up_momentum_synthetic(ROOT)

    assert result["status"] == STATUS
    assert result["source_sha256_matches"] == {
        name: True for name in EXPECTED_HASHES
    }
    assert result["synthetic_engine_implemented"] is True
    assert result["synthetic_fixture_executed_by_review"] is False
    assert result["real_market_values_opened_by_review"] is False
    assert result["source_values_opened"] is False
    assert result["real_weekly_aggregation_executed"] is False
    assert result["real_outcomes_generated"] is False
    assert result["development_run_executed"] is False
    assert result["model_training_executed"] is False
    assert result["real_orders_submitted"] is False


def test_review_proves_engine_has_no_reader_or_network_surface():
    result = review_weekly_persistent_up_momentum_synthetic(ROOT)

    assert result["engine_static_safety"] == {
        "allowed_imports_only": True,
        "filesystem_calls_absent": True,
        "network_calls_absent": True,
        "parsed_python_ast": True,
    }
    assert result["filesystem_reader_implemented"] is False
    assert result["network_reader_implemented"] is False


@pytest.mark.parametrize("tampered_name", tuple(BOUND_PATHS))
def test_review_rejects_every_bound_source_tamper(tmp_path, tampered_name):
    _copy_bound_files(tmp_path)
    target = tmp_path / BOUND_PATHS[tampered_name]
    target.write_bytes(target.read_bytes() + b"tamper\n")

    with pytest.raises(RuntimeError, match=tampered_name):
        review_weekly_persistent_up_momentum_synthetic(tmp_path)


def test_bound_sources_are_stable_from_lf_or_crlf_checkout(tmp_path):
    _copy_bound_files(tmp_path)
    for relative in BOUND_PATHS.values():
        target = tmp_path / relative
        source_bytes = target.read_bytes()
        canonical_lf = source_bytes.replace(b"\r\n", b"\n").replace(
            b"\r", b"\n"
        )
        target.write_bytes(canonical_lf.replace(b"\n", b"\r\n"))

    result = review_weekly_persistent_up_momentum_synthetic(tmp_path)

    assert result["status"] == STATUS
    assert all(result["source_sha256_matches"].values())
