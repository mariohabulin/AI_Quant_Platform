"""Static hash and safety review for the weekly persistent-UP hypothesis."""

from __future__ import annotations

import argparse
import ast
import hashlib
import json
from pathlib import Path

try:
    from kraken_weekly_persistent_up_momentum_hypothesis import (
        ASSET_ORDER,
        COMPONENT_ID,
        CONTROL_ORDER,
        DEVELOPMENT_GATES,
        DEVELOPMENT_SLICES,
        PARENT_COMMIT,
        PRIMARY_RULE_ID,
        PROTOCOL_ID,
        SAFETY_FLAGS,
        TERMINAL_12H_STATUS,
        validate_weekly_persistent_up_momentum_hypothesis,
        weekly_persistent_up_momentum_hypothesis_declaration,
    )
except ImportError:  # pragma: no cover - package import compatibility
    from .kraken_weekly_persistent_up_momentum_hypothesis import (
        ASSET_ORDER,
        COMPONENT_ID,
        CONTROL_ORDER,
        DEVELOPMENT_GATES,
        DEVELOPMENT_SLICES,
        PARENT_COMMIT,
        PRIMARY_RULE_ID,
        PROTOCOL_ID,
        SAFETY_FLAGS,
        TERMINAL_12H_STATUS,
        validate_weekly_persistent_up_momentum_hypothesis,
        weekly_persistent_up_momentum_hypothesis_declaration,
    )


SCHEMA_VERSION = 1
STATUS = "KRAKEN_WEEKLY_PERSISTENT_UP_MOMENTUM_HYPOTHESIS_STATIC_REVIEW_PASS"
EXPECTED_PARENT_COMMIT = "a9307dfe46078b1509c777710238057a81f790b5"
EXPECTED_HASHES = {
    "terminal_12h_result": "d9f1ac12d56571752dc78f13dc0157df3df7023be37e07448e75e0f700c87794",
    "round_2_closure": "725cdf931d34dac4d92aa7777d52cd8dab8476ffcf37e7630f1379e54f2b3ec3",
    "daily_dataset_protocol": "814cd561e1869023832315050683665c142f3b216ae354d45019a28edcc6a05a",
    "portfolio_protocol": "8615d0e9a21d0e3ca663626dd26f1ab19059e37e4fef39e0cf1954d55cdd0cd8",
    "protocol": "06c2e0f25a6a237b8b490d12865973c6c4d9118bd378e42c2113e41f907658f1",
    "component": "a8c22d3f2e4d1dc4584b1926fe537afec0962b33f0693e891b1ca657bc9a1772",
}

BOUND_PATHS = {
    "terminal_12h_result": (
        "KRAKEN_AI_DRIVEN_V2_REGIME_GATED_SELECTIVE_DEVELOPMENT_ATTEMPT_1_RESULT.md"
    ),
    "round_2_closure": "KRAKEN_AI_DRIVEN_V2_ROUND_2_CLOSURE.md",
    "daily_dataset_protocol": "KRAKEN_BTC_ETH_XRP_DAILY_DATASET_LOCK_PROTOCOL_V2.md",
    "portfolio_protocol": "SELECTIVE_SWING_PORTFOLIO_CONSTRUCTION_PROTOCOL_V1.md",
    "protocol": (
        "KRAKEN_BTC_ETH_XRP_WEEKLY_PERSISTENT_UP_MOMENTUM_"
        "HYPOTHESIS_PROTOCOL_V1.md"
    ),
    "component": "src/kraken_weekly_persistent_up_momentum_hypothesis.py",
}

ALLOWED_COMPONENT_IMPORTS = {"__future__", "copy", "hashlib", "json"}
FORBIDDEN_CALL_NAMES = {
    "open",
    "read_csv",
    "read_json",
    "read_parquet",
    "request",
    "urlopen",
}


def _checkout_stable_bytes(path):
    raw = Path(path).read_bytes()
    return raw.replace(b"\r\n", b"\n").replace(b"\r", b"\n")


def _checkout_stable_sha256(path):
    return hashlib.sha256(_checkout_stable_bytes(path)).hexdigest()


def _component_static_safety(path):
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
    unexpected_imports = imports - ALLOWED_COMPONENT_IMPORTS
    forbidden_calls = calls & FORBIDDEN_CALL_NAMES
    if unexpected_imports:
        raise RuntimeError(
            f"Weekly hypothesis imports non-declarative modules: {sorted(unexpected_imports)}."
        )
    if forbidden_calls:
        raise RuntimeError(
            f"Weekly hypothesis contains forbidden data calls: {sorted(forbidden_calls)}."
        )
    return {
        "allowed_imports_only": True,
        "forbidden_data_calls_absent": True,
        "parsed_python_ast": True,
    }


def review_weekly_persistent_up_momentum_hypothesis(root=None):
    root = Path(__file__).resolve().parents[1] if root is None else Path(root)
    paths = {name: root / relative for name, relative in BOUND_PATHS.items()}
    observed = {name: _checkout_stable_sha256(path) for name, path in paths.items()}
    for name, expected in EXPECTED_HASHES.items():
        if observed[name] != expected:
            raise RuntimeError(f"Weekly hypothesis source binding mismatch: {name}.")

    declaration = weekly_persistent_up_momentum_hypothesis_declaration()
    validate_weekly_persistent_up_momentum_hypothesis(declaration)
    if PARENT_COMMIT != EXPECTED_PARENT_COMMIT:
        raise RuntimeError("Weekly hypothesis parent commit mismatch.")
    if declaration["protocol_id"] != PROTOCOL_ID:
        raise RuntimeError("Weekly hypothesis protocol identity mismatch.")
    if declaration["component_id"] != COMPONENT_ID:
        raise RuntimeError("Weekly hypothesis component identity mismatch.")
    if tuple(declaration["asset_order"]) != ASSET_ORDER:
        raise RuntimeError("Weekly hypothesis asset order mismatch.")
    if declaration["primary_rule_id"] != PRIMARY_RULE_ID:
        raise RuntimeError("Weekly hypothesis primary rule mismatch.")
    if tuple(declaration["control_order"]) != CONTROL_ORDER:
        raise RuntimeError("Weekly hypothesis control registry mismatch.")
    if declaration["terminal_12h_status"] != TERMINAL_12H_STATUS:
        raise RuntimeError("Weekly hypothesis terminal 12h boundary mismatch.")
    if declaration["configuration"]["development"]["slices"] != [
        dict(item) for item in DEVELOPMENT_SLICES
    ]:
        raise RuntimeError("Weekly hypothesis Development slices mismatch.")
    if declaration["configuration"]["development"]["gates"] != DEVELOPMENT_GATES:
        raise RuntimeError("Weekly hypothesis Development gates mismatch.")
    if any(declaration[name] is not False for name in SAFETY_FLAGS):
        raise RuntimeError("Weekly hypothesis safety boundary mismatch.")

    static_safety = _component_static_safety(paths["component"])
    return {
        **declaration,
        "status": STATUS,
        "source_sha256_matches": {name: True for name in observed},
        "source_sha256": observed,
        "component_static_safety": static_safety,
        "prior_daily_rule_rounds_closed": True,
        "terminal_12h_research_remains_closed": True,
        "real_market_values_opened_by_review": False,
        "next_stage": "SEPARATE_SYNTHETIC_ONLY_IMPLEMENTATION_DECISION",
    }


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="Review the frozen weekly persistent-UP momentum hypothesis."
    )
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    args = parser.parse_args(argv)
    print(
        json.dumps(
            review_weekly_persistent_up_momentum_hypothesis(args.root),
            indent=2,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
