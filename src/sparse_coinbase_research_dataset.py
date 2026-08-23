"""Gap-aware native Coinbase research data with explicit missing buckets.

This module is deliberately separate from the continuous-grid candidate-v1
dataset boundary. It accepts only provider-observed candles, records every
missing UTC bucket and never creates a synthetic market row.
"""

import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd

try:
    from coinbase_research_dataset import (
        CANONICAL_COLUMN_ORDER,
        MAX_CANDLES_PER_REQUEST,
        CoinbaseResearchDatasetBuilder,
        CoinbaseResearchDatasetContract,
        LockedCoinbaseResearchDataset,
        dataset_canonicalization_metadata,
        dataset_source_metadata,
    )
except ImportError:  # package import when src is not placed directly on sys.path
    from src.coinbase_research_dataset import (
        CANONICAL_COLUMN_ORDER,
        MAX_CANDLES_PER_REQUEST,
        CoinbaseResearchDatasetBuilder,
        CoinbaseResearchDatasetContract,
        LockedCoinbaseResearchDataset,
        dataset_canonicalization_metadata,
        dataset_source_metadata,
    )


SPARSE_DATASET_MANIFEST_SCHEMA_VERSION = "2.0"
SPARSE_NATIVE_GAP_POLICY = {
    "mode": "PROVIDER_OBSERVED_WITH_EXPLICIT_GAPS",
    "max_missing_buckets_per_product": 50,
    "max_consecutive_missing_buckets": 24,
    "missing_candle_recovery_passes": 2,
    "max_missing_candle_recovery_requests": 100,
    "synthetic_candles_allowed": False,
    "interpolation_allowed": False,
    "forward_fill_allowed": False,
    "resampling_allowed": False,
    "calendar_windowing_required": True,
}


def _timestamp_text(timestamp):
    return timestamp.strftime("%Y-%m-%dT%H:%M:%SZ")


def _max_consecutive_missing(missing, start, step):
    if not len(missing):
        return 0
    positions = sorted(int((timestamp - start) / step) for timestamp in missing)
    maximum = 1
    current = 1
    for previous, position in zip(positions, positions[1:]):
        if position == previous + 1:
            current += 1
            maximum = max(maximum, current)
        else:
            current = 1
    return maximum


