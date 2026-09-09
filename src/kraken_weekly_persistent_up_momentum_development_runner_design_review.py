"""Hash and AST review for the inert weekly Development runner design."""

from __future__ import annotations

import argparse
import ast
import hashlib
import json
from pathlib import Path

try:
    from kraken_weekly_persistent_up_momentum_development_runner_design import (
        ARCHIVE_SPEC,
        ASSET_ORDER,
        COMPONENT_ID,
        CONTROL_ORDER,
        DESIGN_FALSE_FLAGS,
        DESIGN_TRUE_FLAGS,
        DEVELOPMENT_GATES,
        DEVELOPMENT_SLICES,
        EVIDENCE_FILE_ORDER,
        EXPECTED_DEVELOPMENT_SOURCE,
        EXPECTED_INVALID_MARKET_WEEK_STARTS,
        FUTURE_AUTHORIZATION_PHRASE,
        HYPOTHESIS_PROTOCOL_ID,
        MEMBER_BASENAME_BY_ASSET,
        PARENT_COMMIT,
        PRIMARY_RULE_ID,
        PROTOCOL_ID,
        RULE_ORDER,
        SOURCE_BINDING_SHA256,
        SYNTHETIC_PROTOCOL_ID,
        validate_weekly_development_runner_design,
        weekly_development_runner_design_declaration,
    )
except ImportError:  # pragma: no cover - package import compatibility
    from .kraken_weekly_persistent_up_momentum_development_runner_design import (
        ARCHIVE_SPEC,
        ASSET_ORDER,
        COMPONENT_ID,
        CONTROL_ORDER,
        DESIGN_FALSE_FLAGS,
        DESIGN_TRUE_FLAGS,
        DEVELOPMENT_GATES,
        DEVELOPMENT_SLICES,
        EVIDENCE_FILE_ORDER,
        EXPECTED_DEVELOPMENT_SOURCE,
        EXPECTED_INVALID_MARKET_WEEK_STARTS,
        FUTURE_AUTHORIZATION_PHRASE,
        HYPOTHESIS_PROTOCOL_ID,
        MEMBER_BASENAME_BY_ASSET,
        PARENT_COMMIT,
        PRIMARY_RULE_ID,
        PROTOCOL_ID,
        RULE_ORDER,
        SOURCE_BINDING_SHA256,
        SYNTHETIC_PROTOCOL_ID,
        validate_weekly_development_runner_design,
        weekly_development_runner_design_declaration,
    )


