"""Explicitly authorized, one-episode-at-a-time Kraken blinded replay."""

import argparse
import hashlib
import json
from dataclasses import dataclass
from pathlib import Path

try:
    from blinded_daily_replay import ALLOWED_ACTIONS, BlindedDailyReplaySession
    from blinded_replay_evidence import (
        BlindedReplayEvidenceLock,
        DurableBlindedReplayJournal,
    )
    from kraken_blinded_replay_review import (
        CONTEXT_BARS,
        DATASET_ID,
        DATASET_LOCK_EVIDENCE_NORMALIZED_SHA256,
        DATASET_MANIFEST_SHA256,
        DECISION_BARS,
        EPISODE_ROWS,
        EVIDENCE_COMPONENT_NORMALIZED_SHA256,
        REPLAY_COMPONENT_NORMALIZED_SHA256,
        REVIEW_PROTOCOL_ID,
        REVIEW_PROTOCOL_NORMALIZED_SHA256,
        KrakenBlindedReplayPreflight,
        _candidate_inventory,
        _rows_to_frame,
        _selected_candidate,
        load_dataset_lock_evidence,
        load_replay_review_protocol,
        load_reviewed_component,
    )
    from kraken_daily_dataset import ASSET_ORDER, KrakenDailyDatasetLock
    from research_evidence import canonical_json_bytes
except ImportError:  # pragma: no cover - package import compatibility
    from .blinded_daily_replay import ALLOWED_ACTIONS, BlindedDailyReplaySession
    from .blinded_replay_evidence import (
        BlindedReplayEvidenceLock,
        DurableBlindedReplayJournal,
    )
    from .kraken_blinded_replay_review import (
        CONTEXT_BARS,
        DATASET_ID,
        DATASET_LOCK_EVIDENCE_NORMALIZED_SHA256,
        DATASET_MANIFEST_SHA256,
        DECISION_BARS,
        EPISODE_ROWS,
        EVIDENCE_COMPONENT_NORMALIZED_SHA256,
        REPLAY_COMPONENT_NORMALIZED_SHA256,
        REVIEW_PROTOCOL_ID,
        REVIEW_PROTOCOL_NORMALIZED_SHA256,
        KrakenBlindedReplayPreflight,
        _candidate_inventory,
        _rows_to_frame,
        _selected_candidate,
        load_dataset_lock_evidence,
        load_replay_review_protocol,
        load_reviewed_component,
    )
    from .kraken_daily_dataset import ASSET_ORDER, KrakenDailyDatasetLock
    from .research_evidence import canonical_json_bytes


EXECUTION_SCHEMA_VERSION = 1
EXECUTION_PROTOCOL_ID = "kraken-btc-eth-xrp-supervised-blinded-replay-v1"
OPERATOR_AUTHORIZATION_PHRASE = "AUTHORIZE_ONE_KRAKEN_BLINDED_REPLAY_EPISODE_V1"
SELECTION_SCHEDULE_SHA256 = (
    "3e805044356777f0bdfa2901db267d714c1e14d11415dd4686acaaaed92f1042"
)
PREFLIGHT_EVIDENCE_NORMALIZED_SHA256 = (
    "ca5958b01370c222efd28c5149bb7a04e7627e0b71eef720db73116c7ccdfdf3"
)
EXECUTION_PROTOCOL_NORMALIZED_SHA256 = (
    "aa98e349b4189223938b0f33e587a601cb57ad5bacc9208c91b9e9f0601348b1"
)
DEFAULT_DATASET_LOCK_EVIDENCE_PATH = Path(
    "KRAKEN_BTC_ETH_XRP_DAILY_DATASET_LOCK_EVIDENCE_V2.md"
)
DEFAULT_REVIEW_PROTOCOL_PATH = Path(
    "KRAKEN_BTC_ETH_XRP_BLINDED_REPLAY_REVIEW_PROTOCOL_V1.md"
)
DEFAULT_PREFLIGHT_EVIDENCE_PATH = Path(
    "KRAKEN_BTC_ETH_XRP_BLINDED_REPLAY_PREFLIGHT_EVIDENCE_V1.md"
)
DEFAULT_EXECUTION_PROTOCOL_PATH = Path(
    "KRAKEN_BTC_ETH_XRP_SUPERVISED_BLINDED_REPLAY_PROTOCOL_V1.md"
)
DEFAULT_REPLAY_COMPONENT_PATH = Path("src/blinded_daily_replay.py")
DEFAULT_EVIDENCE_COMPONENT_PATH = Path("src/blinded_replay_evidence.py")
CATALOG_DIRECTORY_NAME = "catalog"
CATALOG_STAGING_DIRECTORY_NAME = ".catalog.staging"
CATALOG_FILENAME = "replay_catalog.json"
CATALOG_CHECKSUM_FILENAME = "replay_catalog.sha256"


