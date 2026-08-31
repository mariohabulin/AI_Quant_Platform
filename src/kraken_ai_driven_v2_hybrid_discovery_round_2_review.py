"""Hash-bound nonexecuting review for Kraken V2 hybrid discovery Round 2."""

import argparse
import hashlib
import json
from pathlib import Path

try:
    from kraken_ai_driven_v2_hybrid_discovery_round_2 import (
        HYPOTHESIS_ORDER,
        PROTOCOL_ID,
        ROUND_ID,
        STATUS,
        round_2_declaration,
    )
    from kraken_ai_driven_v2_round_1_closure_review import (
        REVIEW_STATUS as PARENT_REVIEW_STATUS,
        review_declaration as parent_review_declaration,
    )
except ImportError:  # pragma: no cover - package import compatibility
    from .kraken_ai_driven_v2_hybrid_discovery_round_2 import (
        HYPOTHESIS_ORDER,
        PROTOCOL_ID,
        ROUND_ID,
        STATUS,
        round_2_declaration,
    )
    from .kraken_ai_driven_v2_round_1_closure_review import (
        REVIEW_STATUS as PARENT_REVIEW_STATUS,
        review_declaration as parent_review_declaration,
    )


SCHEMA_VERSION = 1
REVIEW_STATUS = (
    "KRAKEN_AI_V2_HYBRID_DISCOVERY_ROUND_2_REVIEWED_"
    "COMPONENT_IMPLEMENTATION_REQUIRED"
)
ROUND_2_PROTOCOL_NORMALIZED_SHA256 = (
    "d0d241d2891ce3d975a26049a9fc5b37d53f2175355695f7e47c60656a3d9c1b"
)
ROUND_2_COMPONENT_NORMALIZED_SHA256 = (
    "c6fc41bbddc31c64430996069e36ee17b75e8999e34c69547484ca082f7182ac"
)
COMPONENT_BINDINGS = (
    {
        "label": "AI-driven v2 hybrid discovery protocol",
        "path": (
            "KRAKEN_BTC_ETH_XRP_AI_DRIVEN_V2_"
            "STRATEGY_DISCOVERY_LEARNING_PROTOCOL_V1.md"
        ),
        "sha256": "66e3148924965ecbc32954c76eb122ee6f74f7454ae88a4e8ddf7a28cf8d54cb",
    },
    {
        "label": "AI-driven v2 hybrid discovery component",
        "path": "src/kraken_ai_driven_v2_strategy_discovery.py",
        "sha256": "846fb4d1e096e1ff2d79f579ab0c603a03bbdc527e7492ec20e2c7dfc37b85f6",
    },
    {
        "label": "AI-driven v2 hybrid discovery review",
        "path": "src/kraken_ai_driven_v2_strategy_discovery_review.py",
        "sha256": "93e53676f152efbc9f9f4b0ee1ef04d34ee80a6ba9b1083383ee00234b8d6a1a",
    },
    {
        "label": "AI-driven v2 Round 1 protocol",
        "path": (
            "KRAKEN_BTC_ETH_XRP_AI_DRIVEN_V2_"
            "HYBRID_DISCOVERY_ROUND_1_PROTOCOL_V1.md"
        ),
        "sha256": "ac886ea36e7938f651d369b5adf8586f29f075831f9e1b583a32c802a9626ce4",
    },
    {
        "label": "AI-driven v2 Round 1 component",
        "path": "src/kraken_ai_driven_v2_hybrid_discovery_round_1.py",
        "sha256": "ddc15b21ec69bc028eadc7720831cba326063122d91d9b4121424dcb07c1f0ce",
    },
    {
        "label": "AI-driven v2 Round 1 closure document",
        "path": "KRAKEN_AI_DRIVEN_V2_ROUND_1_CLOSURE.md",
        "sha256": "7e10a8ee49174ffb8d278231ca4561046ea0e6312a7a5252d1587ff238162f84",
    },
    {
        "label": "AI-driven v2 Round 1 closure component",
        "path": "src/kraken_ai_driven_v2_round_1_closure.py",
        "sha256": "dd6b74c01727d5127c311fe7cb272a02471107cb65eec1dfa818b5814c22ba87",
    },
    {
        "label": "AI-driven v2 Round 1 closure review",
        "path": "src/kraken_ai_driven_v2_round_1_closure_review.py",
        "sha256": "dda243cdba5ca594008b89f1c18b6682659328776a322a28254966d85b7289a6",
    },
)
DEFAULT_ROUND_2_PROTOCOL_PATH = Path(
    "KRAKEN_BTC_ETH_XRP_AI_DRIVEN_V2_HYBRID_DISCOVERY_ROUND_2_PROTOCOL_V1.md"
)
DEFAULT_ROUND_2_COMPONENT_PATH = Path(
    "src/kraken_ai_driven_v2_hybrid_discovery_round_2.py"
)


