"""Hash and AST review for the weekly synthetic-only momentum engine."""

from __future__ import annotations

import argparse
import ast
import hashlib
import json
from pathlib import Path

try:
    from kraken_weekly_persistent_up_momentum_synthetic import (
        ASSET_ORDER,
        COMPONENT_ID,
        COST_PROFILE_ORDER,
        DAILY_FIELD_ORDER,
        INPUT_MODE,
        PARENT_COMMIT,
        PROTOCOL_ID,
        REAL_SAFETY_FLAGS,
        RULE_ORDER,
        SYNTHETIC_AUTHORIZATION_TOKEN,
        synthetic_implementation_declaration,
        validate_synthetic_implementation_declaration,
    )
except ImportError:  # pragma: no cover - package import compatibility
    from .kraken_weekly_persistent_up_momentum_synthetic import (
        ASSET_ORDER,
        COMPONENT_ID,
        COST_PROFILE_ORDER,
        DAILY_FIELD_ORDER,
        INPUT_MODE,
        PARENT_COMMIT,
        PROTOCOL_ID,
        REAL_SAFETY_FLAGS,
        RULE_ORDER,
        SYNTHETIC_AUTHORIZATION_TOKEN,
        synthetic_implementation_declaration,
        validate_synthetic_implementation_declaration,
    )


SCHEMA_VERSION = 1
STATUS = "KRAKEN_WEEKLY_PERSISTENT_UP_MOMENTUM_SYNTHETIC_STATIC_REVIEW_PASS"
EXPECTED_PARENT_COMMIT = "f7ca20a77f203a4a732d79d5fda4812954a956b2"
EXPECTED_HASHES = {
    "line_ending_policy": (
        "0cc450c4a2fe9a9fdf974fba4a75e7cd5d63b5897469b4f28e888d7c1bc1185e"
    ),
    "hypothesis_protocol": (
        "06c2e0f25a6a237b8b490d12865973c6c4d9118bd378e42c2113e41f907658f1"
    ),
    "hypothesis_component": (
        "a8c22d3f2e4d1dc4584b1926fe537afec0962b33f0693e891b1ca657bc9a1772"
    ),
    "hypothesis_review": (
        "b362a2f8b70f44ae07357e34dcadc97141a96695e1327d0694193035add6fc92"
    ),
    "synthetic_protocol": (
        "297bccf162d780748cdc6dbd120989f73c76489fba97d445c4baf8f5413604c3"
    ),
    "synthetic_component": (
        "cae67fe56a008f1c9639f570d443c167ede4c5cb93ece291b4d1a29a0e7c0bc8"
    ),
}

BOUND_PATHS = {
    "line_ending_policy": ".gitattributes",
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
}

ALLOWED_ENGINE_IMPORTS = {
    "__future__",
    "copy",
    "datetime",
    "decimal",
    "kraken_weekly_persistent_up_momentum_hypothesis",
}
FORBIDDEN_CALL_NAMES = {
    "open",
    "Path",
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


def _engine_static_safety(path):
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
    unexpected_imports = imports - ALLOWED_ENGINE_IMPORTS
    forbidden_calls = calls & FORBIDDEN_CALL_NAMES
    if unexpected_imports:
        raise RuntimeError(
            f"Synthetic engine imports unauthorized modules: {sorted(unexpected_imports)}."
        )
    if forbidden_calls:
        raise RuntimeError(
            f"Synthetic engine contains forbidden data calls: {sorted(forbidden_calls)}."
        )
    return {
        "allowed_imports_only": True,
        "filesystem_calls_absent": True,
        "network_calls_absent": True,
        "parsed_python_ast": True,
    }


def review_weekly_persistent_up_momentum_synthetic(root=None):
    root = Path(__file__).resolve().parents[1] if root is None else Path(root)
    paths = {name: root / relative for name, relative in BOUND_PATHS.items()}
    observed = {name: _checkout_stable_sha256(path) for name, path in paths.items()}
    for name, expected in EXPECTED_HASHES.items():
        if observed[name] != expected:
            raise RuntimeError(f"Weekly synthetic source binding mismatch: {name}.")

    declaration = synthetic_implementation_declaration()
    validate_synthetic_implementation_declaration(declaration)
    if PARENT_COMMIT != EXPECTED_PARENT_COMMIT:
        raise RuntimeError("Weekly synthetic parent commit mismatch.")
    if declaration["protocol_id"] != PROTOCOL_ID:
        raise RuntimeError("Weekly synthetic protocol identity mismatch.")
    if declaration["component_id"] != COMPONENT_ID:
        raise RuntimeError("Weekly synthetic component identity mismatch.")
    if declaration["input_mode"] != INPUT_MODE:
        raise RuntimeError("Weekly synthetic input mode mismatch.")
    if tuple(declaration["asset_order"]) != ASSET_ORDER:
        raise RuntimeError("Weekly synthetic asset order mismatch.")
    if tuple(declaration["daily_field_order"]) != DAILY_FIELD_ORDER:
        raise RuntimeError("Weekly synthetic daily schema mismatch.")
    if tuple(declaration["rule_order"]) != RULE_ORDER:
        raise RuntimeError("Weekly synthetic rule order mismatch.")
    if tuple(declaration["cost_profile_order"]) != COST_PROFILE_ORDER:
        raise RuntimeError("Weekly synthetic cost-profile order mismatch.")
    if declaration["synthetic_authorization_token"] != SYNTHETIC_AUTHORIZATION_TOKEN:
        raise RuntimeError("Weekly synthetic authorization token mismatch.")
    if any(declaration[name] is not False for name in REAL_SAFETY_FLAGS):
        raise RuntimeError("Weekly synthetic real-data safety boundary mismatch.")

    return {
        **declaration,
        "schema_version": SCHEMA_VERSION,
        "status": STATUS,
        "source_sha256": observed,
        "source_sha256_matches": {name: True for name in observed},
        "engine_static_safety": _engine_static_safety(paths["synthetic_component"]),
        "real_market_values_opened_by_review": False,
        "synthetic_fixture_executed_by_review": False,
        "next_stage": "SEPARATE_HASH_BOUND_DEVELOPMENT_RUNNER_DESIGN_DECISION",
    }


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="Review the weekly persistent-UP synthetic-only engine."
    )
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    args = parser.parse_args(argv)
    print(
        json.dumps(
            review_weekly_persistent_up_momentum_synthetic(args.root),
            indent=2,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
