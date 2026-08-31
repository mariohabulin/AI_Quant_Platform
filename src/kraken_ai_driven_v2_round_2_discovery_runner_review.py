"""Hash-bound nonexecuting review for the Round 2 discovery runner."""

import argparse
import hashlib
import json
from pathlib import Path

try:
    from kraken_ai_driven_v2_round_2_family_execution_review import (
        REVIEW_STATUS as PARENT_REVIEW_STATUS,
        review_declaration as parent_review_declaration,
    )
    from kraken_ai_driven_v2_round_2_discovery_runner import (
        AUTHORIZATION_PHRASE,
        COST_PROFILE_ORDER,
        DISCOVERY_RUNNER_PROTOCOL_ID,
        ROUTE_ORDER,
        KrakenAIDrivenV2Round2DiscoveryEvidenceLock,
        runner_declaration,
    )
except ImportError:  # pragma: no cover - package import compatibility
    from .kraken_ai_driven_v2_round_2_family_execution_review import (
        REVIEW_STATUS as PARENT_REVIEW_STATUS,
        review_declaration as parent_review_declaration,
    )
    from .kraken_ai_driven_v2_round_2_discovery_runner import (
        AUTHORIZATION_PHRASE,
        COST_PROFILE_ORDER,
        DISCOVERY_RUNNER_PROTOCOL_ID,
        ROUTE_ORDER,
        KrakenAIDrivenV2Round2DiscoveryEvidenceLock,
        runner_declaration,
    )


SCHEMA_VERSION = 1
REVIEW_STATUS = (
    "KRAKEN_AI_V2_ROUND_2_DISCOVERY_RUNNER_REVIEWED_"
    "EXECUTION_AUTHORIZATION_REQUIRED"
)
RUNNER_PROTOCOL_NORMALIZED_SHA256 = (
    "11cf6181923578379fc10e7fa7d89a210a25b2cbd73cd3cd3fb0c99f274e2aae"
)
RUNNER_COMPONENT_NORMALIZED_SHA256 = (
    "1d6dc71b1d896c04e798ed2e8e9aabf45fafd2050b8654d0683d4381018c9252"
)
COMPONENT_BINDINGS = (
    {
        "label": "AI-driven v2 Round 2 family execution protocol",
        "path": "KRAKEN_BTC_ETH_XRP_AI_DRIVEN_V2_ROUND_2_FAMILY_EXECUTION_PROTOCOL_V1.md",
        "sha256": "74b2fa5258258005a2c7ea2393d5fbd68fadf06c143a3a5b2d795d0f1fb446e9",
    },
    {
        "label": "AI-driven v2 Round 2 family execution component",
        "path": "src/kraken_ai_driven_v2_round_2_family_execution.py",
        "sha256": "dc9b38a5819d570c8ff0405e19b10405f0516cc858bbaa9fb6a08df693733d7b",
    },
    {
        "label": "AI-driven v2 Round 2 family execution review",
        "path": "src/kraken_ai_driven_v2_round_2_family_execution_review.py",
        "sha256": "e2b6a32a19fb671ec0f666a781b5e152366abecb9a0b557c5c71128d67c7d00c",
    },
)
DEFAULT_RUNNER_PROTOCOL_PATH = Path(
    "KRAKEN_BTC_ETH_XRP_AI_DRIVEN_V2_ROUND_2_DISCOVERY_RUNNER_PROTOCOL_V1.md"
)
DEFAULT_RUNNER_COMPONENT_PATH = Path(
    "src/kraken_ai_driven_v2_round_2_discovery_runner.py"
)


def _normalized_text_bytes(path):
    try:
        text = Path(path).read_text(encoding="utf-8")
    except (OSError, UnicodeError) as exc:
        raise RuntimeError(f"Unable to read AI-driven v2 Round 2 discovery input: {path}") from exc
    return text.replace("\r\n", "\n").replace("\r", "\n").encode("utf-8")


def normalized_text_sha256(path):
    return hashlib.sha256(_normalized_text_bytes(path)).hexdigest()


