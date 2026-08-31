"""Hash-bound nonexecuting review for Kraken V2 Round 2 causal signals."""

import argparse
import hashlib
import json
from pathlib import Path

try:
    from kraken_ai_driven_v2_hybrid_discovery_round_2 import (
        HYPOTHESIS_ORDER,
        ROUND_2_CONFIGURATION_LOCK,
    )
    from kraken_ai_driven_v2_hybrid_discovery_round_2_review import (
        REVIEW_STATUS as PARENT_REVIEW_STATUS,
        review_declaration as parent_review_declaration,
    )
    from kraken_ai_driven_v2_round_2_causal_signals import (
        FAMILY_ORDER,
        FEATURE_COMPONENT_ID,
        SIGNAL_COMPONENT_ID,
        KrakenAIDrivenV2Round2CausalFeatureEngine,
        KrakenAIDrivenV2Round2SignalEngine,
    )
except ImportError:  # pragma: no cover - package import compatibility
    from .kraken_ai_driven_v2_hybrid_discovery_round_2 import (
        HYPOTHESIS_ORDER,
        ROUND_2_CONFIGURATION_LOCK,
    )
    from .kraken_ai_driven_v2_hybrid_discovery_round_2_review import (
        REVIEW_STATUS as PARENT_REVIEW_STATUS,
        review_declaration as parent_review_declaration,
    )
    from .kraken_ai_driven_v2_round_2_causal_signals import (
        FAMILY_ORDER,
        FEATURE_COMPONENT_ID,
        SIGNAL_COMPONENT_ID,
        KrakenAIDrivenV2Round2CausalFeatureEngine,
        KrakenAIDrivenV2Round2SignalEngine,
    )


SCHEMA_VERSION = 1
REVIEW_STATUS = (
    "KRAKEN_AI_V2_ROUND_2_CAUSAL_SIGNALS_REVIEWED_"
    "EXECUTION_COMPONENTS_REQUIRED"
)
SIGNAL_PROTOCOL_NORMALIZED_SHA256 = (
    "b3ff8ff40272d4a0af0ec15f598dd127461af9f3f206de2095e39d46dcad2c6f"
)
SIGNAL_COMPONENT_NORMALIZED_SHA256 = (
    "80cc6512bdcca299424a2d86c509121286ad45ccec63d70d9e2aa5df96e0e63e"
)
COMPONENT_BINDINGS = (
    {
        "label": "AI-driven v2 Round 2 protocol",
        "path": (
            "KRAKEN_BTC_ETH_XRP_AI_DRIVEN_V2_"
            "HYBRID_DISCOVERY_ROUND_2_PROTOCOL_V1.md"
        ),
        "sha256": "d0d241d2891ce3d975a26049a9fc5b37d53f2175355695f7e47c60656a3d9c1b",
    },
    {
        "label": "AI-driven v2 Round 2 component",
        "path": "src/kraken_ai_driven_v2_hybrid_discovery_round_2.py",
        "sha256": "c6fc41bbddc31c64430996069e36ee17b75e8999e34c69547484ca082f7182ac",
    },
    {
        "label": "AI-driven v2 Round 2 review",
        "path": "src/kraken_ai_driven_v2_hybrid_discovery_round_2_review.py",
        "sha256": "1f3c410ad582ac9175016c849b51666a569ebf2a02190207f41c9b67d3969794",
    },
)
DEFAULT_SIGNAL_PROTOCOL_PATH = Path(
    "KRAKEN_BTC_ETH_XRP_AI_DRIVEN_V2_ROUND_2_CAUSAL_SIGNALS_PROTOCOL_V1.md"
)
DEFAULT_SIGNAL_COMPONENT_PATH = Path(
    "src/kraken_ai_driven_v2_round_2_causal_signals.py"
)


