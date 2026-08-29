"""Fail-closed calendar partitions for Kraken AI-driven v2 research.

This component freezes metadata and validates timestamp indexes only.  It does
not locate or open dataset bytes, calculate features, execute the state/risk
layers, score performance, search parameters or authorize any real order.
"""

from dataclasses import asdict, dataclass
import hashlib
import json

import pandas as pd


SCHEMA_VERSION = 1
PARTITION_PROTOCOL_ID = "kraken-btc-eth-xrp-ai-driven-v2-partition-v1"
DATASET_ID = (
    "kraken-spot-btc-eth-xrp-native-1d-20190101-20260401-archive-only-v2"
)
DATASET_MANIFEST_SHA256 = (
    "8c91b42f2bc0c16a0ef0c6b4373572ac53fbf7f5937d4ebbbe75a0d39483df1c"
)
V1_BTC_EPISODE_EVIDENCE_SHA256 = (
    "56710a21a423a63963e5c97ab6ca956021f9cd7a7d494c3f29a197068367ff60"
)
ASSET_ORDER = ("BTC-USD", "ETH-USD", "XRP-USD")
PARTITION_ORDER = ("DEVELOPMENT", "CALIBRATION", "EVALUATION")
RESEARCH_START_UTC = "2019-01-01T00:00:00Z"
DEVELOPMENT_END_EXCLUSIVE_UTC = "2024-04-01T00:00:00Z"
CALIBRATION_START_UTC = DEVELOPMENT_END_EXCLUSIVE_UTC
CALIBRATION_END_EXCLUSIVE_UTC = "2025-04-01T00:00:00Z"
EVALUATION_START_UTC = CALIBRATION_END_EXCLUSIVE_UTC
EVALUATION_END_EXCLUSIVE_UTC = "2026-04-01T00:00:00Z"
INSPECTED_BTC_START_UTC = "2024-05-08T00:00:00Z"
INSPECTED_BTC_END_UTC = "2024-07-06T00:00:00Z"
DAILY_STEP = pd.Timedelta(days=1)
KNOWN_GAPS_UTC = {
    "BTC-USD": ("2024-03-31T00:00:00Z",),
    "ETH-USD": (),
    "XRP-USD": (
        "2022-05-11T00:00:00Z",
        "2022-05-12T00:00:00Z",
    ),
}


