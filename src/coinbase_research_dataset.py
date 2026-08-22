"""Deterministic public Coinbase candle acquisition for offline research.

This module is deliberately separate from the live Coinbase adapter. It reads
public historical candles, validates a frozen continuous grid, writes canonical
CSV bytes, and produces a SHA-256 manifest. It cannot place orders.
"""

from dataclasses import asdict, dataclass
import argparse
import csv
import hashlib
import io
import json
import math
from pathlib import Path
import time

import numpy as np
import pandas as pd


COINBASE_EXCHANGE_CANDLES_URL = (
    "https://api.exchange.coinbase.com/products/{product_id}/candles"
)
COINBASE_CANDLES_DOCUMENTATION = (
    "https://docs.cdp.coinbase.com/api-reference/exchange-api/rest-api/"
    "products/get-product-candles"
)
COINBASE_FEES_DOCUMENTATION = (
    "https://help.coinbase.com/exchange/trading-and-funding/exchange-fees"
)
ALLOWED_GRANULARITIES = {60, 300, 900, 3600, 21600, 86400}
MAX_CANDLES_PER_REQUEST = 300
DATASET_MANIFEST_SCHEMA_VERSION = "1.0"
CANONICAL_COLUMN_ORDER = (
    "Timestamp",
    "Open",
    "High",
    "Low",
    "Close",
    "Volume",
)


def dataset_source_metadata():
    return {
        "provider": "Coinbase Exchange public REST",
        "endpoint": COINBASE_EXCHANGE_CANDLES_URL,
        "response_shape": ["time", "low", "high", "open", "close", "volume"],
        "candles_documentation": COINBASE_CANDLES_DOCUMENTATION,
        "fees_documentation": COINBASE_FEES_DOCUMENTATION,
        "max_candles_per_request": MAX_CANDLES_PER_REQUEST,
    }


def dataset_canonicalization_metadata():
    return {
        "encoding": "utf-8",
        "line_ending": "LF",
        "timestamp": "UTC ISO-8601 second precision",
        "float_format": ".17g",
        "column_order": list(CANONICAL_COLUMN_ORDER),
    }


def _utc_timestamp(value, name):
    timestamp = pd.Timestamp(value)
    if pd.isna(timestamp):
        raise ValueError(f"{name} must be a valid timestamp.")
    if timestamp.tzinfo is None:
        timestamp = timestamp.tz_localize("UTC")
    else:
        timestamp = timestamp.tz_convert("UTC")
    return timestamp


@dataclass(frozen=True)
class CoinbaseResearchDatasetContract:
    """Immutable acquisition and continuity contract for one dataset version."""

    dataset_id: str
    products: tuple
    granularity_seconds: int
    start: str
    end: str

    def __post_init__(self):
        if not isinstance(self.dataset_id, str) or not self.dataset_id.strip():
            raise ValueError("Dataset ID is required.")
        object.__setattr__(self, "dataset_id", self.dataset_id.strip())

        if not isinstance(self.products, tuple) or not self.products:
            raise ValueError("Products must be a non-empty tuple.")
        if any(not isinstance(product, str) for product in self.products):
            raise TypeError("Every product ID must be a string.")
        products = tuple(sorted(product.strip().upper() for product in self.products))
        if any(not product for product in products):
            raise ValueError("Every product ID is required.")
        if len(set(products)) != len(products):
            raise ValueError("Products must not contain duplicates.")
        object.__setattr__(self, "products", products)

        if self.granularity_seconds not in ALLOWED_GRANULARITIES:
            raise ValueError("Unsupported Coinbase candle granularity.")

        start = _utc_timestamp(self.start, "Dataset start")
        end = _utc_timestamp(self.end, "Dataset end")
        if end <= start:
            raise ValueError("Dataset end must be after start.")
        step = pd.Timedelta(seconds=self.granularity_seconds)
        if start.value % step.value or end.value % step.value:
            raise ValueError("Dataset boundaries must align to candle granularity.")
        object.__setattr__(self, "start", start.strftime("%Y-%m-%dT%H:%M:%SZ"))
        object.__setattr__(self, "end", end.strftime("%Y-%m-%dT%H:%M:%SZ"))

    @property
    def start_timestamp(self):
        return _utc_timestamp(self.start, "Dataset start")

    @property
    def end_timestamp(self):
        return _utc_timestamp(self.end, "Dataset end")

    @property
    def expected_rows_per_product(self):
        duration = self.end_timestamp - self.start_timestamp
        return int(duration / pd.Timedelta(seconds=self.granularity_seconds))

    @property
    def timeframe(self):
        labels = {
            60: "1m",
            300: "5m",
            900: "15m",
            3600: "1h",
            21600: "6h",
            86400: "1d",
        }
        return labels[self.granularity_seconds]

    def as_dict(self):
        result = asdict(self)
        result["products"] = list(self.products)
        result["timeframe"] = self.timeframe
        result["expected_rows_per_product"] = self.expected_rows_per_product
        result["range_semantics"] = "start_inclusive_end_exclusive"
        return result


