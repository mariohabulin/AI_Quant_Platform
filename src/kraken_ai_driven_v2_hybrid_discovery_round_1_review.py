"""Hash-bound nonexecuting review for Kraken V2 hybrid discovery Round 1."""

import argparse
import hashlib
import json
from pathlib import Path

try:
    from kraken_ai_driven_v2_hybrid_discovery_round_1 import (
        HYPOTHESIS_ORDER,
        PROTOCOL_ID,
        ROUND_ID,
        STATUS,
        round_1_declaration,
    )
    from kraken_ai_driven_v2_strategy_discovery_review import (
        REVIEW_STATUS as PARENT_REVIEW_STATUS,
        review_declaration as parent_review_declaration,
    )
except ImportError:  # pragma: no cover - package import compatibility
    from .kraken_ai_driven_v2_hybrid_discovery_round_1 import (
        HYPOTHESIS_ORDER,
        PROTOCOL_ID,
        ROUND_ID,
        STATUS,
        round_1_declaration,
    )
    from .kraken_ai_driven_v2_strategy_discovery_review import (
        REVIEW_STATUS as PARENT_REVIEW_STATUS,
        review_declaration as parent_review_declaration,
    )


SCHEMA_VERSION = 1
REVIEW_STATUS = (
    "KRAKEN_AI_V2_HYBRID_DISCOVERY_ROUND_1_REVIEWED_"
    "COMPONENT_IMPLEMENTATION_REQUIRED"
)
ROUND_1_PROTOCOL_NORMALIZED_SHA256 = (
    "ac886ea36e7938f651d369b5adf8586f29f075831f9e1b583a32c802a9626ce4"
)
ROUND_1_COMPONENT_NORMALIZED_SHA256 = (
    "ddc15b21ec69bc028eadc7720831cba326063122d91d9b4121424dcb07c1f0ce"
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
)
DEFAULT_ROUND_1_PROTOCOL_PATH = Path(
    "KRAKEN_BTC_ETH_XRP_AI_DRIVEN_V2_HYBRID_DISCOVERY_ROUND_1_PROTOCOL_V1.md"
)
DEFAULT_ROUND_1_COMPONENT_PATH = Path(
    "src/kraken_ai_driven_v2_hybrid_discovery_round_1.py"
)


