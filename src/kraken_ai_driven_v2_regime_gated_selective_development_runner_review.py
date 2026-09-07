"""Static hash and safety review for the regime-gated selective runner."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

try:
    from kraken_ai_driven_v2_regime_gated_selective_development_runner import (
        AUTHORIZATION_PHRASE,
        COMPONENT_ID,
        DATASET_MANIFEST_SHA256,
        DIRECTION_ORDER,
        MATCHED_CONTROL,
        PARENT_COMMIT,
        PROTOCOL_ID,
        SOURCE_BINDING_SHA256,
        TERMINAL_FAILURE_STATUS,
        VARIANT_SPECS,
        runner_declaration,
    )
except ImportError:  # pragma: no cover - package import compatibility
    from .kraken_ai_driven_v2_regime_gated_selective_development_runner import (
        AUTHORIZATION_PHRASE,
        COMPONENT_ID,
        DATASET_MANIFEST_SHA256,
        DIRECTION_ORDER,
        MATCHED_CONTROL,
        PARENT_COMMIT,
        PROTOCOL_ID,
        SOURCE_BINDING_SHA256,
        TERMINAL_FAILURE_STATUS,
        VARIANT_SPECS,
        runner_declaration,
    )


SCHEMA_VERSION = 1
STATUS = "KRAKEN_AI_V2_REGIME_GATED_SELECTIVE_DEVELOPMENT_RUNNER_REVIEWED"
EXPECTED_PARENT_COMMIT = "87927efa5f99e52ec0b6dba1fb2b10c4711e43f2"
EXPECTED_DATASET_MANIFEST_SHA256 = (
    "db4dde045d9fce22bee1389fe8c7ad13d3e3ccc5e5c4ace7c433f5461ba11916"
)
EXPECTED_HASHES = {
    **SOURCE_BINDING_SHA256,
    "runner_protocol": (
        "b8e89cd9b9a4b8d6f4c207bac96a3b9cd1bcee35420471f2a0b40f52f0499587"
    ),
    "runner_component": (
        "04f9ab4a62294e586b5a1c533e78ee5ee827ef7947cb91b3dbd23aa4fa89a560"
    ),
}


def _sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def review_regime_gated_selective_development_runner(root=None):
    root = Path(__file__).resolve().parents[1] if root is None else Path(root)
    paths = {
        "learning_core_component": root / "src" / "kraken_ai_driven_v2_learning_core.py",
        "spot_reader_component": root
        / "src"
        / "kraken_ai_driven_v2_12h_development_learning_runner.py",
        "bidirectional_runner_component": root
        / "src"
        / "kraken_ai_driven_v2_bidirectional_development_learning_runner.py",
        "context_dataset_component": root
        / "src"
        / "kraken_ai_driven_v2_derivatives_context_dataset.py",
        "context_hypothesis_component": root
        / "src"
        / "kraken_ai_driven_v2_derivatives_context_hypothesis.py",
        "regime_hypothesis_protocol": root
        / "KRAKEN_BTC_ETH_XRP_AI_DRIVEN_V2_REGIME_GATED_SELECTIVE_DEVELOPMENT_HYPOTHESIS_PROTOCOL_V1.md",
        "regime_hypothesis_component": root
        / "src"
        / "kraken_ai_driven_v2_regime_gated_selective_hypothesis.py",
        "regime_hypothesis_review": root
        / "src"
        / "kraken_ai_driven_v2_regime_gated_selective_hypothesis_review.py",
        "runner_protocol": root
        / "KRAKEN_BTC_ETH_XRP_AI_DRIVEN_V2_REGIME_GATED_SELECTIVE_DEVELOPMENT_RUNNER_PROTOCOL_V1.md",
        "runner_component": root
        / "src"
        / "kraken_ai_driven_v2_regime_gated_selective_development_runner.py",
    }
    observed = {name: _sha256(path) for name, path in paths.items()}
    for name, expected in EXPECTED_HASHES.items():
        if observed[name] != expected:
            raise RuntimeError(f"Regime-gated runner binding mismatch: {name}.")

    declaration = runner_declaration()
    if PARENT_COMMIT != EXPECTED_PARENT_COMMIT:
        raise RuntimeError("Regime-gated runner parent commit mismatch.")
    if DATASET_MANIFEST_SHA256 != EXPECTED_DATASET_MANIFEST_SHA256:
        raise RuntimeError("Regime-gated dataset manifest mismatch.")
    if declaration["protocol_id"] != PROTOCOL_ID:
        raise RuntimeError("Regime-gated runner protocol identity mismatch.")
    if declaration["component_id"] != COMPONENT_ID:
        raise RuntimeError("Regime-gated runner component identity mismatch.")
    if declaration["authorization_phrase"] != AUTHORIZATION_PHRASE:
        raise RuntimeError("Regime-gated authorization phrase mismatch.")
    if tuple(declaration["variant_order"]) != tuple(VARIANT_SPECS):
        raise RuntimeError("Regime-gated runner variant registry mismatch.")
    if tuple(declaration["direction_order"]) != tuple(DIRECTION_ORDER):
        raise RuntimeError("Regime-gated runner direction registry mismatch.")
    if declaration["matched_control"] != MATCHED_CONTROL:
        raise RuntimeError("Regime-gated runner matched control mismatch.")
    if declaration["maximum_base_model_fits"] != 12:
        raise RuntimeError("Regime-gated base fit budget mismatch.")
    if declaration["maximum_calibrator_fits"] != 12:
        raise RuntimeError("Regime-gated calibrator fit budget mismatch.")
    if declaration["maximum_total_fits"] != 24:
        raise RuntimeError("Regime-gated total fit budget mismatch.")
    if not TERMINAL_FAILURE_STATUS.endswith("STOP_KRAKEN_12H_RESEARCH"):
        raise RuntimeError("Regime-gated terminal stop mismatch.")

    required_true = (
        "strict_regime_filter_implemented",
        "directional_context_confirmation_implemented",
        "chronological_inner_calibration_implemented",
        "payoff_break_even_threshold_implemented",
        "brier_prevalence_skill_gate_implemented",
        "absolute_and_incremental_gates_implemented",
        "terminal_research_stop_implemented",
        "real_model_artifact_persistence_implemented",
        "out_of_fold_prediction_artifact_implemented",
        "canonical_binary_lf_sidecars_implemented",
        "one_shot_atomic_evidence_implemented",
        "independent_evidence_reader_implemented",
    )
    if any(declaration[field] is not True for field in required_true):
        raise RuntimeError("Regime-gated runner implementation boundary mismatch.")
    required_false = (
        "authorization_phrase_active",
        "network_download_authorized",
        "source_archive_opened",
        "context_dataset_opened",
        "development_data_opened",
        "labels_generated",
        "model_training_authorized",
        "model_training_executed",
        "feature_search_authorized",
        "hyperparameter_sweep_authorized",
        "threshold_sweep_authorized",
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
        raise RuntimeError("Regime-gated runner safety boundary mismatch.")

    return {
        **declaration,
        "schema_version": SCHEMA_VERSION,
        "status": STATUS,
        "source_sha256_matches": {
            name: observed[name] == EXPECTED_HASHES[name]
            for name in SOURCE_BINDING_SHA256
        },
        "runner_protocol_sha256": observed["runner_protocol"],
        "runner_protocol_sha256_match": True,
        "runner_component_sha256": observed["runner_component"],
        "runner_component_sha256_match": True,
        "model_training_executed": False,
        "next_stage": (
            "SEPARATE_OPERATOR_DECISION_FOR_ONE_SHOT_REGIME_GATED_SELECTIVE_"
            "DEVELOPMENT_RUN"
        ),
    }


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="Review the frozen regime-gated selective Development runner."
    )
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    args = parser.parse_args(argv)
    print(
        json.dumps(
            review_regime_gated_selective_development_runner(args.root),
            indent=2,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
