"""Static hash, AST and safety review for the weekly Development runner."""

from __future__ import annotations

import argparse
import ast
import hashlib
import json
from pathlib import Path

try:
    from kraken_weekly_persistent_up_momentum_development_runner import (
        ASSET_ORDER,
        AUTHORIZATION_PHRASE,
        COMPONENT_ID,
        DECLARATION_FALSE_FLAGS,
        DEVELOPMENT_GATES,
        DEVELOPMENT_SLICES,
        EVIDENCE_FILE_ORDER,
        EXPECTED_DEVELOPMENT_SOURCE,
        FROZEN_ARCHIVE_SPEC,
        IMPLEMENTATION_TRUE_FLAGS,
        MEMBER_BASENAME_BY_ASSET,
        PARENT_COMMIT,
        PROTOCOL_ID,
        RULE_ORDER,
        RUNNER_SYNTHETIC_TEST_TOKEN,
        SOURCE_BINDING_SHA256,
        runner_declaration,
    )
    from kraken_weekly_persistent_up_momentum_synthetic import (
        SYNTHETIC_AUTHORIZATION_TOKEN,
    )
except ImportError:  # pragma: no cover - package import compatibility
    from .kraken_weekly_persistent_up_momentum_development_runner import (
        ASSET_ORDER,
        AUTHORIZATION_PHRASE,
        COMPONENT_ID,
        DECLARATION_FALSE_FLAGS,
        DEVELOPMENT_GATES,
        DEVELOPMENT_SLICES,
        EVIDENCE_FILE_ORDER,
        EXPECTED_DEVELOPMENT_SOURCE,
        FROZEN_ARCHIVE_SPEC,
        IMPLEMENTATION_TRUE_FLAGS,
        MEMBER_BASENAME_BY_ASSET,
        PARENT_COMMIT,
        PROTOCOL_ID,
        RULE_ORDER,
        RUNNER_SYNTHETIC_TEST_TOKEN,
        SOURCE_BINDING_SHA256,
        runner_declaration,
    )
    from .kraken_weekly_persistent_up_momentum_synthetic import (
        SYNTHETIC_AUTHORIZATION_TOKEN,
    )


SCHEMA_VERSION = 1
STATUS = (
    "KRAKEN_WEEKLY_PERSISTENT_UP_MOMENTUM_DEVELOPMENT_RUNNER_STATIC_REVIEW_PASS"
)
EXPECTED_PARENT_COMMIT = "0b51b8455f218793605cc6da086862e96776e50d"
EXPECTED_ARCHIVE_SHA256 = (
    "e6ab4a3d2fe3be99167607fa28f230a84a038ad3ea3348ef81dc4bffcabb758d"
)
EXPECTED_HASHES = {
    **SOURCE_BINDING_SHA256,
    "runner_implementation_protocol": (
        "a38504231acbf5416ec62941b4306ea30bb48677b168a2b327181508c4960b3d"
    ),
    "runner_component": (
        "882cd03adbcc22d80adb7c929d29432d60e98517aee26daad8003f03420344e9"
    ),
}