FIRST_CANDIDATE_DATASET_CONTRACT = CoinbaseResearchDatasetContract(
    dataset_id="coinbase-exchange-btc-eth-native-6h-20190101-20260801-v1",
    products=("BTC-USD", "ETH-USD"),
    granularity_seconds=21600,
    start="2019-01-01T00:00:00Z",
    end="2026-08-01T00:00:00Z",
)


class CoinbaseResearchDatasetBuilder:
    """Download, validate and hash one frozen public-candle dataset."""

    def __init__(
        self,
        contract=FIRST_CANDIDATE_DATASET_CONTRACT,
        request_fn=None,
        timeout_seconds=15.0,
        request_pause_seconds=0.25,
        max_attempts=3,
        retry_backoff_seconds=1.0,
        sleep_fn=time.sleep,
    ):
        if not isinstance(contract, CoinbaseResearchDatasetContract):
            raise TypeError("Contract must be a CoinbaseResearchDatasetContract.")
        if not isinstance(max_attempts, int) or isinstance(max_attempts, bool):
            raise TypeError("Maximum attempts must be an integer.")
        if max_attempts <= 0:
            raise ValueError("Maximum attempts must be positive.")
        for value, name in (
            (timeout_seconds, "Timeout"),
            (request_pause_seconds, "Request pause"),
            (retry_backoff_seconds, "Retry backoff"),
        ):
            if not isinstance(value, (int, float)) or isinstance(value, bool):
                raise TypeError(f"{name} must be a number.")
            if float(value) < 0.0 or (name == "Timeout" and float(value) == 0.0):
                raise ValueError(f"{name} is invalid.")
        self.contract = contract
        self.request_fn = request_fn
        self.timeout_seconds = float(timeout_seconds)
        self.request_pause_seconds = float(request_pause_seconds)
        self.max_attempts = max_attempts
        self.retry_backoff_seconds = float(retry_backoff_seconds)
        self.sleep_fn = sleep_fn

    @staticmethod
    def _request_timestamp(timestamp):
        return timestamp.strftime("%Y-%m-%dT%H:%M:%SZ")

    def _request(self, product_id, start, end):
        if self.request_fn is None:
            import requests

            request_fn = requests.get
        else:
            request_fn = self.request_fn
        url = COINBASE_EXCHANGE_CANDLES_URL.format(product_id=product_id)
        params = {
            "start": self._request_timestamp(start),
            "end": self._request_timestamp(end),
            "granularity": self.contract.granularity_seconds,
        }
        last_error = None
        for attempt in range(1, self.max_attempts + 1):
            try:
                response = request_fn(
                    url,
                    params=params,
                    timeout=self.timeout_seconds,
                )
                raise_for_status = getattr(response, "raise_for_status", None)
                if callable(raise_for_status):
                    raise_for_status()
                payload = response.json() if hasattr(response, "json") else response
                if not isinstance(payload, list):
                    raise RuntimeError("Coinbase candle response must be a list.")
                return payload
            except Exception as exc:
                last_error = exc
                if attempt < self.max_attempts:
                    self.sleep_fn(self.retry_backoff_seconds * attempt)
        raise RuntimeError(
            f"Coinbase candle request failed after {self.max_attempts} attempts."
        ) from last_error

    def _parse_row(self, row):
        if not isinstance(row, (list, tuple)) or len(row) < 6:
            raise RuntimeError("Coinbase candle row is invalid.")
        try:
            timestamp = pd.Timestamp(int(row[0]), unit="s", tz="UTC")
            low, high, open_, close, volume = map(float, row[1:6])
        except (TypeError, ValueError, OverflowError) as exc:
            raise RuntimeError("Coinbase candle row contains invalid values.") from exc
        values = (open_, high, low, close, volume)
        if not all(math.isfinite(value) for value in values):
            raise RuntimeError("Coinbase candle values must be finite.")
        if any(value <= 0.0 for value in (open_, high, low, close)):
            raise RuntimeError("Coinbase OHLC values must be positive.")
        if volume < 0.0:
            raise RuntimeError("Coinbase volume cannot be negative.")
        if high < max(open_, low, close) or low > min(open_, high, close):
            raise RuntimeError("Coinbase candle price geometry is invalid.")
        step = pd.Timedelta(seconds=self.contract.granularity_seconds)
        if timestamp.value % step.value:
            raise RuntimeError("Coinbase candle timestamp is not grid-aligned.")
        return timestamp, (open_, high, low, close, volume)

    def fetch_product(self, product_id):
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
            for raw_row in payload:
                timestamp, values = self._parse_row(raw_row)
                if not start <= timestamp < end:
                    continue
                existing = bars.get(timestamp)
                if existing is not None and existing != values:
                    raise RuntimeError(
                        f"Conflicting duplicate candle for {product_id} at {timestamp}."
                    )
                bars[timestamp] = values
            cursor = chunk_end
            if cursor < end and self.request_pause_seconds:
                self.sleep_fn(self.request_pause_seconds)

        expected = pd.date_range(start, end, freq=step, inclusive="left")
        observed = pd.DatetimeIndex(sorted(bars))
        missing = expected.difference(observed)
        extra = observed.difference(expected)
        if len(missing) or len(extra):
            raise RuntimeError(
                f"Incomplete {product_id} candle grid: missing={len(missing)} "
                f"extra={len(extra)}."
            )
        frame = pd.DataFrame(
            [bars[timestamp] for timestamp in expected],
            index=expected,
            columns=["Open", "High", "Low", "Close", "Volume"],
        )
        frame.index.name = "Timestamp"
        return frame

    @staticmethod
    def _canonical_csv_bytes(frame):
        output = io.StringIO(newline="")
        writer = csv.writer(output, lineterminator="\n")
        writer.writerow(["Timestamp", "Open", "High", "Low", "Close", "Volume"])
        for timestamp, row in frame.iterrows():
            writer.writerow(
                [
                    timestamp.strftime("%Y-%m-%dT%H:%M:%SZ"),
                    *(format(float(row[column]), ".17g") for column in (
                        "Open", "High", "Low", "Close", "Volume"
                    )),
                ]
            )
        return output.getvalue().encode("utf-8")

    def _filename(self, product_id):
        start = self.contract.start_timestamp.strftime("%Y%m%d")
        end = self.contract.end_timestamp.strftime("%Y%m%d")
        product = product_id.lower().replace("-", "_")
        return f"{product}_{self.contract.timeframe}_{start}_{end}.csv"

    @staticmethod
    def _write_new(path, payload, overwrite):
        if path.exists() and not overwrite:
            raise FileExistsError(f"Refusing to overwrite existing file: {path}")
        temporary = path.with_name(path.name + ".tmp")
        temporary.write_bytes(payload)
        temporary.replace(path)

    def build(self, output_directory, overwrite=False):
        if not isinstance(overwrite, bool):
            raise TypeError("Overwrite must be a boolean.")
        output_directory = Path(output_directory)
        output_directory.mkdir(parents=True, exist_ok=True)
        assets = {}
        for product_id in self.contract.products:
            frame = self.fetch_product(product_id)
            payload = self._canonical_csv_bytes(frame)
            filename = self._filename(product_id)
            path = output_directory / filename
            self._write_new(path, payload, overwrite)
            assets[product_id] = {
                "file": filename,
                "sha256": hashlib.sha256(payload).hexdigest(),
                "rows": len(frame),
                "first_timestamp": frame.index[0].strftime("%Y-%m-%dT%H:%M:%SZ"),
                "last_timestamp": frame.index[-1].strftime("%Y-%m-%dT%H:%M:%SZ"),
            }

        manifest = {
            "schema_version": DATASET_MANIFEST_SCHEMA_VERSION,
            "contract": self.contract.as_dict(),
            "source": dataset_source_metadata(),
            "canonicalization": dataset_canonicalization_metadata(),
            "assets": assets,
        }
        manifest_bytes = (
            json.dumps(manifest, indent=2, sort_keys=True) + "\n"
        ).encode("utf-8")
        manifest_path = output_directory / "manifest.json"
        self._write_new(manifest_path, manifest_bytes, overwrite)
        manifest_sha256 = hashlib.sha256(manifest_bytes).hexdigest()
        checksum_path = output_directory / "manifest.sha256"
        checksum_bytes = f"{manifest_sha256}  manifest.json\n".encode("ascii")
        self._write_new(checksum_path, checksum_bytes, overwrite)
        return {
            "manifest_path": manifest_path,
            "manifest_sha256": manifest_sha256,
            "checksum_path": checksum_path,
            "assets": assets,
        }


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="Build the frozen first-candidate Coinbase 6h research dataset."
    )
    parser.add_argument("--output", required=True)
    parser.add_argument("--overwrite", action="store_true")
    args = parser.parse_args(argv)
    result = CoinbaseResearchDatasetBuilder().build(
        args.output,
        overwrite=args.overwrite,
    )
    print(f"dataset_status=LOCKED manifest={result['manifest_path']}")
    print(f"manifest_sha256={result['manifest_sha256']}")
    for product_id, evidence in sorted(result["assets"].items()):
        print(
            f"{product_id} rows={evidence['rows']} "
            f"sha256={evidence['sha256']} file={evidence['file']}"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
