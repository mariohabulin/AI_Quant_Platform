"""Fail-closed durable evidence for one blinded daily replay episode."""

import hashlib
import json
import re
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path

try:
    from blinded_daily_replay import BlindedReplayDecision
    from research_evidence import canonical_json_bytes
except ImportError:  # pragma: no cover - package import compatibility
    from .blinded_daily_replay import BlindedReplayDecision
    from .research_evidence import canonical_json_bytes


EVIDENCE_SCHEMA_VERSION = 1
DECISION_DIRECTORY_NAME = "decisions"
MANIFEST_FILENAME = "replay_evidence.json"
CHECKSUM_FILENAME = "replay_evidence.sha256"
BOUNDARY_KINDS = ("BOUNDED_EPISODE_END",)
LOWER_HEX_64 = re.compile(r"[0-9a-f]{64}")
DECISION_KEYS = frozenset(
    {
        "asset",
        "sequence",
        "timestamp",
        "action",
        "reason",
        "position_before",
        "position_after",
        "visible_bars_sha256",
    }
)
DECISION_PAYLOAD_KEYS = frozenset(
    {
        "schema_version",
        "evidence_type",
        "dataset_id",
        "manifest_sha256",
        "protocol_id",
        "asset",
        "episode_id",
        "previous_decision_sha256",
        "decision",
        "future_bars_persisted",
        "performance_evaluation_executed",
        "strategy_selection_executed",
    }
)
MANIFEST_KEYS = frozenset(
    {
        "schema_version",
        "status",
        "evidence_type",
        "dataset_id",
        "manifest_sha256",
        "protocol_id",
        "asset",
        "episode_id",
        "context_bars",
        "decision_count",
        "decision_evidence",
        "final_decision_sha256",
        "boundary_kind",
        "terminal_position_state",
        "terminal_position_resolution",
        "synthetic_exit_inserted",
        "position_carried_to_another_episode",
        "future_bars_persisted",
        "performance_evaluation_executed",
        "strategy_selection_executed",
        "candidate_v2_authorized",
        "bounded_forward_paper_authorized",
        "cloud_execution_authorized",
        "live_execution_authorized",
    }
)
POSITION_TRANSITIONS = {
    ("FLAT", "ENTER"): "LONG",
    ("FLAT", "SKIP"): "FLAT",
    ("LONG", "EXIT"): "FLAT",
    ("LONG", "HOLD"): "LONG",
}


def _required_text(value, label):
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{label} must be a nonempty string.")
    return value.strip()


def _required_sha256(value, label):
    value = _required_text(value, label)
    if LOWER_HEX_64.fullmatch(value) is None:
        raise ValueError(f"{label} must be lowercase SHA-256 hex.")
    return value


def _required_utc_timestamp(value, label):
    value = _required_text(value, label)
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise ValueError(f"{label} must be a valid timestamp.") from exc
    if parsed.tzinfo is None or parsed.utcoffset() != timedelta(0):
        raise ValueError(f"{label} must be UTC.")
    return parsed


def _write_new(path, payload):
    path = Path(path)
    try:
        with path.open("xb") as handle:
            handle.write(payload)
    except FileExistsError as exc:
        raise FileExistsError(f"Refusing to overwrite replay evidence: {path}") from exc


@dataclass(frozen=True)
class RecordedBlindedReplayEpisode:
    evidence_path: Path
    checksum_path: Path
    evidence_sha256: str
    decision_count: int
    terminal_position_state: str
    terminal_position_resolution: str
    status: str = "BLINDED_REPLAY_EPISODE_EVIDENCE_RECORDED"

    def as_dict(self):
        return {
            "status": self.status,
            "evidence_path": str(self.evidence_path),
            "checksum_path": str(self.checksum_path),
            "evidence_sha256": self.evidence_sha256,
            "decision_count": self.decision_count,
            "terminal_position_state": self.terminal_position_state,
            "terminal_position_resolution": self.terminal_position_resolution,
            "performance_evaluation_executed": False,
            "strategy_selection_executed": False,
            "candidate_v2_authorized": False,
            "bounded_forward_paper_authorized": False,
            "live_execution_authorized": False,
        }


@dataclass(frozen=True)
class LockedBlindedReplayEvidence:
    manifest: dict
    evidence_sha256: str
    decisions: tuple