def _normalized_text_bytes(path):
    try:
        text = Path(path).read_text(encoding="utf-8")
    except (OSError, UnicodeError) as exc:
        raise RuntimeError(
            f"Unable to read AI-driven v2 Round 2 review input: {path}"
        ) from exc
    return text.replace("\r\n", "\n").replace("\r", "\n").encode("utf-8")


def normalized_text_sha256(path):
    return hashlib.sha256(_normalized_text_bytes(path)).hexdigest()


def _load_exact(path, expected_sha256, label):
    digest = normalized_text_sha256(path)
    if digest != expected_sha256:
        raise RuntimeError(
            f"{label} SHA256 mismatch: {digest} != {expected_sha256}."
        )
    return digest


def load_round_2_protocol(path=DEFAULT_ROUND_2_PROTOCOL_PATH):
    raw = _normalized_text_bytes(path)
    digest = hashlib.sha256(raw).hexdigest()
    if digest != ROUND_2_PROTOCOL_NORMALIZED_SHA256:
        raise RuntimeError(
            "AI-driven v2 Round 2 protocol SHA256 mismatch: "
            f"{digest} != {ROUND_2_PROTOCOL_NORMALIZED_SHA256}."
        )
    text = raw.decode("utf-8")
    required = (
        STATUS,
        PROTOCOL_ID,
        ROUND_ID,
        "three new hypotheses",
        "seven of the maximum twelve",
        "Round 1 rerun authorization",
        "Development data opened: `false`",
        "Evaluation data opened: `false`",
        "Candidate v2",
        "IMPLEMENT_ROUND_2_CAUSAL_COMPONENTS_SYNTHETIC_ONLY",
    )
    if any(value not in text for value in required):
        raise RuntimeError(
            "AI-driven v2 Round 2 protocol required contract text is missing."
        )
    return text, digest


def _validate_parent_review(declaration):
    if declaration.get("status") != PARENT_REVIEW_STATUS:
        raise RuntimeError("Round 2 parent closure review status mismatch.")
    bindings = declaration.get("parent_source_binding_matches")
    if not isinstance(bindings, dict) or not bindings or not all(bindings.values()):
        raise RuntimeError("Round 2 parent closure source binding mismatch.")
    for field in (
        "closure_component_sha256_match",
        "closure_document_sha256_match",
        "parent_discovery_runner_review_passed",
        "round_1_closure_implemented",
        "offline_feedback_attribution_implemented",
        "external_evidence_required_for_closure",
    ):
        if declaration.get(field) is not True:
            raise RuntimeError(f"Round 2 parent closure review mismatch for {field}.")
    for field in (
        "round_1_closed",
        "round_1_rerun_authorized",
        "round_2_manifest_registered",
        "development_data_opened",
        "calibration_data_opened",
        "evaluation_data_opened",
        "automatic_ranking_generated",
        "candidate_v2_authorized",
        "live_execution_authorized",
    ):
        if declaration.get(field) is not False:
            raise RuntimeError(f"Round 2 parent closure safety mismatch for {field}.")