class SparseCoinbaseResearchDatasetBuilder(CoinbaseResearchDatasetBuilder):
    """Build a one-shot provider-observed dataset with bounded explicit gaps."""

    def __init__(
        self,
        contract,
        request_fn=None,
        timeout_seconds=15.0,
        request_pause_seconds=0.25,
        max_attempts=3,
        retry_backoff_seconds=1.0,
        sleep_fn=None,
    ):
        kwargs = {
            "contract": contract,
            "request_fn": request_fn,
            "timeout_seconds": timeout_seconds,
            "request_pause_seconds": request_pause_seconds,
            "max_attempts": max_attempts,
            "missing_candle_recovery_passes": SPARSE_NATIVE_GAP_POLICY[
                "missing_candle_recovery_passes"
            ],
            "max_missing_candle_recovery_requests": SPARSE_NATIVE_GAP_POLICY[
                "max_missing_candle_recovery_requests"
            ],
            "retry_backoff_seconds": retry_backoff_seconds,
        }
        if sleep_fn is not None:
            kwargs["sleep_fn"] = sleep_fn
        super().__init__(**kwargs)

    def _fetch_observed_product(self, product_id):
        product_id = str(product_id).strip().upper()
        if product_id not in self.contract.products:
            raise ValueError("Product is outside the frozen dataset contract.")

        start = self.contract.start_timestamp
        end = self.contract.end_timestamp
        step = pd.Timedelta(seconds=self.contract.granularity_seconds)
        chunk_span = step * (MAX_CANDLES_PER_REQUEST - 1)
        bars = {}
        cursor = start
        while cursor < end:
            chunk_end = min(cursor + chunk_span, end)
            payload = self._request(product_id, cursor, chunk_end)
            self._merge_payload(bars, payload, product_id, start, end)
            cursor = chunk_end
            if cursor < end and self.request_pause_seconds:
                self.sleep_fn(self.request_pause_seconds)

        expected = pd.date_range(start, end, freq=step, inclusive="left")
        observed = pd.DatetimeIndex(sorted(bars))
        missing = expected.difference(observed)
        recovery_status = "not_needed"
        if len(missing):
            missing, recovery_status = self._recover_missing_candles(
                product_id,
                bars,
                expected,
                missing,
                step,
            )
            observed = pd.DatetimeIndex(sorted(bars))

        extra = observed.difference(expected)
        if len(extra):
            raise RuntimeError(
                f"Sparse {product_id} dataset contains {len(extra)} extra buckets."
            )

        maximum_missing = SPARSE_NATIVE_GAP_POLICY[
            "max_missing_buckets_per_product"
        ]
        if len(missing) > maximum_missing:
            raise RuntimeError(
                f"Sparse {product_id} dataset exceeds missing bucket limit: "
                f"missing={len(missing)} limit={maximum_missing}."
            )
        maximum_consecutive = _max_consecutive_missing(missing, start, step)
        consecutive_limit = SPARSE_NATIVE_GAP_POLICY[
            "max_consecutive_missing_buckets"
        ]
        if maximum_consecutive > consecutive_limit:
            raise RuntimeError(
                f"Sparse {product_id} dataset exceeds consecutive missing bucket "
                f"limit: observed={maximum_consecutive} limit={consecutive_limit}."
            )
        if len(missing) and recovery_status != "exhausted_2_passes":
            raise RuntimeError(
                f"Sparse {product_id} gaps were not exhausted through the frozen "
                "exact-bucket recovery policy."
            )
        if not len(observed):
            raise RuntimeError(
                f"Sparse {product_id} dataset contains no observed candles."
            )

        frame = pd.DataFrame(
            [bars[timestamp] for timestamp in observed],
            index=observed,
            columns=["Open", "High", "Low", "Close", "Volume"],
        )
        frame.index.name = "Timestamp"
        evidence = {
            "expected_rows": len(expected),
            "rows": len(frame),
            "missing_rows": len(missing),
            "missing_timestamps": [_timestamp_text(item) for item in missing],
            "max_consecutive_missing_buckets": maximum_consecutive,
            "recovery_status": recovery_status,
        }
        return frame, evidence

    @staticmethod
    def _staging_directory(output_directory):
        return output_directory.with_name(f".{output_directory.name}.staging")

    def build(self, output_directory, overwrite=False):
        if not isinstance(overwrite, bool):
            raise TypeError("Overwrite must be a boolean.")
        if overwrite:
            raise ValueError(
                "Sparse dataset evidence is one-shot and cannot overwrite."
            )

        output_directory = Path(output_directory)
        if output_directory.exists() and any(output_directory.iterdir()):
            raise FileExistsError(
                f"Refusing to overwrite existing directory: {output_directory}"
            )
        staging_directory = self._staging_directory(output_directory)
        if staging_directory.exists():
            raise FileExistsError(
                f"Sparse dataset staging exists: {staging_directory}"
            )

        prepared = {}
        for product_id in self.contract.products:
            frame, gap_evidence = self._fetch_observed_product(product_id)
            payload = self._canonical_csv_bytes(frame)
            filename = self._filename(product_id)
            prepared[product_id] = {
                "payload": payload,
                "evidence": {
                    "file": filename,
                    "sha256": hashlib.sha256(payload).hexdigest(),
                    "first_timestamp": _timestamp_text(frame.index[0]),
                    "last_timestamp": _timestamp_text(frame.index[-1]),
                    **gap_evidence,
                },
            }

        assets = {
            product_id: item["evidence"]
            for product_id, item in sorted(prepared.items())
        }
        manifest = {
            "schema_version": SPARSE_DATASET_MANIFEST_SCHEMA_VERSION,
            "contract": self.contract.as_dict(),
            "source": dataset_source_metadata(),
            "canonicalization": dataset_canonicalization_metadata(),
            "gap_policy": dict(SPARSE_NATIVE_GAP_POLICY),
            "assets": assets,
        }
        manifest_bytes = (
            json.dumps(manifest, indent=2, sort_keys=True) + "\n"
        ).encode("utf-8")
        manifest_sha256 = hashlib.sha256(manifest_bytes).hexdigest()
        checksum_bytes = f"{manifest_sha256}  manifest.json\n".encode("ascii")

        staging_directory.parent.mkdir(parents=True, exist_ok=True)
        staging_directory.mkdir(exist_ok=False)
        for product_id, item in sorted(prepared.items()):
            self._write_new(
                staging_directory / item["evidence"]["file"],
                item["payload"],
                overwrite=False,
            )
        self._write_new(
            staging_directory / "manifest.json",
            manifest_bytes,
            overwrite=False,
        )
        self._write_new(
            staging_directory / "manifest.sha256",
            checksum_bytes,
            overwrite=False,
        )

        if output_directory.exists():
            output_directory.rmdir()
        staging_directory.rename(output_directory)
        return {
            "manifest_path": output_directory / "manifest.json",
            "manifest_sha256": manifest_sha256,
            "checksum_path": output_directory / "manifest.sha256",
            "assets": assets,
        }