def _load_exact(path, expected_sha256, label):
    digest = normalized_text_sha256(path)
    if digest != expected_sha256:
        raise RuntimeError(f"{label} SHA256 mismatch: {digest} != {expected_sha256}.")
    return digest


def load_runner_protocol(path=DEFAULT_RUNNER_PROTOCOL_PATH):
    raw = _normalized_text_bytes(path)
    digest = hashlib.sha256(raw).hexdigest()
    if digest != RUNNER_PROTOCOL_NORMALIZED_SHA256:
        raise RuntimeError(
            "AI-driven v2 Round 2 discovery runner protocol SHA256 mismatch: "
            f"{digest} != {RUNNER_PROTOCOL_NORMALIZED_SHA256}."
        )
    text = raw.decode("utf-8")
    required = (
        "seven pre-registered Round 2 asset-family routes",
        "independent USD 5,000 research ledger",
        "A no-trade slice does not count as nonnegative",
        "Synthetic terminal force-close is prohibited",
        "development data opened: `false`",
        "development run authorized: `false`",
        "Reference A",
        "Candidate v2",
    )
    if any(value not in text for value in required):
        raise RuntimeError("Round 2 discovery runner required contract text is missing.")
    return text, digest


def _validate_parent_review(declaration):
    if declaration.get("status") != PARENT_REVIEW_STATUS:
        raise RuntimeError("Round 2 discovery parent review mismatch.")
    bindings = declaration.get("parent_source_binding_matches")
    if not isinstance(bindings, dict) or not bindings or not all(bindings.values()):
        raise RuntimeError("Round 2 discovery parent binding mismatch.")
    for field in (
        "family_execution_components_implemented",
        "baseline_cost_profile_implemented",
        "stress_cost_profile_implemented",
        "shared_safety_envelope_implemented",
        "protective_execution_implemented",
    ):
        if declaration.get(field) is not True:
            raise RuntimeError(f"Round 2 discovery parent mismatch for {field}.")
    for field in (
        "discovery_runner_implemented",
        "dataset_opened",
        "development_data_opened",
        "calibration_data_opened",
        "evaluation_data_opened",
        "performance_evaluation_executed",
        "candidate_v2_authorized",
        "real_orders_submitted",
        "live_execution_authorized",
    ):
        if declaration.get(field) is not False:
            raise RuntimeError(f"Round 2 discovery parent safety mismatch for {field}.")


