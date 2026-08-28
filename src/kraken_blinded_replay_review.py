"""Fail-closed review and sealed preflight for bounded Kraken daily replay."""

import argparse
import hashlib
import json
from decimal import Decimal
from pathlib import Path

import pandas as pd

try:
    from blinded_daily_replay import (
        REQUIRED_OHLCV_COLUMNS,
        find_missing_daily_timestamps,
        split_continuous_daily_segments,
    )
    from kraken_daily_dataset import ASSET_ORDER, KrakenDailyDatasetLock
    from research_evidence import canonical_json_bytes
except ImportError:  # pragma: no cover - package import compatibility
    from .blinded_daily_replay import (
        REQUIRED_OHLCV_COLUMNS,
        find_missing_daily_timestamps,
        split_continuous_daily_segments,
    )
    from .kraken_daily_dataset import ASSET_ORDER, KrakenDailyDatasetLock
    from .research_evidence import canonical_json_bytes


REVIEW_SCHEMA_VERSION = 1
REVIEW_PROTOCOL_ID = "kraken-btc-eth-xrp-bounded-blinded-replay-review-v1"
DATASET_ID = (
    "kraken-spot-btc-eth-xrp-native-1d-20190101-20260401-archive-only-v2"
)
DATASET_MANIFEST_SHA256 = (
    "8c91b42f2bc0c16a0ef0c6b4373572ac53fbf7f5937d4ebbbe75a0d39483df1c"
)
DATASET_LOCK_EVIDENCE_NORMALIZED_SHA256 = (
    "cd83822005525381024f0cd90130f34246ec609a90436c714b79633daed82184"
)
REVIEW_PROTOCOL_NORMALIZED_SHA256 = (
    "5ce8159192817d2d6cba42b0a9c4168cca027feb8ff4a31fd23ea356b9f495eb"
)
REPLAY_COMPONENT_NORMALIZED_SHA256 = (
    "9aa103e0cb8c1cb48479eb6b6d7357884cb6a3373b04613d9461d779fc0972a0"
)
EVIDENCE_COMPONENT_NORMALIZED_SHA256 = (
    "2341e3f7da6086565caf537df61df9410dfb6f6931944d1923122822ec103bf5"
)
DEFAULT_DATASET_LOCK_EVIDENCE_PATH = Path(
    "KRAKEN_BTC_ETH_XRP_DAILY_DATASET_LOCK_EVIDENCE_V2.md"
)
DEFAULT_REVIEW_PROTOCOL_PATH = Path(
    "KRAKEN_BTC_ETH_XRP_BLINDED_REPLAY_REVIEW_PROTOCOL_V1.md"
)
DEFAULT_REPLAY_COMPONENT_PATH = Path("src/blinded_daily_replay.py")
DEFAULT_EVIDENCE_COMPONENT_PATH = Path("src/blinded_replay_evidence.py")
CONTEXT_BARS = 30
DECISION_BARS = 60
EPISODE_ROWS = CONTEXT_BARS + DECISION_BARS - 1
EXPECTED_MISSING_TIMESTAMPS = {
    "BTC-USD": ("2024-03-31T00:00:00Z",),
    "ETH-USD": (),
    "XRP-USD": (
        "2022-05-11T00:00:00Z",
        "2022-05-12T00:00:00Z",
    ),
}
EXPECTED_OBSERVED_ROWS = {"BTC-USD": 2646, "ETH-USD": 2647, "XRP-USD": 2645}
EXPECTED_SEGMENT_ROWS = {
    "BTC-USD": (1916, 730),
    "ETH-USD": (2647,),
    "XRP-USD": (1226, 1419),
}


def _normalized_text_bytes(path):
    try:
        text = Path(path).read_text(encoding="utf-8")
    except (OSError, UnicodeError) as exc:
        raise RuntimeError(f"Unable to read replay review contract: {path}") from exc
    return text.replace("\r\n", "\n").replace("\r", "\n").encode("utf-8")


def normalized_text_sha256(path):
    return hashlib.sha256(_normalized_text_bytes(path)).hexdigest()


def _load_hash_bound_text(path, expected_sha256, required, label):
    raw = _normalized_text_bytes(path)
    digest = hashlib.sha256(raw).hexdigest()
    if digest != expected_sha256:
        raise RuntimeError(
            f"{label} SHA256 mismatch: {digest} != {expected_sha256}."
        )
    text = raw.decode("utf-8")
    if any(value not in text for value in required):
        raise RuntimeError(f"{label} required contract text is missing.")
    return text, digest


def load_dataset_lock_evidence(path=DEFAULT_DATASET_LOCK_EVIDENCE_PATH):
    return _load_hash_bound_text(
        path,
        DATASET_LOCK_EVIDENCE_NORMALIZED_SHA256,
        (
            "LOCKED_NON_PERFORMANCE_DATASET_INDEPENDENTLY_REVALIDATED",
            DATASET_ID,
            DATASET_MANIFEST_SHA256,
            "INDEPENDENT_RELOCK_PASS",
        ),
        "Dataset-lock evidence",
    )