@dataclass(frozen=True)
class EpisodeSpec:
    ordinal: int
    asset: str
    episode_id: str
    directory_name: str


EPISODE_SPECS = (
    EpisodeSpec(1, "BTC-USD", "kraken_btc_usd_episode_01_v1", "episode_01_btc_usd"),
    EpisodeSpec(2, "ETH-USD", "kraken_eth_usd_episode_02_v1", "episode_02_eth_usd"),
    EpisodeSpec(3, "XRP-USD", "kraken_xrp_usd_episode_03_v1", "episode_03_xrp_usd"),
)

CATALOG_KEYS = frozenset(
    {
        "schema_version",
        "status",
        "evidence_type",
        "dataset_id",
        "manifest_sha256",
        "selection_protocol_id",
        "execution_protocol_id",
        "selection_schedule_sha256",
        "asset_order",
        "episode_count",
        "decision_count",
        "episode_evidence",
        "selected_timestamps_exposed_before_replay",
        "source_ohlcv_persisted",
        "chart_images_persisted",
        "network_requests_executed",
        "real_chart_replay_executed",
        "supervised_reconstruction_completed",
        "synthetic_exit_inserted",
        "position_carried_between_episodes",
        "performance_evaluation_executed",
        "strategy_selection_executed",
        "candidate_v2_authorized",
        "bounded_forward_paper_authorized",
        "cloud_execution_authorized",
        "live_execution_authorized",
    }
)
CATALOG_EPISODE_KEYS = frozenset(
    {
        "ordinal",
        "asset",
        "episode_id",
        "directory",
        "evidence_sha256",
        "decision_count",
        "terminal_position_state",
        "terminal_position_resolution",
    }
)


def _normalized_text_bytes(path, label):
    try:
        text = Path(path).read_text(encoding="utf-8")
    except (OSError, UnicodeError) as exc:
        raise RuntimeError(f"Unable to read {label}: {path}") from exc
    return text.replace("\r\n", "\n").replace("\r", "\n").encode("utf-8")


def _load_hash_bound_text(path, expected_sha256, required, label):
    raw = _normalized_text_bytes(path, label)
    digest = hashlib.sha256(raw).hexdigest()
    if digest != expected_sha256:
        raise RuntimeError(f"{label} SHA256 mismatch: {digest} != {expected_sha256}.")
    text = raw.decode("utf-8")
    if any(value not in text for value in required):
        raise RuntimeError(f"{label} required text is missing.")
    return text, digest


def load_preflight_evidence(path=DEFAULT_PREFLIGHT_EVIDENCE_PATH):
    return _load_hash_bound_text(
        path,
        PREFLIGHT_EVIDENCE_NORMALIZED_SHA256,
        (
            "KRAKEN_BLINDED_REPLAY_PREFLIGHT_PASS",
            DATASET_MANIFEST_SHA256,
            SELECTION_SCHEDULE_SHA256,
            "selected timestamps exposed: `false`",
            "real replay authorized: `false`",
        ),
        "Sealed-preflight evidence",
    )


def load_execution_protocol(path=DEFAULT_EXECUTION_PROTOCOL_PATH):
    return _load_hash_bound_text(
        path,
        EXECUTION_PROTOCOL_NORMALIZED_SHA256,
        (
            "Kraken BTC/ETH/XRP Supervised Blinded Replay Protocol v1",
            "SUPERVISED_REPLAY_METHOD_REVIEWED_NOT_AUTHORIZED",
            EXECUTION_PROTOCOL_ID,
            SELECTION_SCHEDULE_SHA256,
            "OPEN_POSITION_UNRESOLVED_AT_EPISODE_END",
        ),
        "Supervised-replay protocol",
    )