BOUND_PATHS = {
    "line_ending_policy": ".gitattributes",
    "daily_dataset_protocol": "KRAKEN_BTC_ETH_XRP_DAILY_DATASET_LOCK_PROTOCOL_V2.md",
    "daily_dataset_evidence": "KRAKEN_BTC_ETH_XRP_DAILY_DATASET_LOCK_EVIDENCE_V2.md",
    "daily_dataset_component": "src/kraken_daily_dataset.py",
    "partition_protocol": (
        "KRAKEN_BTC_ETH_XRP_AI_DRIVEN_V2_PARTITION_PROTOCOL_V1.md"
    ),
    "partition_component": "src/kraken_ai_driven_v2_partition.py",
    "partition_review": "src/kraken_ai_driven_v2_partition_review.py",
    "hypothesis_protocol": (
        "KRAKEN_BTC_ETH_XRP_WEEKLY_PERSISTENT_UP_MOMENTUM_"
        "HYPOTHESIS_PROTOCOL_V1.md"
    ),
    "hypothesis_component": (
        "src/kraken_weekly_persistent_up_momentum_hypothesis.py"
    ),
    "hypothesis_review": (
        "src/kraken_weekly_persistent_up_momentum_hypothesis_review.py"
    ),
    "synthetic_protocol": (
        "KRAKEN_BTC_ETH_XRP_WEEKLY_PERSISTENT_UP_MOMENTUM_"
        "SYNTHETIC_IMPLEMENTATION_PROTOCOL_V1.md"
    ),
    "synthetic_component": (
        "src/kraken_weekly_persistent_up_momentum_synthetic.py"
    ),
    "synthetic_review": (
        "src/kraken_weekly_persistent_up_momentum_synthetic_review.py"
    ),
    "runner_design_protocol": (
        "KRAKEN_BTC_ETH_XRP_WEEKLY_PERSISTENT_UP_MOMENTUM_"
        "DEVELOPMENT_RUNNER_PROTOCOL_V1.md"
    ),
    "runner_design_component": (
        "src/kraken_weekly_persistent_up_momentum_"
        "development_runner_design.py"
    ),
    "runner_design_review": (
        "src/kraken_weekly_persistent_up_momentum_"
        "development_runner_design_review.py"
    ),
    "runner_implementation_protocol": (
        "KRAKEN_BTC_ETH_XRP_WEEKLY_PERSISTENT_UP_MOMENTUM_"
        "DEVELOPMENT_RUNNER_IMPLEMENTATION_PROTOCOL_V1.md"
    ),
    "runner_component": (
        "src/kraken_weekly_persistent_up_momentum_development_runner.py"
    ),
}

ALLOWED_RUNNER_IMPORTS = {
    "__future__",
    "argparse",
    "copy",
    "dataclasses",
    "datetime",
    "decimal",
    "hashlib",
    "json",
    "os",
    "pathlib",
    "zipfile",
    "kraken_weekly_persistent_up_momentum_development_runner_design",
    "kraken_weekly_persistent_up_momentum_synthetic",
}
FORBIDDEN_IMPORTS = {
    "http",
    "numpy",
    "pandas",
    "pickle",
    "requests",
    "sklearn",
    "socket",
    "subprocess",
    "urllib",
}
FORBIDDEN_CALL_NAMES = {
    "fit",
    "fit_predict",
    "popen",
    "predict",
    "read_csv",
    "read_parquet",
    "request",
    "system",
    "urlopen",
}


def _checkout_stable_bytes(path):
    raw = Path(path).read_bytes()
    return raw.replace(b"\r\n", b"\n").replace(b"\r", b"\n")


def _checkout_stable_sha256(path):
    return hashlib.sha256(_checkout_stable_bytes(path)).hexdigest()