class SparseCoinbaseResearchDatasetLock:
    """Revalidate sparse canonical bytes and every explicit missing bucket."""

    def __init__(self, contract):
        if not isinstance(contract, CoinbaseResearchDatasetContract):
            raise TypeError("Contract must be a CoinbaseResearchDatasetContract.")
        self.contract = contract

    @staticmethod
    def _sha256(path):
        return hashlib.sha256(Path(path).read_bytes()).hexdigest()

    def _load_manifest(self, manifest_path):
        manifest_path = Path(manifest_path)
        manifest_bytes = manifest_path.read_bytes()
        manifest_sha256 = hashlib.sha256(manifest_bytes).hexdigest()
        try:
            manifest = json.loads(manifest_bytes.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise ValueError("Sparse dataset manifest is not valid JSON.") from exc
        canonical = (
            json.dumps(manifest, indent=2, sort_keys=True) + "\n"
        ).encode("utf-8")
        if canonical != manifest_bytes:
            raise ValueError("Sparse dataset manifest is not canonical JSON.")
        if set(manifest) != {
            "schema_version",
            "contract",
            "source",
            "canonicalization",
            "gap_policy",
            "assets",
        }:
            raise ValueError("Sparse dataset manifest fields are invalid.")
        if manifest["schema_version"] != SPARSE_DATASET_MANIFEST_SCHEMA_VERSION:
            raise ValueError("Sparse dataset manifest schema version is invalid.")
        if manifest["contract"] != self.contract.as_dict():
            raise ValueError("Sparse dataset manifest contract is invalid.")
        if manifest["source"] != dataset_source_metadata():
            raise ValueError("Sparse dataset source contract is invalid.")
        if manifest["canonicalization"] != dataset_canonicalization_metadata():
            raise ValueError("Sparse dataset canonicalization is invalid.")
        if manifest["gap_policy"] != SPARSE_NATIVE_GAP_POLICY:
            raise ValueError("Sparse dataset gap policy is invalid.")
        if not isinstance(manifest["assets"], dict) or tuple(
            sorted(manifest["assets"])
        ) != self.contract.products:
            raise ValueError("Sparse dataset asset scope is invalid.")

        checksum_path = manifest_path.with_name("manifest.sha256")
        expected = f"{manifest_sha256}  manifest.json\n".encode("ascii")
        if not checksum_path.is_file() or checksum_path.read_bytes() != expected:
            raise ValueError("Sparse dataset manifest sidecar is invalid.")
        return manifest, manifest_sha256

    def _load_asset(self, manifest_path, product_id, evidence):
        required = {
            "file",
            "sha256",
            "first_timestamp",
            "last_timestamp",
            "expected_rows",
            "rows",
            "missing_rows",
            "missing_timestamps",
            "max_consecutive_missing_buckets",
            "recovery_status",
        }
        if not isinstance(evidence, dict) or set(evidence) != required:
            raise ValueError(f"Sparse dataset evidence is invalid for {product_id}.")
        filename = evidence["file"]
        if not isinstance(filename, str) or Path(filename).name != filename:
            raise ValueError("Sparse dataset file names must be basenames.")
        path = Path(manifest_path).parent / filename
        if not path.is_file():
            raise ValueError(f"Sparse dataset file is missing for {product_id}.")
        if self._sha256(path) != evidence["sha256"]:
            raise ValueError(f"Sparse dataset SHA-256 mismatch for {product_id}.")

        frame = pd.read_csv(path)
        if list(frame.columns) != list(CANONICAL_COLUMN_ORDER):
            raise ValueError(f"Sparse dataset columns are invalid for {product_id}.")
        for key in (
            "expected_rows",
            "rows",
            "missing_rows",
            "max_consecutive_missing_buckets",
        ):
            if not isinstance(evidence[key], int) or isinstance(
                evidence[key], bool
            ):
                raise ValueError(
                    f"Sparse dataset integer evidence is invalid for {product_id}."
                )
        if len(frame) != evidence["rows"]:
            raise ValueError(f"Sparse dataset row count mismatch for {product_id}.")
        if frame.empty:
            raise ValueError(f"Sparse dataset is empty for {product_id}.")

        timestamps = pd.DatetimeIndex(
            pd.to_datetime(frame.pop("Timestamp"), utc=True, errors="raise")
        )
        if not timestamps.is_monotonic_increasing or timestamps.has_duplicates:
            raise ValueError(f"Sparse dataset timestamps are invalid for {product_id}.")
        expected = pd.date_range(
            self.contract.start_timestamp,
            self.contract.end_timestamp,
            freq=pd.Timedelta(seconds=self.contract.granularity_seconds),
            inclusive="left",
        )
        extra = timestamps.difference(expected)
        missing = expected.difference(timestamps)
        if len(extra):
            raise ValueError(f"Sparse dataset contains extra rows for {product_id}.")
        expected_missing = [_timestamp_text(item) for item in missing]
        if evidence["missing_timestamps"] != expected_missing:
            raise ValueError(
                "Sparse dataset missing timestamp evidence is invalid for "
                f"{product_id}."
            )
        if evidence["expected_rows"] != len(expected):
            raise ValueError(
                f"Sparse expected row evidence is invalid for {product_id}."
            )
        if evidence["missing_rows"] != len(missing):
            raise ValueError(
                f"Sparse missing row evidence is invalid for {product_id}."
            )
        if len(frame) + len(missing) != len(expected):
            raise ValueError(f"Sparse dataset accounting is invalid for {product_id}.")
        step = pd.Timedelta(seconds=self.contract.granularity_seconds)
        maximum_consecutive = _max_consecutive_missing(
            missing,
            self.contract.start_timestamp,
            step,
        )
        if evidence["max_consecutive_missing_buckets"] != maximum_consecutive:
            raise ValueError(
                f"Sparse consecutive gap evidence is invalid for {product_id}."
            )
        if len(missing) > SPARSE_NATIVE_GAP_POLICY[
            "max_missing_buckets_per_product"
        ] or maximum_consecutive > SPARSE_NATIVE_GAP_POLICY[
            "max_consecutive_missing_buckets"
        ]:
            raise ValueError(f"Sparse dataset gap limits failed for {product_id}.")
        allowed_recovery = (
            {"exhausted_2_passes"}
            if len(missing)
            else {"not_needed", "recovered_pass_1", "recovered_pass_2"}
        )
        if evidence["recovery_status"] not in allowed_recovery:
            raise ValueError(f"Sparse recovery evidence is invalid for {product_id}.")
        if evidence["first_timestamp"] != _timestamp_text(timestamps[0]):
            raise ValueError(f"Sparse first timestamp is invalid for {product_id}.")
        if evidence["last_timestamp"] != _timestamp_text(timestamps[-1]):
            raise ValueError(f"Sparse last timestamp is invalid for {product_id}.")

        try:
            frame = frame.apply(pd.to_numeric, errors="raise")
        except (TypeError, ValueError) as exc:
            raise ValueError(f"Sparse values are invalid for {product_id}.") from exc
        values = frame[["Open", "High", "Low", "Close", "Volume"]].to_numpy()
        if not np.isfinite(values).all():
            raise ValueError(f"Sparse values must be finite for {product_id}.")
        if (frame[["Open", "High", "Low", "Close"]] <= 0.0).any().any():
            raise ValueError(f"Sparse OHLC values must be positive for {product_id}.")
        if (frame["Volume"] < 0.0).any():
            raise ValueError(f"Sparse volume cannot be negative for {product_id}.")
        price_maximum = frame[["Open", "Low", "Close"]].max(axis=1)
        price_minimum = frame[["Open", "High", "Close"]].min(axis=1)
        if (frame["High"] < price_maximum).any() or (
            frame["Low"] > price_minimum
        ).any():
            raise ValueError(f"Sparse OHLC geometry is invalid for {product_id}.")
        frame.index = timestamps
        frame.index.name = "Timestamp"
        return frame

    def lock(self, manifest_path):
        manifest, manifest_sha256 = self._load_manifest(manifest_path)
        assets = {
            product_id: self._load_asset(
                manifest_path,
                product_id,
                manifest["assets"][product_id],
            )
            for product_id in self.contract.products
        }
        return LockedCoinbaseResearchDataset(
            contract=self.contract,
            manifest=manifest,
            manifest_sha256=manifest_sha256,
            assets=assets,
        )