class BlindedReplayEvidenceLock:
    """Independently revalidate a completed replay-evidence directory."""

    @staticmethod
    def _read_canonical_json(path, label):
        try:
            raw = Path(path).read_bytes()
            payload = json.loads(raw.decode("utf-8"))
        except (OSError, UnicodeError, json.JSONDecodeError) as exc:
            raise ValueError(f"Unable to read {label} evidence.") from exc
        if raw != canonical_json_bytes(payload):
            raise ValueError(f"{label} evidence is not canonical JSON.")
        return raw, payload

    @staticmethod
    def _verify_sidecar(path, digest, filename, label):
        try:
            actual = Path(path).read_bytes()
        except OSError as exc:
            raise ValueError(f"Unable to read {label} checksum.") from exc
        expected = f"{digest}  {filename}\n".encode("ascii")
        if actual != expected:
            raise ValueError(f"{label} SHA-256 sidecar mismatch.")

    def lock(self, output_directory):
        output_directory = Path(output_directory)
        manifest_path = output_directory / MANIFEST_FILENAME
        raw, manifest = self._read_canonical_json(manifest_path, "Replay manifest")
        digest = hashlib.sha256(raw).hexdigest()
        self._verify_sidecar(
            output_directory / CHECKSUM_FILENAME,
            digest,
            MANIFEST_FILENAME,
            "Replay manifest",
        )
        if manifest.get("schema_version") != EVIDENCE_SCHEMA_VERSION:
            raise ValueError("Replay evidence schema version mismatch.")
        if frozenset(manifest) != MANIFEST_KEYS:
            raise ValueError("Replay evidence manifest fields are not exact.")
        if manifest.get("status") != "BLINDED_REPLAY_EPISODE_COMPLETED":
            raise ValueError("Replay evidence status mismatch.")
        if manifest.get("evidence_type") != (
            "INSPECTED_HYPOTHESIS_RECONSTRUCTION_ONLY"
        ):
            raise ValueError("Replay evidence role mismatch.")
        dataset_id = _required_text(manifest.get("dataset_id"), "Dataset ID")
        manifest_sha256 = _required_sha256(
            manifest.get("manifest_sha256"), "Manifest SHA-256"
        )
        protocol_id = _required_text(manifest.get("protocol_id"), "Protocol ID")
        asset = _required_text(manifest.get("asset"), "Asset")
        episode_id = _required_text(manifest.get("episode_id"), "Episode ID")
        context_bars = manifest.get("context_bars")
        if (
            not isinstance(context_bars, int)
            or isinstance(context_bars, bool)
            or context_bars < 2
        ):
            raise ValueError("Replay context-bar evidence is invalid.")
        if manifest.get("boundary_kind") not in BOUNDARY_KINDS:
            raise ValueError("Replay boundary kind is not reviewed.")
        evidence = manifest.get("decision_evidence")
        decision_count = manifest.get("decision_count")
        if (
            not isinstance(evidence, list)
            or not isinstance(decision_count, int)
            or isinstance(decision_count, bool)
            or decision_count <= 0
            or len(evidence) != decision_count
        ):
            raise ValueError("Replay decision inventory is incomplete.")

        previous = None
        previous_timestamp = None
        position_state = "FLAT"
        decisions = []
        for sequence, item in enumerate(evidence):
            expected_file = f"{DECISION_DIRECTORY_NAME}/{sequence:06d}.json"
            if (
                not isinstance(item, dict)
                or frozenset(item) != {"file", "sha256"}
                or item.get("file") != expected_file
            ):
                raise ValueError("Replay decision filename/order mismatch.")
            expected_digest = _required_sha256(
                item.get("sha256"), "Decision SHA-256"
            )
            decision_path = output_directory / expected_file
            decision_raw, payload = self._read_canonical_json(
                decision_path, "Replay decision"
            )
            decision_digest = hashlib.sha256(decision_raw).hexdigest()
            if decision_digest != expected_digest:
                raise ValueError("Replay decision SHA-256 mismatch.")
            self._verify_sidecar(
                decision_path.with_name(f"{decision_path.name}.sha256"),
                decision_digest,
                decision_path.name,
                "Replay decision",
            )
            if payload.get("schema_version") != EVIDENCE_SCHEMA_VERSION:
                raise ValueError("Replay decision schema version mismatch.")
            if frozenset(payload) != DECISION_PAYLOAD_KEYS:
                raise ValueError("Replay decision payload fields are not exact.")
            if payload.get("evidence_type") != "BLINDED_REPLAY_DECISION":
                raise ValueError("Replay decision evidence type mismatch.")
            if (
                payload.get("dataset_id") != dataset_id
                or payload.get("manifest_sha256") != manifest_sha256
                or payload.get("protocol_id") != protocol_id
                or payload.get("asset") != asset
                or payload.get("episode_id") != episode_id
            ):
                raise ValueError("Replay decision identity mismatch.")
            if payload.get("previous_decision_sha256") != previous:
                raise ValueError("Replay decision hash chain mismatch.")
            decision = payload.get("decision")
            if (
                not isinstance(decision, dict)
                or frozenset(decision) != DECISION_KEYS
                or decision.get("asset") != asset
                or decision.get("sequence") != sequence
            ):
                raise ValueError("Replay decision sequence evidence mismatch.")
            reason = decision.get("reason")
            if not isinstance(reason, str) or not reason.strip():
                raise ValueError("Replay decision reason evidence is invalid.")
            _required_sha256(
                decision.get("visible_bars_sha256"), "Visible-bars SHA-256"
            )
            timestamp = _required_utc_timestamp(
                decision.get("timestamp"), "Replay decision timestamp"
            )
            if previous_timestamp is not None and (
                timestamp - previous_timestamp != timedelta(days=1)
            ):
                raise ValueError("Replay decision timestamps are not continuous daily.")
            if decision.get("position_before") != position_state:
                raise ValueError("Replay decision position chain mismatch.")
            expected_after = POSITION_TRANSITIONS.get(
                (position_state, decision.get("action"))
            )
            if expected_after is None or decision.get("position_after") != expected_after:
                raise ValueError("Replay decision position transition mismatch.")
            if payload.get("future_bars_persisted") is not False:
                raise ValueError("Replay decision contains future-bar evidence.")
            if payload.get("performance_evaluation_executed") is not False:
                raise ValueError("Replay decision contains performance execution.")
            if payload.get("strategy_selection_executed") is not False:
                raise ValueError("Replay decision contains strategy selection.")
            previous = decision_digest
            previous_timestamp = timestamp
            position_state = expected_after
            decisions.append(decision)

        if manifest.get("final_decision_sha256") != previous:
            raise ValueError("Replay final decision SHA-256 mismatch.")
        terminal = manifest.get("terminal_position_state")
        if terminal != position_state:
            raise ValueError("Replay terminal position does not match decisions.")
        expected_resolution = (
            "FLAT_AT_EPISODE_END"
            if terminal == "FLAT"
            else "OPEN_POSITION_UNRESOLVED_AT_EPISODE_END"
            if terminal == "LONG"
            else None
        )
        if manifest.get("terminal_position_resolution") != expected_resolution:
            raise ValueError("Replay terminal-position resolution mismatch.")
        for field in (
            "synthetic_exit_inserted",
            "position_carried_to_another_episode",
            "future_bars_persisted",
            "performance_evaluation_executed",
            "strategy_selection_executed",
            "candidate_v2_authorized",
            "bounded_forward_paper_authorized",
            "cloud_execution_authorized",
            "live_execution_authorized",
        ):
            if manifest.get(field) is not False:
                raise ValueError(f"Replay safety flag mismatch: {field}.")
        return LockedBlindedReplayEvidence(manifest, digest, tuple(decisions))