def execution_declaration(
    dataset_lock_evidence_path=DEFAULT_DATASET_LOCK_EVIDENCE_PATH,
    review_protocol_path=DEFAULT_REVIEW_PROTOCOL_PATH,
    preflight_evidence_path=DEFAULT_PREFLIGHT_EVIDENCE_PATH,
    execution_protocol_path=DEFAULT_EXECUTION_PROTOCOL_PATH,
    replay_component_path=DEFAULT_REPLAY_COMPONENT_PATH,
    evidence_component_path=DEFAULT_EVIDENCE_COMPONENT_PATH,
):
    _, dataset_digest = load_dataset_lock_evidence(dataset_lock_evidence_path)
    _, review_digest = load_replay_review_protocol(review_protocol_path)
    _, preflight_digest = load_preflight_evidence(preflight_evidence_path)
    _, execution_digest = load_execution_protocol(execution_protocol_path)
    replay_digest = load_reviewed_component(
        replay_component_path,
        REPLAY_COMPONENT_NORMALIZED_SHA256,
        "Replay component",
    )
    evidence_digest = load_reviewed_component(
        evidence_component_path,
        EVIDENCE_COMPONENT_NORMALIZED_SHA256,
        "Replay-evidence component",
    )
    return {
        "schema_version": EXECUTION_SCHEMA_VERSION,
        "status": (
            "KRAKEN_SUPERVISED_BLINDED_REPLAY_REVIEWED_OPERATOR_AUTHORIZATION_REQUIRED"
        ),
        "execution_protocol_id": EXECUTION_PROTOCOL_ID,
        "selection_protocol_id": REVIEW_PROTOCOL_ID,
        "dataset_id": DATASET_ID,
        "dataset_manifest_sha256": DATASET_MANIFEST_SHA256,
        "selection_schedule_sha256": SELECTION_SCHEDULE_SHA256,
        "dataset_lock_evidence_sha256_match": (
            dataset_digest == DATASET_LOCK_EVIDENCE_NORMALIZED_SHA256
        ),
        "review_protocol_sha256_match": (
            review_digest == REVIEW_PROTOCOL_NORMALIZED_SHA256
        ),
        "preflight_evidence_sha256_match": (
            preflight_digest == PREFLIGHT_EVIDENCE_NORMALIZED_SHA256
        ),
        "execution_protocol_sha256_match": (
            execution_digest == EXECUTION_PROTOCOL_NORMALIZED_SHA256
        ),
        "replay_component_sha256_match": (
            replay_digest == REPLAY_COMPONENT_NORMALIZED_SHA256
        ),
        "evidence_component_sha256_match": (
            evidence_digest == EVIDENCE_COMPONENT_NORMALIZED_SHA256
        ),
        "asset_order": list(ASSET_ORDER),
        "episode_count": len(EPISODE_SPECS),
        "episodes_per_invocation": 1,
        "context_bars": CONTEXT_BARS,
        "decision_bars_per_episode": DECISION_BARS,
        "episode_rows": EPISODE_ROWS,
        "sealed_preflight_completed": True,
        "supervised_replay_review_eligible": True,
        "operator_authorization_supplied": False,
        "dataset_opened": False,
        "participant_view_created": False,
        "real_replay_authorized": False,
        "real_chart_replay_executed": False,
        "crypto_strategy_implemented": False,
        "performance_evaluation_executed": False,
        "optimization_authorized": False,
        "candidate_v2_authorized": False,
        "bounded_forward_paper_authorized": False,
        "cloud_execution_authorized": False,
        "live_execution_authorized": False,
    }