def _normalized_text_bytes(path):
    try:
        text = Path(path).read_text(encoding="utf-8")
    except (OSError, UnicodeError) as exc:
        raise RuntimeError(
            f"Unable to read AI-driven v2 Round 2 causal signal input: {path}"
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


def load_signal_protocol(path=DEFAULT_SIGNAL_PROTOCOL_PATH):
    raw = _normalized_text_bytes(path)
    digest = hashlib.sha256(raw).hexdigest()
    if digest != SIGNAL_PROTOCOL_NORMALIZED_SHA256:
        raise RuntimeError(
            "AI-driven v2 Round 2 causal signals protocol SHA256 mismatch: "
            f"{digest} != {SIGNAL_PROTOCOL_NORMALIZED_SHA256}."
        )
    text = raw.decode("utf-8")
    required = (
        "three exact",
        "At least two completed post-setup bars",
        "rolling baseline current bar included is `false`",
        "Round 2 execution components implemented: `false`",
        "Development data opened: `false`",
        "3ce14fda95f657c0b671b74c702d55ec4102da303e9e033ebaf0e02ff5c2fa9b",
        "Candidate v2",
        "IMPLEMENT_ROUND_2_FAMILY_EXECUTION_COMPONENTS_SYNTHETIC_ONLY",
    )
    if any(value not in text for value in required):
        raise RuntimeError(
            "AI-driven v2 Round 2 causal signals required contract text is missing."
        )
    return text, digest


def _validate_parent_review(declaration):
    if declaration.get("status") != PARENT_REVIEW_STATUS:
        raise RuntimeError("Round 2 causal signals parent review status mismatch.")
    bindings = declaration.get("parent_source_binding_matches")
    if not isinstance(bindings, dict) or not bindings or not all(bindings.values()):
        raise RuntimeError("Round 2 causal signals parent source binding mismatch.")
    for field in (
        "round_2_protocol_sha256_match",
        "round_2_component_sha256_match",
        "round_1_closure_review_passed",
        "remaining_discovery_budget_verified",
        "route_dispositions_frozen",
        "round_2_manifest_registered",
    ):
        if declaration.get(field) is not True:
            raise RuntimeError(
                f"Round 2 causal signals parent review mismatch for {field}."
            )
    for field in (
        "round_1_rerun_authorized",
        "round_1_gates_weakened",
        "cost_profiles_changed",
        "development_slices_changed",
        "regime_components_implemented",
        "signal_components_implemented",
        "execution_components_implemented",
        "discovery_runner_implemented",
        "development_data_opened",
        "calibration_data_opened",
        "evaluation_data_opened",
        "performance_evaluation_executed",
        "candidate_v2_authorized",
        "live_execution_authorized",
    ):
        if declaration.get(field) is not False:
            raise RuntimeError(
                f"Round 2 causal signals parent safety mismatch for {field}."
            )


def review_declaration(
    parent_protocol_path=Path(COMPONENT_BINDINGS[0]["path"]),
    parent_component_path=Path(COMPONENT_BINDINGS[1]["path"]),
    parent_review_path=Path(COMPONENT_BINDINGS[2]["path"]),
    *,
    signal_protocol_path=DEFAULT_SIGNAL_PROTOCOL_PATH,
    signal_component_path=DEFAULT_SIGNAL_COMPONENT_PATH,
    parent_reviewer=None,
):
    paths = (parent_protocol_path, parent_component_path, parent_review_path)
    binding_matches = {}
    for binding, path in zip(COMPONENT_BINDINGS, paths):
        digest = _load_exact(path, binding["sha256"], binding["label"])
        binding_matches[binding["label"]] = digest == binding["sha256"]
    _, protocol_digest = load_signal_protocol(signal_protocol_path)
    component_digest = _load_exact(
        signal_component_path,
        SIGNAL_COMPONENT_NORMALIZED_SHA256,
        "AI-driven v2 Round 2 causal signals component",
    )

    reviewer = parent_reviewer or parent_review_declaration
    if not callable(reviewer):
        raise TypeError("Round 2 causal signals parent reviewer must be callable.")
    parent_review = reviewer()
    _validate_parent_review(parent_review)

    feature_configuration = (
        KrakenAIDrivenV2Round2CausalFeatureEngine().configuration()
    )
    signal_configuration = KrakenAIDrivenV2Round2SignalEngine().configuration()
    expected_lock = ROUND_2_CONFIGURATION_LOCK.sha256
    if feature_configuration["round_2_configuration_sha256"] != expected_lock:
        raise RuntimeError("Round 2 causal feature configuration lock mismatch.")
    if signal_configuration["round_2_configuration_sha256"] != expected_lock:
        raise RuntimeError("Round 2 causal signal configuration lock mismatch.")
    if tuple(signal_configuration["family_order"]) != FAMILY_ORDER:
        raise RuntimeError("Round 2 causal signal family order mismatch.")

    return {
        "schema_version": SCHEMA_VERSION,
        "status": REVIEW_STATUS,
        "round_2_configuration_sha256": expected_lock,
        "hypothesis_order": list(HYPOTHESIS_ORDER),
        "family_order": list(FAMILY_ORDER),
        "family_count": len(FAMILY_ORDER),
        "feature_component_id": FEATURE_COMPONENT_ID,
        "signal_component_id": SIGNAL_COMPONENT_ID,
        "parent_source_binding_matches": binding_matches,
        "signal_protocol_sha256_match": (
            protocol_digest == SIGNAL_PROTOCOL_NORMALIZED_SHA256
        ),
        "signal_component_sha256_match": (
            component_digest == SIGNAL_COMPONENT_NORMALIZED_SHA256
        ),
        "parent_round_2_review_passed": True,
        "feature_component_implemented": True,
        "regime_components_implemented": True,
        "signal_components_implemented": True,
        "family_execution_intent": "ENTER_NEXT_OPEN",
        "position_state_implemented": False,
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
        "next_stage": (
            "IMPLEMENT_ROUND_2_FAMILY_EXECUTION_COMPONENTS_SYNTHETIC_ONLY"
        ),
    }


def _parser():
    parser = argparse.ArgumentParser(
        description="Review nonexecuting Kraken V2 Round 2 causal signals."
    )
    for index, binding in enumerate(COMPONENT_BINDINGS):
        parser.add_argument(f"--binding-{index}", default=binding["path"])
    parser.add_argument(
        "--signal-protocol", default=str(DEFAULT_SIGNAL_PROTOCOL_PATH)
    )
    parser.add_argument(
        "--signal-component", default=str(DEFAULT_SIGNAL_COMPONENT_PATH)
    )
    return parser


def main(argv=None):
    args = _parser().parse_args(argv)
    binding_paths = [getattr(args, f"binding_{index}") for index in range(3)]
    declaration = review_declaration(
        *binding_paths,
        signal_protocol_path=args.signal_protocol,
        signal_component_path=args.signal_component,
    )
    print(json.dumps(declaration, indent=2, sort_keys=True))
    return declaration


if __name__ == "__main__":  # pragma: no cover
    main()