def review_declaration(
    parent_protocol_path=Path(COMPONENT_BINDINGS[0]["path"]),
    parent_component_path=Path(COMPONENT_BINDINGS[1]["path"]),
    parent_review_path=Path(COMPONENT_BINDINGS[2]["path"]),
    *,
    runner_protocol_path=DEFAULT_RUNNER_PROTOCOL_PATH,
    runner_component_path=DEFAULT_RUNNER_COMPONENT_PATH,
    parent_reviewer=None,
):
    paths = (parent_protocol_path, parent_component_path, parent_review_path)
    binding_matches = {}
    for binding, path in zip(COMPONENT_BINDINGS, paths):
        digest = _load_exact(path, binding["sha256"], binding["label"])
        binding_matches[binding["label"]] = digest == binding["sha256"]
    _, protocol_digest = load_runner_protocol(runner_protocol_path)
    component_digest = _load_exact(
        runner_component_path,
        RUNNER_COMPONENT_NORMALIZED_SHA256,
        "AI-driven v2 Round 2 discovery runner component",
    )
    reviewer = parent_reviewer or parent_review_declaration
    if not callable(reviewer):
        raise TypeError("Round 2 discovery parent reviewer must be callable.")
    _validate_parent_review(reviewer())

    component = runner_declaration()
    if component.get("discovery_runner_protocol_id") != DISCOVERY_RUNNER_PROTOCOL_ID:
        raise RuntimeError("Round 2 discovery runner protocol ID mismatch.")
    if component.get("route_order") != list(ROUTE_ORDER):
        raise RuntimeError("Round 2 discovery route order mismatch.")
    if component.get("cost_profile_ids") != list(COST_PROFILE_ORDER):
        raise RuntimeError("Round 2 discovery cost-profile order mismatch.")
    if not isinstance(KrakenAIDrivenV2Round2DiscoveryEvidenceLock(), KrakenAIDrivenV2Round2DiscoveryEvidenceLock):
        raise RuntimeError("Round 2 discovery evidence lock is unavailable.")
    for field in (
        "development_only_reader_reused",
        "independent_evidence_lock_implemented",
        "one_shot_atomic_evidence_implemented",
        "absolute_route_gates_implemented",
        "round_interest_gate_implemented",
        "discovery_runner_implemented",
    ):
        if component.get(field) is not True:
            raise RuntimeError(f"Round 2 discovery runner mismatch for {field}.")
    for field in (
        "dataset_opened",
        "development_data_opened",
        "calibration_data_opened",
        "evaluation_data_opened",
        "development_run_authorized",
        "development_run_executed",
        "performance_evaluation_executed",
        "parameter_sweep_executed",
        "automatic_ranking_generated",
        "automatic_strategy_selection",
        "candidate_v2_authorized",
        "real_orders_submitted",
        "live_execution_authorized",
    ):
        if component.get(field) is not False:
            raise RuntimeError(f"Round 2 discovery runner safety mismatch for {field}.")

    return {
        "schema_version": SCHEMA_VERSION,
        "status": REVIEW_STATUS,
        "discovery_runner_protocol_id": DISCOVERY_RUNNER_PROTOCOL_ID,
        "round_2_configuration_sha256": component["round_2_configuration_sha256"],
        "authorization_phrase": AUTHORIZATION_PHRASE,
        "authorization_phrase_active": False,
        "route_count": len(ROUTE_ORDER),
        "route_order": list(ROUTE_ORDER),
        "cost_profile_ids": list(COST_PROFILE_ORDER),
        "parent_source_binding_matches": binding_matches,
        "runner_protocol_sha256_match": protocol_digest == RUNNER_PROTOCOL_NORMALIZED_SHA256,
        "runner_component_sha256_match": component_digest == RUNNER_COMPONENT_NORMALIZED_SHA256,
        "parent_family_execution_review_passed": True,
        "development_only_reader_reused": True,
        "independent_evidence_lock_implemented": True,
        "one_shot_atomic_evidence_implemented": True,
        "absolute_route_gates_implemented": True,
        "round_interest_gate_implemented": True,
        "discovery_runner_implemented": True,
        "dataset_opened": False,
        "development_data_opened": False,
        "calibration_data_opened": False,
        "evaluation_data_opened": False,
        "development_run_authorized": False,
        "development_run_executed": False,
        "performance_evaluation_executed": False,
        "parameter_sweep_executed": False,
        "automatic_ranking_generated": False,
        "automatic_strategy_selection": False,
        "runtime_learning_authorized": False,
        "calibration_authorized": False,
        "evaluation_authorized": False,
        "candidate_v2_authorized": False,
        "bounded_forward_paper_authorized": False,
        "cloud_execution_authorized": False,
        "real_orders_submitted": False,
        "live_execution_authorized": False,
        "next_stage": "SEPARATE_OPERATOR_DECISION_FOR_ONE_SHOT_ROUND_2_DEVELOPMENT_DISCOVERY_RUN",
    }


def _parser():
    parser = argparse.ArgumentParser(description="Review nonexecuting Kraken V2 Round 2 discovery runner.")
    for index, binding in enumerate(COMPONENT_BINDINGS):
        parser.add_argument(f"--binding-{index}", default=binding["path"])
    parser.add_argument("--runner-protocol", default=str(DEFAULT_RUNNER_PROTOCOL_PATH))
    parser.add_argument("--runner-component", default=str(DEFAULT_RUNNER_COMPONENT_PATH))
    return parser


def main(argv=None):
    args = _parser().parse_args(argv)
    binding_paths = [getattr(args, f"binding_{index}") for index in range(3)]
    declaration = review_declaration(
        *binding_paths,
        runner_protocol_path=args.runner_protocol,
        runner_component_path=args.runner_component,
    )
    print(json.dumps(declaration, indent=2, sort_keys=True))
    return declaration


if __name__ == "__main__":  # pragma: no cover
    main()