def _runner_static_safety(path):
    source = _checkout_stable_bytes(path).decode("utf-8")
    tree = ast.parse(source)
    imports = set()
    calls = set()
    run_body = None
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imports.update(alias.name.split(".", 1)[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            imports.add((node.module or "").split(".", 1)[0])
        elif isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name):
                calls.add(node.func.id)
            elif isinstance(node.func, ast.Attribute):
                calls.add(node.func.attr)
        elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name == "run":
            run_body = node.body
    unexpected = imports - ALLOWED_RUNNER_IMPORTS
    forbidden_imports = imports & FORBIDDEN_IMPORTS
    forbidden_calls = calls & FORBIDDEN_CALL_NAMES
    if unexpected:
        raise RuntimeError(f"Weekly runner imports unauthorized modules: {sorted(unexpected)}.")
    if forbidden_imports:
        raise RuntimeError(f"Weekly runner imports forbidden modules: {sorted(forbidden_imports)}.")
    if forbidden_calls:
        raise RuntimeError(f"Weekly runner contains forbidden calls: {sorted(forbidden_calls)}.")
    if not run_body or not isinstance(run_body[0], ast.If):
        raise RuntimeError("Weekly runner does not check authorization first.")
    return {
        "allowed_imports_only": True,
        "network_imports_absent": True,
        "model_imports_absent": True,
        "model_fit_calls_absent": True,
        "authorization_check_is_first_statement": True,
        "parsed_python_ast": True,
    }


def review_weekly_development_runner(root=None):
    root = Path(__file__).resolve().parents[1] if root is None else Path(root)
    paths = {name: root / relative for name, relative in BOUND_PATHS.items()}
    observed = {name: _checkout_stable_sha256(path) for name, path in paths.items()}
    for name, expected in EXPECTED_HASHES.items():
        if observed[name] != expected:
            raise RuntimeError(f"Weekly Development runner binding mismatch: {name}.")

    declaration = runner_declaration()
    if PARENT_COMMIT != EXPECTED_PARENT_COMMIT:
        raise RuntimeError("Weekly Development runner parent commit mismatch.")
    if declaration["protocol_id"] != PROTOCOL_ID:
        raise RuntimeError("Weekly Development runner protocol identity mismatch.")
    if declaration["component_id"] != COMPONENT_ID:
        raise RuntimeError("Weekly Development runner component identity mismatch.")
    if declaration["frozen_archive_spec"] != FROZEN_ARCHIVE_SPEC:
        raise RuntimeError("Weekly Development runner archive identity mismatch.")
    if FROZEN_ARCHIVE_SPEC["sha256"] != EXPECTED_ARCHIVE_SHA256:
        raise RuntimeError("Weekly Development runner archive hash mismatch.")
    if tuple(declaration["asset_order"]) != ASSET_ORDER:
        raise RuntimeError("Weekly Development runner asset order mismatch.")
    if tuple(declaration["rule_order"]) != RULE_ORDER:
        raise RuntimeError("Weekly Development runner rule order mismatch.")
    if declaration["development_slices"] != [list(item) for item in DEVELOPMENT_SLICES]:
        raise RuntimeError("Weekly Development runner slice registry mismatch.")
    if declaration["development_gates"] != DEVELOPMENT_GATES:
        raise RuntimeError("Weekly Development runner gate registry mismatch.")
    if tuple(declaration["evidence_file_order"]) != EVIDENCE_FILE_ORDER:
        raise RuntimeError("Weekly Development runner evidence registry mismatch.")
    if tuple(MEMBER_BASENAME_BY_ASSET) != ASSET_ORDER:
        raise RuntimeError("Weekly Development runner member order mismatch.")
    if tuple(EXPECTED_DEVELOPMENT_SOURCE) != ASSET_ORDER:
        raise RuntimeError("Weekly Development runner source order mismatch.")
    if declaration["authorization_phrase"] != AUTHORIZATION_PHRASE:
        raise RuntimeError("Weekly Development runner authorization mismatch.")
    if RUNNER_SYNTHETIC_TEST_TOKEN == SYNTHETIC_AUTHORIZATION_TOKEN:
        raise RuntimeError("Weekly Development runner reuses synthetic engine token.")
    if declaration["model_artifact_count"] != 0:
        raise RuntimeError("Weekly Development runner model-artifact boundary mismatch.")
    if any(declaration[name] is not True for name in IMPLEMENTATION_TRUE_FLAGS):
        raise RuntimeError("Weekly Development runner implementation boundary mismatch.")
    if any(declaration[name] is not False for name in DECLARATION_FALSE_FLAGS):
        raise RuntimeError("Weekly Development runner safety boundary mismatch.")

    return {
        **declaration,
        "schema_version": SCHEMA_VERSION,
        "status": STATUS,
        "source_sha256": observed,
        "source_sha256_matches": {name: True for name in observed},
        "runner_static_safety": _runner_static_safety(paths["runner_component"]),
        "source_values_opened_by_review": False,
        "kraken_archive_opened_by_review": False,
        "synthetic_fixture_executed_by_review": False,
        "development_run_executed_by_review": False,
        "next_stage": "SEPARATE_READ_ONLY_DEVELOPMENT_PREFLIGHT_DECISION",
    }


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="Review the hash-bound weekly Persistent-UP Development runner."
    )
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    args = parser.parse_args(argv)
    print(
        json.dumps(
            review_weekly_development_runner(args.root),
            indent=2,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
