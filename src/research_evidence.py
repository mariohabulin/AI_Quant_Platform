"""Canonical serialization helpers for deterministic research evidence."""

import json

import numpy as np
import pandas as pd


def _json_default(value):
    """Normalize expected research scalar types without hiding bad evidence."""

    if value is pd.NaT:
        raise ValueError("Timestamp evidence must not be missing.")
    if isinstance(value, (pd.Timestamp, np.datetime64)):
        if pd.isna(value):
            raise ValueError("Timestamp evidence must not be missing.")
        return pd.Timestamp(value).isoformat()
    if isinstance(value, (pd.Timedelta, np.timedelta64)):
        if pd.isna(value):
            raise ValueError("Timedelta evidence must not be missing.")
        return pd.Timedelta(value).isoformat()
    if isinstance(value, np.ndarray):
        return value.tolist()
    if isinstance(value, np.generic):
        return value.item()
    raise TypeError(
        f"Object of type {value.__class__.__name__} is not JSON serializable"
    )


def canonical_json_bytes(payload):
    """Return deterministic UTF-8 JSON bytes and reject non-finite evidence."""

    text = json.dumps(
        payload,
        allow_nan=False,
        default=_json_default,
        ensure_ascii=True,
        separators=(",", ":"),
        sort_keys=True,
    )
    return f"{text}\n".encode("utf-8")