def _read_canonical_json(path, label):
    try:
        raw = Path(path).read_bytes()
        payload = json.loads(raw.decode("utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise ValueError(f"Unable to read {label}.") from exc
    if raw != canonical_json_bytes(payload):
        raise ValueError(f"{label} is not canonical JSON.")
    return raw, payload


def _verify_sidecar(path, digest, filename, label):
    try:
        raw = Path(path).read_bytes()
    except OSError as exc:
        raise ValueError(f"Unable to read {label} checksum.") from exc
    if raw != f"{digest}  {filename}\n".encode("ascii"):
        raise ValueError(f"{label} SHA-256 sidecar mismatch.")


def _write_new(path, payload):
    try:
        with Path(path).open("xb") as handle:
            handle.write(payload)
    except FileExistsError as exc:
        raise FileExistsError(f"Refusing to overwrite replay catalog: {path}") from exc


@dataclass(frozen=True)
class LockedKrakenReplayCatalog:
    manifest: dict
    catalog_sha256: str
    episodes: tuple


def _validate_locked_episode(spec, locked):
    manifest = locked.manifest
    if (
        manifest.get("dataset_id") != DATASET_ID
        or manifest.get("manifest_sha256") != DATASET_MANIFEST_SHA256
        or manifest.get("protocol_id") != EXECUTION_PROTOCOL_ID
        or manifest.get("asset") != spec.asset
        or manifest.get("episode_id") != spec.episode_id
        or manifest.get("context_bars") != CONTEXT_BARS
        or manifest.get("decision_count") != DECISION_BARS
    ):
        raise ValueError(f"Completed replay identity mismatch for {spec.asset}.")
    return locked


class KrakenBlindedReplayCatalogLock:
    """Independently re-lock the completed three-episode catalog."""

    def lock(self, evidence_root):
        catalog_directory = Path(evidence_root) / CATALOG_DIRECTORY_NAME
        raw, manifest = _read_canonical_json(
            catalog_directory / CATALOG_FILENAME,
            "Replay catalog",
        )
        digest = hashlib.sha256(raw).hexdigest()
        _verify_sidecar(
            catalog_directory / CATALOG_CHECKSUM_FILENAME,
            digest,
            CATALOG_FILENAME,
            "Replay catalog",
        )
        if frozenset(manifest) != CATALOG_KEYS:
            raise ValueError("Replay catalog fields are not exact.")
        if (
            manifest.get("schema_version") != EXECUTION_SCHEMA_VERSION
            or manifest.get("status")
            != "KRAKEN_SUPERVISED_BLINDED_REPLAY_CATALOG_COMPLETED"
            or manifest.get("evidence_type")
            != "INSPECTED_HYPOTHESIS_RECONSTRUCTION_ONLY"
            or manifest.get("dataset_id") != DATASET_ID
            or manifest.get("manifest_sha256") != DATASET_MANIFEST_SHA256
            or manifest.get("selection_protocol_id") != REVIEW_PROTOCOL_ID
            or manifest.get("execution_protocol_id") != EXECUTION_PROTOCOL_ID
            or manifest.get("selection_schedule_sha256") != SELECTION_SCHEDULE_SHA256
            or manifest.get("asset_order") != list(ASSET_ORDER)
            or manifest.get("episode_count") != len(EPISODE_SPECS)
            or manifest.get("decision_count") != len(EPISODE_SPECS) * DECISION_BARS
        ):
            raise ValueError("Replay catalog identity mismatch.")

        episode_evidence = manifest.get("episode_evidence")
        if not isinstance(episode_evidence, list) or len(episode_evidence) != len(
            EPISODE_SPECS
        ):
            raise ValueError("Replay catalog episode inventory is incomplete.")
        locked_episodes = []
        for spec, item in zip(EPISODE_SPECS, episode_evidence):
            if not isinstance(item, dict) or frozenset(item) != CATALOG_EPISODE_KEYS:
                raise ValueError("Replay catalog episode fields are not exact.")
            if (
                item.get("ordinal") != spec.ordinal
                or item.get("asset") != spec.asset
                or item.get("episode_id") != spec.episode_id
                or item.get("directory") != spec.directory_name
                or item.get("decision_count") != DECISION_BARS
            ):
                raise ValueError("Replay catalog episode order mismatch.")
            locked = _validate_locked_episode(
                spec,
                BlindedReplayEvidenceLock().lock(
                    Path(evidence_root) / spec.directory_name
                ),
            )
            if (
                item.get("evidence_sha256") != locked.evidence_sha256
                or item.get("terminal_position_state")
                != locked.manifest["terminal_position_state"]
                or item.get("terminal_position_resolution")
                != locked.manifest["terminal_position_resolution"]
            ):
                raise ValueError("Replay catalog episode digest mismatch.")
            locked_episodes.append(locked)

        expected_true = (
            "real_chart_replay_executed",
            "supervised_reconstruction_completed",
        )
        if any(manifest.get(field) is not True for field in expected_true):
            raise ValueError("Replay catalog completion flag mismatch.")
        expected_false = (
            "selected_timestamps_exposed_before_replay",
            "source_ohlcv_persisted",
            "chart_images_persisted",
            "network_requests_executed",
            "synthetic_exit_inserted",
            "position_carried_between_episodes",
            "performance_evaluation_executed",
            "strategy_selection_executed",
            "candidate_v2_authorized",
            "bounded_forward_paper_authorized",
            "cloud_execution_authorized",
            "live_execution_authorized",
        )
        if any(manifest.get(field) is not False for field in expected_false):
            raise ValueError("Replay catalog safety flag mismatch.")
        return LockedKrakenReplayCatalog(manifest, digest, tuple(locked_episodes))


def _episode_item(spec, locked):
    return {
        "ordinal": spec.ordinal,
        "asset": spec.asset,
        "episode_id": spec.episode_id,
        "directory": spec.directory_name,
        "evidence_sha256": locked.evidence_sha256,
        "decision_count": locked.manifest["decision_count"],
        "terminal_position_state": locked.manifest["terminal_position_state"],
        "terminal_position_resolution": locked.manifest["terminal_position_resolution"],
    }


def _finalize_catalog(evidence_root, locked_episodes):
    evidence_root = Path(evidence_root)
    staging = evidence_root / CATALOG_STAGING_DIRECTORY_NAME
    final = evidence_root / CATALOG_DIRECTORY_NAME
    if staging.exists():
        raise FileExistsError("Incomplete replay catalog requires review.")
    if final.exists():
        raise FileExistsError("Completed replay catalog already exists.")
    staging.mkdir()
    payload = {
        "schema_version": EXECUTION_SCHEMA_VERSION,
        "status": "KRAKEN_SUPERVISED_BLINDED_REPLAY_CATALOG_COMPLETED",
        "evidence_type": "INSPECTED_HYPOTHESIS_RECONSTRUCTION_ONLY",
        "dataset_id": DATASET_ID,
        "manifest_sha256": DATASET_MANIFEST_SHA256,
        "selection_protocol_id": REVIEW_PROTOCOL_ID,
        "execution_protocol_id": EXECUTION_PROTOCOL_ID,
        "selection_schedule_sha256": SELECTION_SCHEDULE_SHA256,
        "asset_order": list(ASSET_ORDER),
        "episode_count": len(EPISODE_SPECS),
        "decision_count": len(EPISODE_SPECS) * DECISION_BARS,
        "episode_evidence": [
            _episode_item(spec, locked)
            for spec, locked in zip(EPISODE_SPECS, locked_episodes)
        ],
        "selected_timestamps_exposed_before_replay": False,
        "source_ohlcv_persisted": False,
        "chart_images_persisted": False,
        "network_requests_executed": False,
        "real_chart_replay_executed": True,
        "supervised_reconstruction_completed": True,
        "synthetic_exit_inserted": False,
        "position_carried_between_episodes": False,
        "performance_evaluation_executed": False,
        "strategy_selection_executed": False,
        "candidate_v2_authorized": False,
        "bounded_forward_paper_authorized": False,
        "cloud_execution_authorized": False,
        "live_execution_authorized": False,
    }
    raw = canonical_json_bytes(payload)
    digest = hashlib.sha256(raw).hexdigest()
    _write_new(staging / CATALOG_FILENAME, raw)
    _write_new(
        staging / CATALOG_CHECKSUM_FILENAME,
        f"{digest}  {CATALOG_FILENAME}\n".encode("ascii"),
    )
    staging.rename(final)
    return KrakenBlindedReplayCatalogLock().lock(evidence_root)


def _inspect_evidence_root(evidence_root):
    evidence_root = Path(evidence_root)
    if evidence_root.exists() and not evidence_root.is_dir():
        raise ValueError("Replay evidence root must be a directory.")
    evidence_root.mkdir(parents=True, exist_ok=True)
    allowed = {CATALOG_DIRECTORY_NAME, CATALOG_STAGING_DIRECTORY_NAME}
    for spec in EPISODE_SPECS:
        allowed.add(spec.directory_name)
        allowed.add(f".{spec.directory_name}.staging")
    unexpected = sorted(
        path.name for path in evidence_root.iterdir() if path.name not in allowed
    )
    if unexpected:
        raise ValueError(f"Unexpected replay evidence entries: {unexpected}.")
    if (evidence_root / CATALOG_STAGING_DIRECTORY_NAME).exists():
        raise FileExistsError("Incomplete replay catalog requires review.")

    locked_episodes = []
    next_spec = None
    for index, spec in enumerate(EPISODE_SPECS):
        final = evidence_root / spec.directory_name
        staging = evidence_root / f".{spec.directory_name}.staging"
        if staging.exists():
            raise FileExistsError(
                f"Incomplete replay evidence requires review: {staging}"
            )
        if final.exists():
            if next_spec is not None:
                raise ValueError("Replay episode order contains a skipped asset.")
            locked_episodes.append(
                _validate_locked_episode(
                    spec,
                    BlindedReplayEvidenceLock().lock(final),
                )
            )
            continue
        next_spec = spec
        for later in EPISODE_SPECS[index + 1 :]:
            if (evidence_root / later.directory_name).exists() or (
                evidence_root / f".{later.directory_name}.staging"
            ).exists():
                raise ValueError("Replay episode order contains a skipped asset.")
        break

    catalog_exists = (evidence_root / CATALOG_DIRECTORY_NAME).exists()
    if next_spec is not None and catalog_exists:
        raise ValueError("Replay catalog exists before every episode is complete.")
    if next_spec is None and catalog_exists:
        catalog = KrakenBlindedReplayCatalogLock().lock(evidence_root)
    else:
        catalog = None
    return evidence_root, tuple(locked_episodes), next_spec, catalog


def _validated_external_paths(dataset_path, evidence_root):
    project_root = Path(__file__).resolve().parents[1]
    dataset = Path(dataset_path).resolve()
    evidence = Path(evidence_root).resolve()
    if dataset == project_root or dataset.is_relative_to(project_root):
        raise ValueError("Locked replay dataset must remain outside the repository.")
    if evidence == project_root or evidence.is_relative_to(project_root):
        raise ValueError("Replay evidence root must remain outside the repository.")
    if (
        evidence == dataset
        or evidence.is_relative_to(dataset)
        or dataset.is_relative_to(evidence)
    ):
        raise ValueError("Replay evidence and locked dataset paths must not overlap.")
    return dataset, evidence


def _selected_episode_frame(locked, asset):
    frame = _rows_to_frame(locked.assets[asset])
    segments, candidates = _candidate_inventory(asset, frame)
    segment_index, start_offset, _, _ = _selected_candidate(asset, candidates)
    selected = (
        segments[segment_index]
        .iloc[start_offset : start_offset + EPISODE_ROWS]
        .copy(deep=True)
    )
    if len(selected) != EPISODE_ROWS:
        raise RuntimeError("Selected replay episode row count mismatch.")
    return selected


def _prompt_decision(view, input_fn, output_fn):
    allowed = ALLOWED_ACTIONS[view.position_state]
    output_fn(
        f"{view.asset} | sequence={view.sequence} | "
        f"timestamp={view.timestamp.isoformat()} | position={view.position_state}"
    )
    while True:
        action = input_fn(f"Action ({'/'.join(allowed)}): ")
        if isinstance(action, str):
            action = action.strip().upper()
        if action not in allowed:
            output_fn(f"Invalid action. Allowed: {', '.join(allowed)}.")
            continue
        reason = input_fn("Reason: ")
        if not isinstance(reason, str) or not reason.strip():
            output_fn("A nonempty contemporaneous reason is required.")
            continue
        return action, reason.strip()


class MatplotlibReplayRenderer:
    """Keep one in-memory causal candlestick/volume chart open."""

    def __init__(self):
        import matplotlib.pyplot as plt
        from matplotlib.patches import Rectangle

        self._plt = plt
        self._rectangle = Rectangle
        self._interactive_backend = self._plt.get_backend().lower() not in {
            "agg",
            "cairo",
            "pdf",
            "pgf",
            "ps",
            "svg",
            "template",
        }
        self._plt.ion()
        self._figure, (self._price_axis, self._volume_axis) = self._plt.subplots(
            2,
            1,
            figsize=(13, 8),
            sharex=True,
            gridspec_kw={"height_ratios": (4, 1)},
        )

    def __call__(self, view):
        price_axis = self._price_axis
        volume_axis = self._volume_axis
        price_axis.clear()
        volume_axis.clear()
        bars = view.bars
        for x_value, (_, row) in enumerate(bars.iterrows()):
            open_value = float(row["Open"])
            high_value = float(row["High"])
            low_value = float(row["Low"])
            close_value = float(row["Close"])
            volume_value = float(row["Volume"])
            color = "#138a36" if close_value >= open_value else "#c62828"
            price_axis.vlines(x_value, low_value, high_value, color=color, linewidth=1)
            body_low = min(open_value, close_value)
            body_height = abs(close_value - open_value)
            if body_height == 0:
                body_height = max(abs(high_value - low_value) * 0.002, 1e-12)
            price_axis.add_patch(
                self._rectangle(
                    (x_value - 0.3, body_low),
                    0.6,
                    body_height,
                    facecolor=color,
                    edgecolor=color,
                )
            )
            volume_axis.bar(x_value, volume_value, color=color, width=0.6)

        tick_step = max(1, len(bars) // 6)
        ticks = list(range(0, len(bars), tick_step))
        if ticks[-1] != len(bars) - 1:
            ticks.append(len(bars) - 1)
        volume_axis.set_xticks(ticks)
        volume_axis.set_xticklabels(
            [bars.index[value].strftime("%Y-%m-%d") for value in ticks],
            rotation=30,
            ha="right",
        )
        price_axis.set_xlim(-1, len(bars))
        price_axis.set_ylabel("Price")
        volume_axis.set_ylabel("Volume")
        price_axis.grid(alpha=0.2)
        volume_axis.grid(alpha=0.2)
        price_axis.set_title(
            f"{view.asset} | {view.timestamp.isoformat()} | "
            f"position={view.position_state} | sequence={view.sequence}"
        )
        self._figure.tight_layout()
        self._figure.canvas.draw_idle()
        if self._interactive_backend:
            self._plt.show(block=False)
            self._plt.pause(0.05)

    def close(self):
        self._plt.close(self._figure)


class KrakenSupervisedBlindedReplayRunner:
    """Execute exactly the next reviewed asset episode after explicit consent."""

    def __init__(self, dataset_lock_factory=KrakenDailyDatasetLock):
        if not callable(dataset_lock_factory):
            raise TypeError("Dataset-lock factory must be callable.")
        self.dataset_lock_factory = dataset_lock_factory

    def run_next(
        self,
        dataset_path,
        evidence_root,
        *,
        authorization,
        renderer=None,
        input_fn=input,
        output_fn=print,
    ):
        if authorization != OPERATOR_AUTHORIZATION_PHRASE:
            raise PermissionError(
                "Exact one-episode operator authorization is required."
            )
        if not callable(input_fn) or not callable(output_fn):
            raise TypeError("Replay input and output functions must be callable.")
        execution_declaration()
        dataset_path, evidence_root = _validated_external_paths(
            dataset_path, evidence_root
        )
        root, completed, spec, catalog = _inspect_evidence_root(evidence_root)
        if catalog is not None:
            return {
                "status": "KRAKEN_SUPERVISED_BLINDED_REPLAY_ALREADY_COMPLETED",
                "catalog_sha256": catalog.catalog_sha256,
                "episode_count": len(catalog.episodes),
                "additional_replay_authorized": False,
                "performance_evaluation_executed": False,
                "candidate_v2_authorized": False,
                "live_execution_authorized": False,
            }
        if spec is None:
            catalog = _finalize_catalog(root, completed)
            return {
                "status": "KRAKEN_SUPERVISED_BLINDED_REPLAY_CATALOG_COMPLETED",
                "catalog_sha256": catalog.catalog_sha256,
                "episode_count": len(catalog.episodes),
                "additional_replay_authorized": False,
                "performance_evaluation_executed": False,
                "candidate_v2_authorized": False,
                "live_execution_authorized": False,
            }

        locked = self.dataset_lock_factory().lock(dataset_path)
        preflight = KrakenBlindedReplayPreflight(
            dataset_lock_factory=self.dataset_lock_factory
        ).review_locked(locked)
        if preflight.get("selection_schedule_sha256") != SELECTION_SCHEDULE_SHA256:
            raise RuntimeError("Sealed replay selection schedule mismatch.")
        episode_frame = _selected_episode_frame(locked, spec.asset)
        active_renderer = (
            renderer if renderer is not None else MatplotlibReplayRenderer()
        )
        if not callable(active_renderer):
            raise TypeError("Replay renderer must be callable.")

        journal = DurableBlindedReplayJournal(
            root / spec.directory_name,
            dataset_id=DATASET_ID,
            manifest_sha256=DATASET_MANIFEST_SHA256,
            protocol_id=EXECUTION_PROTOCOL_ID,
            asset=spec.asset,
            episode_id=spec.episode_id,
        )
        session = BlindedDailyReplaySession(
            spec.asset,
            episode_frame,
            context_bars=CONTEXT_BARS,
            decision_sink=journal,
        )
        try:
            while not session.is_complete:
                view = session.current_view()
                active_renderer(view)
                action, reason = _prompt_decision(view, input_fn, output_fn)
                session.record_decision(action, reason)
                session.advance()
            recorded = journal.finalize(session.summary())
        finally:
            close = getattr(active_renderer, "close", None)
            if callable(close):
                close()

        episode_locked = _validate_locked_episode(
            spec,
            BlindedReplayEvidenceLock().lock(root / spec.directory_name),
        )
        all_completed = (*completed, episode_locked)
        catalog = (
            _finalize_catalog(root, all_completed)
            if spec.ordinal == len(EPISODE_SPECS)
            else None
        )
        return {
            "status": "KRAKEN_SUPERVISED_BLINDED_REPLAY_EPISODE_COMPLETED",
            "asset": spec.asset,
            "episode_ordinal": spec.ordinal,
            "decision_count": recorded.decision_count,
            "episode_evidence_sha256": episode_locked.evidence_sha256,
            "terminal_position_state": recorded.terminal_position_state,
            "terminal_position_resolution": recorded.terminal_position_resolution,
            "selection_schedule_sha256": SELECTION_SCHEDULE_SHA256,
            "catalog_completed": catalog is not None,
            "catalog_sha256": catalog.catalog_sha256 if catalog else None,
            "operator_authorization_consumed": True,
            "additional_replay_authorized": False,
            "real_chart_replay_executed": True,
            "performance_evaluation_executed": False,
            "strategy_selection_executed": False,
            "candidate_v2_authorized": False,
            "bounded_forward_paper_authorized": False,
            "cloud_execution_authorized": False,
            "live_execution_authorized": False,
        }


def _parser():
    parser = argparse.ArgumentParser(
        description="Review or explicitly run one supervised Kraken replay episode."
    )
    parser.add_argument("--dataset")
    parser.add_argument("--evidence-root")
    parser.add_argument("--authorization")
    parser.add_argument(
        "--dataset-lock-evidence",
        default=str(DEFAULT_DATASET_LOCK_EVIDENCE_PATH),
    )
    parser.add_argument(
        "--review-protocol",
        default=str(DEFAULT_REVIEW_PROTOCOL_PATH),
    )
    parser.add_argument(
        "--preflight-evidence",
        default=str(DEFAULT_PREFLIGHT_EVIDENCE_PATH),
    )
    parser.add_argument(
        "--execution-protocol",
        default=str(DEFAULT_EXECUTION_PROTOCOL_PATH),
    )
    parser.add_argument(
        "--replay-component",
        default=str(DEFAULT_REPLAY_COMPONENT_PATH),
    )
    parser.add_argument(
        "--evidence-component",
        default=str(DEFAULT_EVIDENCE_COMPONENT_PATH),
    )
    return parser


def main(argv=None):
    args = _parser().parse_args(argv)
    supplied = (args.dataset, args.evidence_root, args.authorization)
    if not any(supplied):
        result = execution_declaration(
            args.dataset_lock_evidence,
            args.review_protocol,
            args.preflight_evidence,
            args.execution_protocol,
            args.replay_component,
            args.evidence_component,
        )
    else:
        if not all(supplied):
            raise SystemExit(
                "--dataset, --evidence-root and --authorization are all required."
            )
        result = KrakenSupervisedBlindedReplayRunner().run_next(
            args.dataset,
            args.evidence_root,
            authorization=args.authorization,
        )
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