def _utc_midnight(value, label):
    try:
        timestamp = pd.Timestamp(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{label} must be a valid timestamp.") from exc
    if timestamp.tzinfo is None:
        raise ValueError(f"{label} must be timezone-aware.")
    timestamp = timestamp.tz_convert("UTC")
    if (
        timestamp.hour
        or timestamp.minute
        or timestamp.second
        or timestamp.microsecond
        or timestamp.nanosecond
    ):
        raise ValueError(f"{label} must align to UTC midnight.")
    return timestamp


@dataclass(frozen=True)
class PartitionWindow:
    """One immutable half-open calendar partition."""

    name: str
    role: str
    start_utc: str
    end_exclusive_utc: str
    expected_calendar_buckets: int
    inspection_class: str
    genuinely_untouched: bool
    currently_open_authorized: bool

    def __post_init__(self):
        if not isinstance(self.name, str) or not self.name:
            raise ValueError("Partition name must be a nonempty string.")
        if not isinstance(self.role, str) or not self.role:
            raise ValueError("Partition role must be a nonempty string.")
        if not isinstance(self.inspection_class, str) or not self.inspection_class:
            raise ValueError("Partition inspection class must be nonempty.")
        if not isinstance(self.genuinely_untouched, bool):
            raise ValueError("Partition genuinely-untouched flag must be boolean.")
        if not isinstance(self.currently_open_authorized, bool):
            raise ValueError("Partition open-authorization flag must be boolean.")
        if (
            not isinstance(self.expected_calendar_buckets, int)
            or isinstance(self.expected_calendar_buckets, bool)
            or self.expected_calendar_buckets <= 0
        ):
            raise ValueError("Partition calendar bucket count must be positive.")

        start = _utc_midnight(self.start_utc, "Partition start")
        end = _utc_midnight(self.end_exclusive_utc, "Partition end")
        if end <= start:
            raise ValueError("Partition end must be after start.")
        actual_buckets = int((end - start) / DAILY_STEP)
        if start + actual_buckets * DAILY_STEP != end:
            raise ValueError("Partition boundaries must span complete UTC days.")
        if actual_buckets != self.expected_calendar_buckets:
            raise ValueError(
                "Partition calendar bucket count does not match its boundaries."
            )

    def contains(self, timestamp):
        value = _utc_midnight(timestamp, "Partition membership timestamp")
        return (
            _utc_midnight(self.start_utc, "Partition start")
            <= value
            < _utc_midnight(self.end_exclusive_utc, "Partition end")
        )

    def declaration(self):
        return asdict(self)


REFERENCE_WINDOWS = (
    PartitionWindow(
        name="DEVELOPMENT",
        role="MODEL_DEVELOPMENT",
        start_utc=RESEARCH_START_UTC,
        end_exclusive_utc=DEVELOPMENT_END_EXCLUSIVE_UTC,
        expected_calendar_buckets=1917,
        inspection_class="DEVELOPMENT_ONLY",
        genuinely_untouched=False,
        currently_open_authorized=False,
    ),
    PartitionWindow(
        name="CALIBRATION",
        role="PARAMETER_SELECTION_AND_FREEZE",
        start_utc=CALIBRATION_START_UTC,
        end_exclusive_utc=CALIBRATION_END_EXCLUSIVE_UTC,
        expected_calendar_buckets=365,
        inspection_class="INSPECTED_NOT_UNSEEN",
        genuinely_untouched=False,
        currently_open_authorized=False,
    ),
    PartitionWindow(
        name="EVALUATION",
        role="ONE_TIME_FINAL_EVALUATION",
        start_utc=EVALUATION_START_UTC,
        end_exclusive_utc=EVALUATION_END_EXCLUSIVE_UTC,
        expected_calendar_buckets=365,
        inspection_class="SEALED_UNTOUCHED",
        genuinely_untouched=True,
        currently_open_authorized=False,
    ),
)


class KrakenAIDrivenV2PartitionContract:
    """Exact reference partition; constructor accepts no alternate identity."""

    def __init__(self):
        self._windows = REFERENCE_WINDOWS
        self._by_name = {window.name: window for window in self._windows}

    @property
    def windows(self):
        return tuple(self._windows)

    def _asset(self, asset):
        if not isinstance(asset, str):
            raise TypeError("Partition asset must be a string.")
        if asset not in ASSET_ORDER:
            raise ValueError(f"Unknown partition asset: {asset}.")
        return asset

    def window(self, partition):
        if not isinstance(partition, str):
            raise TypeError("Partition name must be a string.")
        try:
            return self._by_name[partition]
        except KeyError as exc:
            raise ValueError(f"Unknown partition: {partition}.") from exc

    def expected_index(self, asset, partition):
        asset = self._asset(asset)
        window = self.window(partition)
        start = _utc_midnight(window.start_utc, "Partition start")
        end = _utc_midnight(window.end_exclusive_utc, "Partition end")
        index = pd.date_range(
            start=start,
            end=end,
            freq="D",
            inclusive="left",
        )
        gaps = pd.DatetimeIndex(
            [
                _utc_midnight(gap, "Known gap")
                for gap in KNOWN_GAPS_UTC[asset]
                if start <= _utc_midnight(gap, "Known gap") < end
            ]
        )
        if len(gaps):
            index = index.drop(gaps)
        return index.copy()

    def validate_partition_index(self, asset, partition, index):
        asset = self._asset(asset)
        window = self.window(partition)
        if not isinstance(index, pd.DatetimeIndex):
            raise TypeError("Partition timestamps must use a DatetimeIndex.")
        if index.tz is None:
            raise ValueError("Partition timestamps must be timezone-aware.")
        if not index.is_monotonic_increasing:
            raise ValueError("Partition timestamps must increase.")
        if index.has_duplicates:
            raise ValueError("Partition timestamps must be unique.")

        normalized = index.tz_convert("UTC").copy()
        if any(
            timestamp.hour
            or timestamp.minute
            or timestamp.second
            or timestamp.microsecond
            or timestamp.nanosecond
            for timestamp in normalized
        ):
            raise ValueError("Partition timestamps must align to UTC midnight.")

        expected = self.expected_index(asset, window.name)
        if not normalized.equals(expected):
            missing = expected.difference(normalized)
            extra = normalized.difference(expected)
            raise ValueError(
                "Partition index does not match the exact expected asset/window "
                f"identity (missing={len(missing)}, extra={len(extra)})."
            )
        return normalized.copy()

    def materialize_segments(self, asset, partition, index):
        """Validate one already-authorized partition index and split its gaps."""

        validated = self.validate_partition_index(asset, partition, index)
        if len(validated) == 0:  # pragma: no cover - reference windows are nonempty
            return ()
        boundaries = [0]
        boundaries.extend(
            position
            for position, delta in enumerate(
                validated[1:] - validated[:-1], start=1
            )
            if delta != DAILY_STEP
        )
        boundaries.append(len(validated))
        return tuple(
            validated[start:end].copy()
            for start, end in zip(boundaries[:-1], boundaries[1:])
        )

    def _plan_payload(self):
        expected_rows = {
            asset: {
                partition: len(self.expected_index(asset, partition))
                for partition in PARTITION_ORDER
            }
            for asset in ASSET_ORDER
        }
        return {
            "schema_version": SCHEMA_VERSION,
            "partition_protocol_id": PARTITION_PROTOCOL_ID,
            "dataset_id": DATASET_ID,
            "dataset_manifest_sha256": DATASET_MANIFEST_SHA256,
            "asset_order": list(ASSET_ORDER),
            "partition_order": list(PARTITION_ORDER),
            "research_start_utc": RESEARCH_START_UTC,
            "research_end_exclusive_utc": EVALUATION_END_EXCLUSIVE_UTC,
            "windows": [window.declaration() for window in self._windows],
            "known_gaps_utc": {
                asset: list(KNOWN_GAPS_UTC[asset]) for asset in ASSET_ORDER
            },
            "expected_observed_rows": expected_rows,
            "v1_btc_episode_evidence_sha256": V1_BTC_EPISODE_EVIDENCE_SHA256,
            "v1_btc_episode_start_utc": INSPECTED_BTC_START_UTC,
            "v1_btc_episode_end_utc": INSPECTED_BTC_END_UTC,
            "v1_btc_episode_partition": "CALIBRATION",
            "v1_btc_episode_is_unseen": False,
            "boundary_selection_basis": "CALENDAR_ONLY_BEFORE_PERFORMANCE",
            "gap_policy": "PRESERVE_NO_TRADE_UNAVAILABLE_AND_SPLIT",
            "state_carry_across_partitions": False,
            "state_carry_across_gaps": False,
            "development_data_open_authorized": False,
            "calibration_data_open_authorized": False,
            "evaluation_data_open_authorized": False,
            "performance_evaluation_authorized": False,
        }

    def plan_sha256(self):
        canonical = json.dumps(
            self._plan_payload(),
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=True,
            allow_nan=False,
        ).encode("utf-8")
        return hashlib.sha256(canonical).hexdigest()

    def configuration(self):
        return {**self._plan_payload(), "plan_sha256": self.plan_sha256()}


REFERENCE_PARTITION_CONTRACT = KrakenAIDrivenV2PartitionContract()