def load_replay_review_protocol(path=DEFAULT_REVIEW_PROTOCOL_PATH):
    return _load_hash_bound_text(
        path,
        REVIEW_PROTOCOL_NORMALIZED_SHA256,
        (
            "Kraken BTC/ETH/XRP Bounded Blinded Replay Review Protocol v1",
            "METHODOLOGY_REVIEWED_PREFLIGHT_NOT_EXECUTED",
            REVIEW_PROTOCOL_ID,
            DATASET_MANIFEST_SHA256,
            "OPEN_POSITION_UNRESOLVED_AT_EPISODE_END",
        ),
        "Replay-review protocol",
    )


def load_reviewed_component(path, expected_sha256, label):
    raw = _normalized_text_bytes(path)
    digest = hashlib.sha256(raw).hexdigest()
    if digest != expected_sha256:
        raise RuntimeError(
            f"{label} SHA256 mismatch: {digest} != {expected_sha256}."
        )
    return digest


def review_declaration(
    dataset_lock_evidence_path=DEFAULT_DATASET_LOCK_EVIDENCE_PATH,
    review_protocol_path=DEFAULT_REVIEW_PROTOCOL_PATH,
    replay_component_path=DEFAULT_REPLAY_COMPONENT_PATH,
    evidence_component_path=DEFAULT_EVIDENCE_COMPONENT_PATH,
):
    _, lock_evidence_digest = load_dataset_lock_evidence(dataset_lock_evidence_path)
    _, protocol_digest = load_replay_review_protocol(review_protocol_path)
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
        "schema_version": REVIEW_SCHEMA_VERSION,
        "status": "KRAKEN_BLINDED_REPLAY_METHODOLOGY_REVIEWED_PREFLIGHT_REQUIRED",
        "protocol_id": REVIEW_PROTOCOL_ID,
        "dataset_id": DATASET_ID,
        "dataset_manifest_sha256": DATASET_MANIFEST_SHA256,
        "dataset_lock_evidence_sha256_match": (
            lock_evidence_digest == DATASET_LOCK_EVIDENCE_NORMALIZED_SHA256
        ),
        "review_protocol_sha256_match": (
            protocol_digest == REVIEW_PROTOCOL_NORMALIZED_SHA256
        ),
        "replay_component_sha256_match": (
            replay_digest == REPLAY_COMPONENT_NORMALIZED_SHA256
        ),
        "evidence_component_sha256_match": (
            evidence_digest == EVIDENCE_COMPONENT_NORMALIZED_SHA256
        ),
        "asset_order": list(ASSET_ORDER),
        "episode_count": len(ASSET_ORDER),
        "episodes_per_asset": 1,
        "context_bars": CONTEXT_BARS,
        "decision_bars_per_episode": DECISION_BARS,
        "episode_rows": EPISODE_ROWS,
        "selection_uses_ohlcv": False,
        "durable_decision_required_before_advance": True,
        "terminal_open_position_policy": (
            "OPEN_POSITION_UNRESOLVED_AT_EPISODE_END"
        ),
        "preflight_executed": False,
        "selected_timestamps_exposed": False,
        "real_replay_review_eligible": False,
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


def _rows_to_frame(rows):
    index = []
    values = []
    for row in rows:
        if len(row) != 6:
            raise ValueError("Locked replay row must contain exact canonical OHLCV.")
        timestamp = pd.Timestamp(row[0])
        if timestamp.tzinfo is None:
            raise ValueError("Locked replay timestamp must be timezone-aware.")
        index.append(timestamp.tz_convert("UTC"))
        values.append([Decimal(value) for value in row[1:]])
    return pd.DataFrame(
        values,
        index=pd.DatetimeIndex(index),
        columns=REQUIRED_OHLCV_COLUMNS,
    )


def _candidate_inventory(asset, frame):
    segments = split_continuous_daily_segments(frame)
    candidates = []
    for segment_index, segment in enumerate(segments):
        available = len(segment) - EPISODE_ROWS + 1
        for start_offset in range(max(0, available)):
            start = segment.index[start_offset]
            end_exclusive = segment.index[start_offset + EPISODE_ROWS - 1] + pd.Timedelta(
                days=1
            )
            candidates.append((segment_index, start_offset, start, end_exclusive))
    if not candidates:
        raise RuntimeError(f"No reviewed replay episode is available for {asset}.")
    return segments, candidates


def _selected_candidate(asset, candidates):
    seed = f"{REVIEW_PROTOCOL_ID}|{DATASET_MANIFEST_SHA256}|{asset}".encode()
    digest = hashlib.sha256(seed).digest()
    index = int.from_bytes(digest, byteorder="big") % len(candidates)
    return candidates[index]