def _normalized_text_bytes(path):
    try:
        text = Path(path).read_text(encoding="utf-8")
    except (OSError, UnicodeError) as exc:
        raise RuntimeError(
            f"Unable to read AI-driven v2 Round 1 review input: {path}"
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


def load_round_1_protocol(path=DEFAULT_ROUND_1_PROTOCOL_PATH):
    raw = _normalized_text_bytes(path)
    digest = hashlib.sha256(raw).hexdigest()
    if digest != ROUND_1_PROTOCOL_NORMALIZED_SHA256:
        raise RuntimeError(
            "AI-driven v2 Round 1 protocol SHA256 mismatch: "
            f"{digest} != {ROUND_1_PROTOCOL_NORMALIZED_SHA256}."
        )
    text = raw.decode("utf-8")
    required = (
        STATUS,
        PROTOCOL_ID,
        ROUND_ID,
        "four hypotheses",
        "eight closed trades",
        "five fixed development slices",
        "components implemented: `false`",
        "development data opened: `false`",
        "evaluation data opened: `false`",
        "Reference A",
        "Candidate v2",
    )
    if any(value not in text for value in required):
        raise RuntimeError(
            "AI-driven v2 Round 1 protocol required contract text is missing."
        )
    return text, digest


def _validate_parent_review(declaration):
    if declaration.get("status") != PARENT_REVIEW_STATUS:
        raise RuntimeError("Round 1 parent hybrid review status mismatch.")
    bindings = declaration.get("source_binding_matches")
    if not isinstance(bindings, dict) or not bindings or not all(bindings.values()):
        raise RuntimeError("Round 1 parent hybrid source binding mismatch.")
    for field in (
        "discovery_protocol_sha256_match",
        "discovery_component_sha256_match",
        "hybrid_routing_contract_implemented",
        "bounded_manifest_validator_implemented",
    ):
        if declaration.get(field) is not True:
            raise RuntimeError(f"Round 1 parent hybrid review mismatch for {field}.")
    for field in (
        "hypothesis_manifest_registered",
        "development_data_opened",
        "calibration_data_opened",
        "evaluation_data_opened",
        "performance_evaluation_executed",
        "candidate_v2_authorized",
        "live_execution_authorized",
    ):
        if declaration.get(field) is not False:
            raise RuntimeError(f"Round 1 parent hybrid safety mismatch for {field}.")


def review_declaration(
    parent_protocol_path=Path(COMPONENT_BINDINGS[0]["path"]),
    parent_component_path=Path(COMPONENT_BINDINGS[1]["path"]),
    parent_review_path=Path(COMPONENT_BINDINGS[2]["path"]),
    *,
    round_1_protocol_path=DEFAULT_ROUND_1_PROTOCOL_PATH,
    round_1_component_path=DEFAULT_ROUND_1_COMPONENT_PATH,
    parent_reviewer=None,
):
    paths = (parent_protocol_path, parent_component_path, parent_review_path)
    binding_matches = {}
    for binding, path in zip(COMPONENT_BINDINGS, paths):
        digest = _load_exact(path, binding["sha256"], binding["label"])
        binding_matches[binding["label"]] = digest == binding["sha256"]
    _, protocol_digest = load_round_1_protocol(round_1_protocol_path)
    component_digest = _load_exact(
        round_1_component_path,
        ROUND_1_COMPONENT_NORMALIZED_SHA256,
        "AI-driven v2 Round 1 component",
    )
    reviewer = parent_reviewer or parent_review_declaration
    if not callable(reviewer):
        raise TypeError("Round 1 parent reviewer must be callable.")
    parent_review = reviewer()
    _validate_parent_review(parent_review)
    declaration = round_1_declaration()
    return {
        "schema_version": SCHEMA_VERSION,
        "status": REVIEW_STATUS,
        "round_1_status": declaration["status"],
        "protocol_id": declaration["protocol_id"],
        "round_id": declaration["round_id"],
        "hypothesis_order": list(HYPOTHESIS_ORDER),
        "hypothesis_count": declaration["hypothesis_count"],
        "manifest_sha256": declaration["manifest_sha256"],
        "configuration_sha256": declaration["configuration_sha256"],
        "parent_source_binding_matches": binding_matches,
        "round_1_protocol_sha256_match": (
            protocol_digest == ROUND_1_PROTOCOL_NORMALIZED_SHA256
        ),
        "round_1_component_sha256_match": (
            component_digest == ROUND_1_COMPONENT_NORMALIZED_SHA256
        ),
        "parent_hybrid_review_passed": True,
        "hypothesis_manifest_registered": True,
        "configuration_lock_implemented": True,
        "route_interest_gates_frozen": True,
        "cost_profiles_frozen": True,
        "development_slices_frozen": True,
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
        "next_stage": "IMPLEMENT_ROUND_1_CAUSAL_COMPONENTS_SYNTHETIC_ONLY",
    }


def _parser():
    parser = argparse.ArgumentParser(
        description="Review nonexecuting Kraken V2 hybrid discovery Round 1."
    )
    for index, binding in enumerate(COMPONENT_BINDINGS):
        parser.add_argument(f"--binding-{index}", default=binding["path"])
    parser.add_argument(
        "--round-1-protocol", default=str(DEFAULT_ROUND_1_PROTOCOL_PATH)
    )
    parser.add_argument(
        "--round-1-component", default=str(DEFAULT_ROUND_1_COMPONENT_PATH)
    )
    return parser


def main(argv=None):
    args = _parser().parse_args(argv)
    binding_paths = [getattr(args, f"binding_{index}") for index in range(3)]
    declaration = review_declaration(
        *binding_paths,
        round_1_protocol_path=args.round_1_protocol,
        round_1_component_path=args.round_1_component,
    )
    print(json.dumps(declaration, indent=2, sort_keys=True))
    return declaration


if __name__ == "__main__":  # pragma: no cover
    main()