class DurableBlindedReplayJournal:
    """Persist each decision before the session is allowed to advance."""

    def __init__(
        self,
        output_directory,
        *,
        dataset_id,
        manifest_sha256,
        protocol_id,
        asset,
        episode_id,
    ):
        self.output_directory = Path(output_directory)
        self.staging_directory = self.output_directory.with_name(
            f".{self.output_directory.name}.staging"
        )
        self.dataset_id = _required_text(dataset_id, "Dataset ID")
        self.manifest_sha256 = _required_sha256(
            manifest_sha256, "Manifest SHA-256"
        )
        self.protocol_id = _required_text(protocol_id, "Protocol ID")
        self.asset = _required_text(asset, "Asset")
        self.episode_id = _required_text(episode_id, "Episode ID")
        if self.output_directory.exists():
            raise FileExistsError(
                f"Replay evidence already exists: {self.output_directory}"
            )
        if self.staging_directory.exists():
            raise FileExistsError(
                f"Incomplete replay evidence requires review: "
                f"{self.staging_directory}"
            )
        self.staging_directory.mkdir(parents=True)
        self.decision_directory = self.staging_directory / DECISION_DIRECTORY_NAME
        self.decision_directory.mkdir()
        self._next_sequence = 0
        self._previous_decision_sha256 = None
        self._decision_evidence = []
        self._position_state = "FLAT"
        self._finalized = False

    def append(self, decision):
        if self._finalized:
            raise RuntimeError("Replay evidence is already finalized.")
        if not isinstance(decision, BlindedReplayDecision):
            raise TypeError("Replay evidence requires BlindedReplayDecision.")
        if decision.asset != self.asset:
            raise ValueError("Replay decision asset does not match the journal.")
        if decision.sequence != self._next_sequence:
            raise ValueError("Replay decision sequence is not exact.")
        if decision.position_before != self._position_state:
            raise ValueError("Replay decision position chain is not exact.")
        expected_after = POSITION_TRANSITIONS.get(
            (self._position_state, decision.action)
        )
        if expected_after is None or decision.position_after != expected_after:
            raise ValueError("Replay decision position transition is invalid.")
        _required_sha256(decision.visible_bars_sha256, "Visible-bars SHA-256")
        _required_text(decision.reason, "Replay decision reason")

        filename = f"{decision.sequence:06d}.json"
        payload = {
            "schema_version": EVIDENCE_SCHEMA_VERSION,
            "evidence_type": "BLINDED_REPLAY_DECISION",
            "dataset_id": self.dataset_id,
            "manifest_sha256": self.manifest_sha256,
            "protocol_id": self.protocol_id,
            "asset": self.asset,
            "episode_id": self.episode_id,
            "previous_decision_sha256": self._previous_decision_sha256,
            "decision": decision.as_dict(),
            "future_bars_persisted": False,
            "performance_evaluation_executed": False,
            "strategy_selection_executed": False,
        }
        raw = canonical_json_bytes(payload)
        digest = hashlib.sha256(raw).hexdigest()
        sidecar_name = f"{filename}.sha256"
        _write_new(self.decision_directory / filename, raw)
        _write_new(
            self.decision_directory / sidecar_name,
            f"{digest}  {filename}\n".encode("ascii"),
        )
        self._decision_evidence.append(
            {"file": f"{DECISION_DIRECTORY_NAME}/{filename}", "sha256": digest}
        )
        self._previous_decision_sha256 = digest
        self._position_state = expected_after
        self._next_sequence += 1
        return digest

    __call__ = append

    def finalize(self, summary, *, boundary_kind="BOUNDED_EPISODE_END"):
        if self._finalized:
            raise RuntimeError("Replay evidence is already finalized.")
        if boundary_kind not in BOUNDARY_KINDS:
            raise ValueError("Replay boundary kind is not reviewed.")
        if not isinstance(summary, dict):
            raise TypeError("Replay summary must be a dictionary.")
        if summary.get("status") != "BLINDED_DAILY_REPLAY_COMPLETED":
            raise ValueError("Only a completed replay episode can be finalized.")
        if summary.get("asset") != self.asset:
            raise ValueError("Replay summary asset does not match the journal.")
        if summary.get("decision_count") != self._next_sequence:
            raise ValueError("Replay summary decision count does not match evidence.")
        if summary.get("performance_evaluation_executed") is not False:
            raise ValueError("Replay evidence cannot contain performance execution.")
        if summary.get("strategy_selection_executed") is not False:
            raise ValueError("Replay evidence cannot contain strategy selection.")
        terminal = summary.get("position_state")
        if terminal not in ("FLAT", "LONG"):
            raise ValueError("Replay terminal position state is invalid.")
        if terminal != self._position_state:
            raise ValueError("Replay summary terminal position does not match decisions.")
        resolution = (
            "FLAT_AT_EPISODE_END"
            if terminal == "FLAT"
            else "OPEN_POSITION_UNRESOLVED_AT_EPISODE_END"
        )
        payload = {
            "schema_version": EVIDENCE_SCHEMA_VERSION,
            "status": "BLINDED_REPLAY_EPISODE_COMPLETED",
            "evidence_type": "INSPECTED_HYPOTHESIS_RECONSTRUCTION_ONLY",
            "dataset_id": self.dataset_id,
            "manifest_sha256": self.manifest_sha256,
            "protocol_id": self.protocol_id,
            "asset": self.asset,
            "episode_id": self.episode_id,
            "context_bars": summary.get("context_bars"),
            "decision_count": self._next_sequence,
            "decision_evidence": list(self._decision_evidence),
            "final_decision_sha256": self._previous_decision_sha256,
            "boundary_kind": boundary_kind,
            "terminal_position_state": terminal,
            "terminal_position_resolution": resolution,
            "synthetic_exit_inserted": False,
            "position_carried_to_another_episode": False,
            "future_bars_persisted": False,
            "performance_evaluation_executed": False,
            "strategy_selection_executed": False,
            "candidate_v2_authorized": False,
            "bounded_forward_paper_authorized": False,
            "cloud_execution_authorized": False,
            "live_execution_authorized": False,
        }
        raw = canonical_json_bytes(payload)
        digest = hashlib.sha256(raw).hexdigest()
        _write_new(self.staging_directory / MANIFEST_FILENAME, raw)
        _write_new(
            self.staging_directory / CHECKSUM_FILENAME,
            f"{digest}  {MANIFEST_FILENAME}\n".encode("ascii"),
        )
        self.staging_directory.rename(self.output_directory)
        self._finalized = True
        return RecordedBlindedReplayEpisode(
            evidence_path=self.output_directory / MANIFEST_FILENAME,
            checksum_path=self.output_directory / CHECKSUM_FILENAME,
            evidence_sha256=digest,
            decision_count=self._next_sequence,
            terminal_position_state=terminal,
            terminal_position_resolution=resolution,
        )