def review_declaration(
    *binding_paths,
    round_2_protocol_path=DEFAULT_ROUND_2_PROTOCOL_PATH,
    round_2_component_path=DEFAULT_ROUND_2_COMPONENT_PATH,
    parent_reviewer=None,
):
    if not binding_paths:
        binding_paths = tuple(Path(item["path"]) for item in COMPONENT_BINDINGS)
    if len(binding_paths) != len(COMPONENT_BINDINGS):
        raise ValueError("Round 2 review binding path count mismatch.")

    binding_matches = {}
    for binding, path in zip(COMPONENT_BINDINGS, binding_paths):
        digest = _load_exact(path, binding["sha256"], binding["label"])
        binding_matches[binding["label"]] = digest == binding["sha256"]

    _, protocol_digest = load_round_2_protocol(round_2_protocol_path)
    component_digest = _load_exact(
        round_2_component_path,
        ROUND_2_COMPONENT_NORMALIZED_SHA256,
        "AI-driven v2 Round 2 component",
    )
    reviewer = parent_reviewer or parent_review_declaration
    if not callable(reviewer):
        raise TypeError("Round 2 parent reviewer must be callable.")
    parent_review = reviewer()
    _validate_parent_review(parent_review)

    declaration = round_2_declaration()
    return {
        "schema_version": SCHEMA_VERSION,
        "status": REVIEW_STATUS,
        "round_2_status": declaration["status"],
        "protocol_id": declaration["protocol_id"],
        "round_id": declaration["round_id"],
        "hypothesis_order": list(HYPOTHESIS_ORDER),
        "hypothesis_count": declaration["hypothesis_count"],
        "asset_route_counts": declaration["asset_route_counts"],
        "manifest_sha256": declaration["manifest_sha256"],
        "configuration_sha256": declaration["configuration_sha256"],
        "round_1_report_sha256": declaration["round_1_report_sha256"],
        "cumulative_hypothesis_count": declaration[
            "cumulative_hypothesis_count"
        ],
        "rounds_registered_under_protocol": declaration[
            "rounds_registered_under_protocol"
        ],
        "parent_source_binding_matches": binding_matches,
        "round_2_protocol_sha256_match": (
            protocol_digest == ROUND_2_PROTOCOL_NORMALIZED_SHA256
        ),
        "round_2_component_sha256_match": (
            component_digest == ROUND_2_COMPONENT_NORMALIZED_SHA256
        ),
        "round_1_closure_review_passed": True,
        "remaining_discovery_budget_verified": True,
        "route_dispositions_frozen": True,
        "round_1_gates_weakened": declaration["round_1_gates_weakened"],
        "cost_profiles_changed": declaration["cost_profiles_changed"],
        "development_slices_changed": declaration[
            "development_slices_changed"
        ],
        "round_1_closed": True,
        "round_1_rerun_authorized": False,
        "round_2_manifest_registered": True,
        "regime_components_implemented": False,
        "signal_components_implemented": False,
        "execution_components_implemented": False,
        "discovery_runner_implemented": False,
        "dataset_opened": False,
        "development_data_opened": False,
        "calibration_data_opened": False,
        "evaluation_data_opened": False,
        "development_run_authorized": False,
        "performance_evaluation_executed": False,
        "parameter_sweep_authorized": False,
        "automatic_ranking_authorized": False,
        "automatic_strategy_selection_authorized": False,
        "runtime_learning_authorized": False,
        "calibration_authorized": False,
        "evaluation_authorized": False,
        "candidate_v2_authorized": False,
        "bounded_forward_paper_authorized": False,
        "cloud_execution_authorized": False,
        "live_execution_authorized": False,
        "next_stage": "IMPLEMENT_ROUND_2_CAUSAL_COMPONENTS_SYNTHETIC_ONLY",
    }


def _parser():
    parser = argparse.ArgumentParser(
        description="Review nonexecuting Kraken V2 hybrid discovery Round 2."
    )
    for index, binding in enumerate(COMPONENT_BINDINGS):
        parser.add_argument(f"--binding-{index}", default=binding["path"])
    parser.add_argument(
        "--round-2-protocol", default=str(DEFAULT_ROUND_2_PROTOCOL_PATH)
    )
    parser.add_argument(
        "--round-2-component", default=str(DEFAULT_ROUND_2_COMPONENT_PATH)
    )
    return parser


def main(argv=None):
    args = _parser().parse_args(argv)
    binding_paths = [getattr(args, f"binding_{index}") for index in range(8)]
    declaration = review_declaration(
        *binding_paths,
        round_2_protocol_path=args.round_2_protocol,
        round_2_component_path=args.round_2_component,
    )
    print(json.dumps(declaration, indent=2, sort_keys=True))
    return declaration


if __name__ == "__main__":  # pragma: no cover
    main()
