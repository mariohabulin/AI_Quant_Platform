"""Static hash and safety review for the regime-gated selective hypothesis."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

try:
    from kraken_ai_driven_v2_regime_gated_selective_hypothesis import (
        COMPONENT_ID,
        CONTEXT_CONFIRMATION_FEATURE_COLUMNS,
        FOLD_PLAN,
        MATCHED_CONTROL,
        PARENT_COMMIT,
        PRIOR_CLOSURE_STATUS,
        PROTOCOL_ID,
        REGIME_FEATURE_COLUMNS,
        TERMINAL_FAILURE_STATUS,
        VARIANT_SPECS,
        fold_plan_is_causal,
        regime_gated_selective_hypothesis_declaration,
    )
except ImportError:  # pragma: no cover - package import compatibility
    from .kraken_ai_driven_v2_regime_gated_selective_hypothesis import (
        COMPONENT_ID,
        CONTEXT_CONFIRMATION_FEATURE_COLUMNS,
        FOLD_PLAN,
        MATCHED_CONTROL,
        PARENT_COMMIT,
        PRIOR_CLOSURE_STATUS,
        PROTOCOL_ID,
        REGIME_FEATURE_COLUMNS,
        TERMINAL_FAILURE_STATUS,
        VARIANT_SPECS,
        fold_plan_is_causal,
        regime_gated_selective_hypothesis_declaration,
    )


SCHEMA_VERSION = 1
STATUS = (
    "KRAKEN_AI_V2_REGIME_GATED_SELECTIVE_DEVELOPMENT_HYPOTHESIS_"
    "REVIEWED_RUNNER_REQUIRED"
)
EXPECTED_PARENT_COMMIT = "0511fe567c8da4afc436697771ac7d9d1d281f2b"
EXPECTED_HASHES = {
    "bidirectional_forensic_result": (
        "eaad73eadeb83a19dad4031edb19c4e7ebeb0c50c3681394e41e41ded50a4920"
    ),
    "bidirectional_forensic_protocol": (
        "55a21dbc3c29203474c9ab3fa51648abf62b8cb8fb241b14ddee53160ebca3ef"
    ),
    "bidirectional_forensic_component": (
        "4af5ada205b5fc55724d9900651fd3495f922168c0d625ef7b60347387be12a5"
    ),
    "bidirectional_forensic_review": (
        "c2ec3582d93759d64044ad534b5ba26d19d43b80a73dee92592aeec8eee8876b"
    ),
    "bidirectional_hypothesis_component": (
        "68e9a61e0614e7159a2f5279e4158bc9a6c781c61061b5458a67ff9dd8d8a80c"
    ),
    "derivatives_context_hypothesis_component": (
        "5355bb5d8e672d539776fc88705f2864b4974a767b12aaabfd4615aeb42288b3"
    ),
    "protocol": "788338f8c66f3bdf326086e03ea91123346fe48d69cc5161b2b1dc1f156e3553",
    "component": "1bb60a99b2b29741b89ab048b8a5942014c3d41eaa4e5b9a5ac4a760732d4594",
}


def _sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def review_regime_gated_selective_hypothesis(root=None):
    root = Path(__file__).resolve().parents[1] if root is None else Path(root)
    paths = {
        "bidirectional_forensic_result": root
        / "KRAKEN_AI_DRIVEN_V2_BIDIRECTIONAL_SCORE_POLARITY_FORENSIC_REVIEW_ATTEMPT_1_RESULT.md",
        "bidirectional_forensic_protocol": root
        / "KRAKEN_BTC_ETH_XRP_AI_DRIVEN_V2_BIDIRECTIONAL_SCORE_POLARITY_FORENSIC_REVIEW_PROTOCOL_V1.md",
        "bidirectional_forensic_component": root
        / "src"
        / "kraken_ai_driven_v2_bidirectional_score_polarity_forensic_review.py",
        "bidirectional_forensic_review": root
        / "src"
        / "kraken_ai_driven_v2_bidirectional_score_polarity_forensic_review_review.py",
        "bidirectional_hypothesis_component": root
        / "src"
        / "kraken_ai_driven_v2_bidirectional_hypothesis.py",
        "derivatives_context_hypothesis_component": root
        / "src"
        / "kraken_ai_driven_v2_derivatives_context_hypothesis.py",
        "protocol": root
        / "KRAKEN_BTC_ETH_XRP_AI_DRIVEN_V2_REGIME_GATED_SELECTIVE_DEVELOPMENT_HYPOTHESIS_PROTOCOL_V1.md",
        "component": root
        / "src"
        / "kraken_ai_driven_v2_regime_gated_selective_hypothesis.py",
    }
    observed = {name: _sha256(path) for name, path in paths.items()}
    for name, expected in EXPECTED_HASHES.items():
        if observed[name] != expected:
            raise RuntimeError(f"Regime-gated hypothesis binding mismatch: {name}.")

    declaration = regime_gated_selective_hypothesis_declaration()
    if PARENT_COMMIT != EXPECTED_PARENT_COMMIT:
        raise RuntimeError("Regime-gated hypothesis parent commit mismatch.")
    if declaration["protocol_id"] != PROTOCOL_ID:
        raise RuntimeError("Regime-gated hypothesis protocol identity mismatch.")
    if declaration["component_id"] != COMPONENT_ID:
        raise RuntimeError("Regime-gated hypothesis component identity mismatch.")
    if PRIOR_CLOSURE_STATUS != declaration["prior_closure_status"]:
        raise RuntimeError("Regime-gated prior closure mismatch.")
    if tuple(declaration["regime_feature_order"]) != REGIME_FEATURE_COLUMNS:
        raise RuntimeError("Regime-gated feature registry mismatch.")
    if (
        tuple(declaration["context_confirmation_feature_order"])
        != CONTEXT_CONFIRMATION_FEATURE_COLUMNS
    ):
        raise RuntimeError("Regime-gated context confirmation registry mismatch.")
    if tuple(declaration["variant_order"]) != tuple(VARIANT_SPECS):
        raise RuntimeError("Regime-gated variant registry mismatch.")
    if declaration["matched_control"] != MATCHED_CONTROL:
        raise RuntimeError("Regime-gated matched control mismatch.")
    if declaration["fold_plan"] != [dict(fold) for fold in FOLD_PLAN]:
        raise RuntimeError("Regime-gated fold plan mismatch.")
    if not fold_plan_is_causal():
        raise RuntimeError("Regime-gated fold plan is not causal.")
    if declaration["new_indicator_count"] != 0:
        raise RuntimeError("Regime-gated hypothesis added an indicator.")
    if declaration["maximum_total_fits"] != 24:
        raise RuntimeError("Regime-gated fit budget mismatch.")
    if declaration["terminal_failure_status"] != TERMINAL_FAILURE_STATUS:
        raise RuntimeError("Regime-gated terminal stop mismatch.")
    if declaration["one_economic_development_execution"] is not True:
        raise RuntimeError("Regime-gated execution budget mismatch.")

    required_false = (
        "source_values_opened",
        "labels_generated",
        "model_training_executed",
        "direct_net_r_regression_authorized",
        "feature_search_authorized",
        "hyperparameter_sweep_authorized",
        "threshold_sweep_authorized",
        "top_k_rule_authorized",
        "automatic_model_selection",
        "automatic_successor_authorized",
        "calibration_data_opened",
        "evaluation_data_opened",
        "candidate_v2_authorized",
        "bounded_forward_paper_authorized",
        "cloud_execution_authorized",
        "real_orders_submitted",
        "live_execution_authorized",
    )
    if any(declaration[field] is not False for field in required_false):
        raise RuntimeError("Regime-gated hypothesis safety boundary mismatch.")

    return {
        **declaration,
        "status": STATUS,
        "source_sha256_matches": {name: True for name in observed},
        "protocol_sha256": observed["protocol"],
        "protocol_sha256_match": True,
        "component_sha256": observed["component"],
        "component_sha256_match": True,
        "prior_bidirectional_hypothesis_closed": True,
        "strict_regime_gate_implemented": True,
        "directional_context_confirmation_implemented": True,
        "payoff_derived_probability_threshold_implemented": True,
        "terminal_research_stop_implemented": True,
        "next_stage": (
            "IMPLEMENT_HASH_BOUND_REGIME_GATED_SELECTIVE_DEVELOPMENT_RUNNER"
        ),
    }


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="Review the frozen regime-gated selective hypothesis."
    )
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    args = parser.parse_args(argv)
    print(
        json.dumps(
            review_regime_gated_selective_hypothesis(args.root),
            indent=2,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