class KrakenBlindedReplayPreflight:
    """Re-lock real data and compute a sealed price-independent schedule."""

    def __init__(self, dataset_lock_factory=KrakenDailyDatasetLock):
        if not callable(dataset_lock_factory):
            raise TypeError("Dataset-lock factory must be callable.")
        self.dataset_lock_factory = dataset_lock_factory

    def review_locked(self, locked):
        if locked.manifest_sha256 != DATASET_MANIFEST_SHA256:
            raise RuntimeError("Kraken replay manifest SHA256 mismatch.")
        manifest = locked.manifest
        if manifest.get("dataset_id") != DATASET_ID:
            raise RuntimeError("Kraken replay dataset identity mismatch.")
        if manifest.get("source_mode") != "OFFICIAL_OHLCVT_ARCHIVES_ONLY":
            raise RuntimeError("Kraken replay source mode mismatch.")
        if manifest.get("network_requests_executed") is not False:
            raise RuntimeError("Kraken replay lock contains network execution.")
        if tuple(locked.assets) != ASSET_ORDER:
            raise RuntimeError("Kraken replay asset order mismatch.")

        asset_evidence = {}
        sealed_schedule = []
        for asset in ASSET_ORDER:
            rows = locked.assets[asset]
            if len(rows) != EXPECTED_OBSERVED_ROWS[asset]:
                raise RuntimeError(f"Kraken replay observed-row mismatch for {asset}.")
            frame = _rows_to_frame(rows)
            missing = tuple(
                timestamp.strftime("%Y-%m-%dT%H:%M:%SZ")
                for timestamp in find_missing_daily_timestamps(frame)
            )
            if missing != EXPECTED_MISSING_TIMESTAMPS[asset]:
                raise RuntimeError(f"Kraken replay missing-timestamp drift for {asset}.")
            manifest_asset = manifest["assets"][asset]
            if tuple(manifest_asset.get("missing_timestamps", ())) != missing:
                raise RuntimeError(f"Kraken manifest gap evidence mismatch for {asset}.")
            segments, candidates = _candidate_inventory(asset, frame)
            segment_rows = tuple(len(segment) for segment in segments)
            if segment_rows != EXPECTED_SEGMENT_ROWS[asset]:
                raise RuntimeError(f"Kraken replay segment drift for {asset}.")
            selected = _selected_candidate(asset, candidates)
            sealed_schedule.append(
                {
                    "asset": asset,
                    "start": selected[2].isoformat(),
                    "end_exclusive": selected[3].isoformat(),
                    "episode_rows": EPISODE_ROWS,
                    "context_bars": CONTEXT_BARS,
                    "decision_bars": DECISION_BARS,
                }
            )
            asset_evidence[asset] = {
                "observed_rows": len(frame),
                "missing_count": len(missing),
                "continuous_segment_count": len(segments),
                "continuous_segment_rows": list(segment_rows),
                "candidate_episode_count": len(candidates),
                "selected_episode_count": 1,
                "selected_timestamps_exposed": False,
            }

        schedule_bytes = canonical_json_bytes(sealed_schedule)
        return {
            "schema_version": REVIEW_SCHEMA_VERSION,
            "status": "KRAKEN_BLINDED_REPLAY_PREFLIGHT_PASS",
            "protocol_id": REVIEW_PROTOCOL_ID,
            "dataset_id": DATASET_ID,
            "dataset_manifest_sha256": locked.manifest_sha256,
            "source_mode": manifest["source_mode"],
            "network_requests_executed": False,
            "asset_order": list(ASSET_ORDER),
            "assets": asset_evidence,
            "episode_count": len(ASSET_ORDER),
            "context_bars": CONTEXT_BARS,
            "decision_bars_per_episode": DECISION_BARS,
            "episode_rows": EPISODE_ROWS,
            "selection_schedule_sha256": hashlib.sha256(schedule_bytes).hexdigest(),
            "selection_schedule_persisted": False,
            "selection_uses_ohlcv": False,
            "selected_timestamps_exposed": False,
            "preflight_executed": True,
            "real_replay_review_eligible": True,
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

    def review(self, dataset_path):
        locked = self.dataset_lock_factory().lock(dataset_path)
        return self.review_locked(locked)


def _parser():
    parser = argparse.ArgumentParser(
        description="Review or preflight bounded blinded Kraken daily replay."
    )
    parser.add_argument("--dataset")
    parser.add_argument(
        "--dataset-lock-evidence",
        default=str(DEFAULT_DATASET_LOCK_EVIDENCE_PATH),
    )
    parser.add_argument(
        "--review-protocol",
        default=str(DEFAULT_REVIEW_PROTOCOL_PATH),
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
    declaration = review_declaration(
        args.dataset_lock_evidence,
        args.review_protocol,
        args.replay_component,
        args.evidence_component,
    )
    result = (
        KrakenBlindedReplayPreflight().review(args.dataset)
        if args.dataset
        else declaration
    )
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