SCHEMA_VERSION = 1
STATUS = (
    "KRAKEN_WEEKLY_PERSISTENT_UP_MOMENTUM_DEVELOPMENT_RUNNER_"
    "DESIGN_STATIC_REVIEW_PASS"
)
EXPECTED_PARENT_COMMIT = "615cc8544aeeddda7163b59a343f099c96d49789"
EXPECTED_ARCHIVE_SHA256 = (
    "e6ab4a3d2fe3be99167607fa28f230a84a038ad3ea3348ef81dc4bffcabb758d"
)
EXPECTED_DATASET_MANIFEST_SHA256 = (
    "8c91b42f2bc0c16a0ef0c6b4373572ac53fbf7f5937d4ebbbe75a0d39483df1c"
)
EXPECTED_HASHES = {
    **SOURCE_BINDING_SHA256,
    "runner_design_protocol": (
        "8aaf29337e124a27ff303db1158d565d790bdd1bd7c59f05db5b017ae7ee8163"
    ),
    "runner_design_component": (
        "89bd2bc3e13827f729e7af3f9e69280cb5134748ae3d9b62f5d3ba0f2089e97d"
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
}

ALLOWED_DESIGN_IMPORTS = {"__future__", "copy", "hashlib", "json"}
FORBIDDEN_CALL_NAMES = {
    "open",
    "Path",
    "ZipFile",
    "read_bytes",
    "read_csv",
    "read_json",
    "read_parquet",
    "read_text",
    "request",
    "urlopen",
}


def _checkout_stable_bytes(path):
    raw = Path(path).read_bytes()
    return raw.replace(b"\r\n", b"\n").replace(b"\r", b"\n")


def _checkout_stable_sha256(path):
    return hashlib.sha256(_checkout_stable_bytes(path)).hexdigest()


def _design_static_safety(path):
    source = _checkout_stable_bytes(path).decode("utf-8")
    tree = ast.parse(source)
    imports = set()
    calls = set()
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
    unexpected_imports = imports - ALLOWED_DESIGN_IMPORTS
    forbidden_calls = calls & FORBIDDEN_CALL_NAMES
    if unexpected_imports:
        raise RuntimeError(
            f"Weekly runner design imports unauthorized modules: {sorted(unexpected_imports)}."
        )
    if forbidden_calls:
        raise RuntimeError(
            f"Weekly runner design contains forbidden data calls: {sorted(forbidden_calls)}."
        )
    return {
        "allowed_declarative_imports_only": True,
        "filesystem_calls_absent": True,
        "network_calls_absent": True,
        "parsed_python_ast": True,
    }


def review_weekly_development_runner_design(root=None):
    root = Path(__file__).resolve().parents[1] if root is None else Path(root)
    paths = {name: root / relative for name, relative in BOUND_PATHS.items()}
    observed = {name: _checkout_stable_sha256(path) for name, path in paths.items()}
    for name, expected in EXPECTED_HASHES.items():
        if observed[name] != expected:
            raise RuntimeError(f"Weekly runner design source binding mismatch: {name}.")

    declaration = weekly_development_runner_design_declaration()
    validate_weekly_development_runner_design(declaration)
    configuration = declaration["configuration"]
    if PARENT_COMMIT != EXPECTED_PARENT_COMMIT:
        raise RuntimeError("Weekly runner design parent commit mismatch.")
    if declaration["protocol_id"] != PROTOCOL_ID:
        raise RuntimeError("Weekly runner design protocol identity mismatch.")
    if declaration["component_id"] != COMPONENT_ID:
        raise RuntimeError("Weekly runner design component identity mismatch.")
    if declaration["hypothesis_protocol_id"] != HYPOTHESIS_PROTOCOL_ID:
        raise RuntimeError("Weekly runner design hypothesis identity mismatch.")
    if declaration["synthetic_protocol_id"] != SYNTHETIC_PROTOCOL_ID:
        raise RuntimeError("Weekly runner design synthetic identity mismatch.")
    if declaration["archive_spec"] != ARCHIVE_SPEC:
        raise RuntimeError("Weekly runner design archive identity mismatch.")
    if ARCHIVE_SPEC["sha256"] != EXPECTED_ARCHIVE_SHA256:
        raise RuntimeError("Weekly runner design archive hash mismatch.")
    if declaration["dataset_manifest_sha256"] != EXPECTED_DATASET_MANIFEST_SHA256:
        raise RuntimeError("Weekly runner design dataset-manifest mismatch.")
    if tuple(configuration["source"]["asset_order"]) != ASSET_ORDER:
        raise RuntimeError("Weekly runner design asset order mismatch.")
    if configuration["source"]["member_basename_by_asset"] != MEMBER_BASENAME_BY_ASSET:
        raise RuntimeError("Weekly runner design member registry mismatch.")
    if configuration["partition"]["expected_source_by_asset"] != EXPECTED_DEVELOPMENT_SOURCE:
        raise RuntimeError("Weekly runner design Development source identity mismatch.")
    if tuple(configuration["adapter"]["expected_invalid_market_week_starts"]) != EXPECTED_INVALID_MARKET_WEEK_STARTS:
        raise RuntimeError("Weekly runner design invalid-week identity mismatch.")
    if tuple(configuration["experiment"]["rule_order"]) != RULE_ORDER:
        raise RuntimeError("Weekly runner design rule registry mismatch.")
    if configuration["experiment"]["primary_rule_id"] != PRIMARY_RULE_ID:
        raise RuntimeError("Weekly runner design primary rule mismatch.")
    if tuple(configuration["experiment"]["control_order"]) != CONTROL_ORDER:
        raise RuntimeError("Weekly runner design control registry mismatch.")
    if configuration["experiment"]["gates"] != DEVELOPMENT_GATES:
        raise RuntimeError("Weekly runner design gate registry mismatch.")
    observed_slices = tuple(
        (item["slice_id"], item["start_inclusive"], item["end_exclusive"])
        for item in configuration["experiment"]["slices"]
    )
    if observed_slices != DEVELOPMENT_SLICES:
        raise RuntimeError("Weekly runner design slice registry mismatch.")
    if tuple(configuration["evidence"]["file_order"]) != EVIDENCE_FILE_ORDER:
        raise RuntimeError("Weekly runner design evidence registry mismatch.")
    if declaration["future_authorization_phrase"] != FUTURE_AUTHORIZATION_PHRASE:
        raise RuntimeError("Weekly runner design future authorization mismatch.")
    if any(declaration[name] is not True for name in DESIGN_TRUE_FLAGS):
        raise RuntimeError("Weekly runner design completeness boundary mismatch.")
    if any(declaration[name] is not False for name in DESIGN_FALSE_FLAGS):
        raise RuntimeError("Weekly runner design safety boundary mismatch.")

    return {
        **declaration,
        "schema_version": SCHEMA_VERSION,
        "status": STATUS,
        "source_sha256": observed,
        "source_sha256_matches": {name: True for name in observed},
        "design_static_safety": _design_static_safety(
            paths["runner_design_component"]
        ),
        "real_market_values_opened_by_review": False,
        "synthetic_fixture_executed_by_review": False,
        "next_stage": (
            "SEPARATE_HASH_BOUND_DEVELOPMENT_RUNNER_IMPLEMENTATION_DECISION"
        ),
    }


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="Review the frozen weekly Development runner design."
    )
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    args = parser.parse_args(argv)
    print(
        json.dumps(
            review_weekly_development_runner_design(args.root),
            indent=2,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
