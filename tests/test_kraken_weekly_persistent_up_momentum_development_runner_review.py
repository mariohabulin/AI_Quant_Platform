import os
from pathlib import Path
import shutil
import sys

import pytest


sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src")))

from kraken_weekly_persistent_up_momentum_development_runner_review import (
    BOUND_PATHS,
    EXPECTED_HASHES,
    STATUS,
    _runner_static_safety,
    review_weekly_development_runner,
)


ROOT = Path(__file__).resolve().parents[1]


def _copy_bound_files(destination):
    for relative in BOUND_PATHS.values():
        source = ROOT / relative
        target = destination / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, target)


def test_review_binds_every_source_and_keeps_execution_closed():
    result = review_weekly_development_runner(ROOT)

    assert result["status"] == STATUS
    assert result["source_sha256_matches"] == {
        name: True for name in EXPECTED_HASHES
    }
    assert result["filesystem_reader_implemented"] is True
    assert result["trusted_real_adapter_implemented"] is True
    assert result["independent_evidence_reader_implemented"] is True
    assert result["authorization_phrase_active"] is False
    assert result["source_values_opened"] is False
    assert result["kraken_archive_opened"] is False
    assert result["real_weekly_aggregation_executed"] is False
    assert result["real_outcomes_generated"] is False
    assert result["development_run_executed"] is False
    assert result["model_training_executed"] is False
    assert result["real_orders_submitted"] is False
    assert result["source_values_opened_by_review"] is False
    assert result["kraken_archive_opened_by_review"] is False
    assert result["synthetic_fixture_executed_by_review"] is False
    assert result["development_run_executed_by_review"] is False


def test_review_proves_runner_static_safety():
    result = review_weekly_development_runner(ROOT)

    assert result["runner_static_safety"] == {
        "allowed_imports_only": True,
        "network_imports_absent": True,
        "model_imports_absent": True,
        "model_fit_calls_absent": True,
        "authorization_check_is_first_statement": True,
        "parsed_python_ast": True,
    }


@pytest.mark.parametrize("tampered_name", tuple(BOUND_PATHS))
def test_review_rejects_every_bound_source_tamper(tmp_path, tampered_name):
    _copy_bound_files(tmp_path)
    target = tmp_path / BOUND_PATHS[tampered_name]
    target.write_bytes(target.read_bytes() + b"tamper\n")

    with pytest.raises(RuntimeError, match=tampered_name):
        review_weekly_development_runner(tmp_path)


def test_bound_sources_are_checkout_stable_from_lf_or_crlf(tmp_path):
    _copy_bound_files(tmp_path)
    for relative in BOUND_PATHS.values():
        target = tmp_path / relative
        canonical_lf = target.read_bytes().replace(b"\r\n", b"\n").replace(
            b"\r", b"\n"
        )
        target.write_bytes(canonical_lf.replace(b"\n", b"\r\n"))

    result = review_weekly_development_runner(tmp_path)

    assert result["status"] == STATUS
    assert all(result["source_sha256_matches"].values())


def test_static_safety_rejects_network_or_model_import(tmp_path):
    component = tmp_path / "bad_import.py"
    component.write_bytes(b"import requests\n")

    with pytest.raises(RuntimeError, match="unauthorized modules"):
        _runner_static_safety(component)


@pytest.mark.parametrize("call_name", ("fit", "predict", "urlopen"))
def test_static_safety_rejects_model_or_network_call(tmp_path, call_name):
    component = tmp_path / "bad_call.py"
    component.write_text(
        f"def helper(value):\n    return value.{call_name}()\n",
        encoding="utf-8",
    )

    with pytest.raises(RuntimeError, match="forbidden calls"):
        _runner_static_safety(component)


def test_static_safety_requires_authorization_as_first_run_statement(tmp_path):
    component = tmp_path / "late_authorization.py"
    component.write_text(
        "class Runner:\n"
        "    def run(self):\n"
        "        value = 1\n"
        "        if value:\n"
        "            return value\n",
        encoding="utf-8",
    )

    with pytest.raises(RuntimeError, match="authorization first"):
        _runner_static_safety(component)
