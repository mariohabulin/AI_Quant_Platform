import os
from pathlib import Path
import shutil
import sys

import pytest


sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src")))

from kraken_weekly_persistent_up_momentum_development_runner_design_review import (
    BOUND_PATHS,
    EXPECTED_HASHES,
    STATUS,
    _design_static_safety,
    review_weekly_development_runner_design,
)


ROOT = Path(__file__).resolve().parents[1]


def _copy_bound_files(destination):
    for relative in BOUND_PATHS.values():
        source = ROOT / relative
        target = destination / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, target)


def test_review_binds_every_source_and_keeps_execution_closed():
    result = review_weekly_development_runner_design(ROOT)

    assert result["status"] == STATUS
    assert result["source_sha256_matches"] == {
        name: True for name in EXPECTED_HASHES
    }
    assert result["runner_design_frozen"] is True
    assert result["filesystem_reader_implemented"] is False
    assert result["network_reader_implemented"] is False
    assert result["source_values_opened"] is False
    assert result["kraken_archive_opened"] is False
    assert result["real_weekly_aggregation_executed"] is False
    assert result["real_outcomes_generated"] is False
    assert result["development_run_executed"] is False
    assert result["model_training_executed"] is False
    assert result["real_orders_submitted"] is False
    assert result["real_market_values_opened_by_review"] is False
    assert result["synthetic_fixture_executed_by_review"] is False


def test_review_proves_design_component_is_declarative_only():
    result = review_weekly_development_runner_design(ROOT)

    assert result["design_static_safety"] == {
        "allowed_declarative_imports_only": True,
        "filesystem_calls_absent": True,
        "network_calls_absent": True,
        "parsed_python_ast": True,
    }


@pytest.mark.parametrize("tampered_name", tuple(BOUND_PATHS))
def test_review_rejects_every_bound_source_tamper(tmp_path, tampered_name):
    _copy_bound_files(tmp_path)
    target = tmp_path / BOUND_PATHS[tampered_name]
    target.write_bytes(target.read_bytes() + b"tamper\n")

    with pytest.raises(RuntimeError, match=tampered_name):
        review_weekly_development_runner_design(tmp_path)


def test_bound_sources_are_checkout_stable_from_lf_or_crlf(tmp_path):
    _copy_bound_files(tmp_path)
    for relative in BOUND_PATHS.values():
        target = tmp_path / relative
        source_bytes = target.read_bytes()
        canonical_lf = source_bytes.replace(b"\r\n", b"\n").replace(
            b"\r", b"\n"
        )
        target.write_bytes(canonical_lf.replace(b"\n", b"\r\n"))

    result = review_weekly_development_runner_design(tmp_path)

    assert result["status"] == STATUS
    assert all(result["source_sha256_matches"].values())


def test_static_safety_rejects_filesystem_import(tmp_path):
    component = tmp_path / "bad_import.py"
    component.write_bytes(b"import os\n")

    with pytest.raises(RuntimeError, match="unauthorized modules"):
        _design_static_safety(component)


def test_static_safety_rejects_data_call(tmp_path):
    component = tmp_path / "bad_call.py"
    component.write_bytes(b"def bad():\n    return open('market.csv')\n")

    with pytest.raises(RuntimeError, match="forbidden data calls"):
        _design_static_safety(component)
