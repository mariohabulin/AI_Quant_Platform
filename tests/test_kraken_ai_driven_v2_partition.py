import json
import os
import sys
from dataclasses import replace

import pandas as pd
import pytest

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src")))

from kraken_ai_driven_v2_partition import (
    ASSET_ORDER,
    DATASET_ID,
    DATASET_MANIFEST_SHA256,
    EVALUATION_END_EXCLUSIVE_UTC,
    EVALUATION_START_UTC,
    INSPECTED_BTC_END_UTC,
    INSPECTED_BTC_START_UTC,
    KNOWN_GAPS_UTC,
    PARTITION_ORDER,
    PARTITION_PROTOCOL_ID,
    REFERENCE_PARTITION_CONTRACT,
    RESEARCH_START_UTC,
    PartitionWindow,
    KrakenAIDrivenV2PartitionContract,
)


def test_reference_partition_identity_and_plan_are_exact_and_deterministic():
    first = REFERENCE_PARTITION_CONTRACT.configuration()
    second = KrakenAIDrivenV2PartitionContract().configuration()

    assert first == second
    assert first["partition_protocol_id"] == PARTITION_PROTOCOL_ID
    assert first["dataset_id"] == DATASET_ID
    assert first["dataset_manifest_sha256"] == DATASET_MANIFEST_SHA256
    assert first["asset_order"] == list(ASSET_ORDER)
    assert first["partition_order"] == list(PARTITION_ORDER)
    assert first["plan_sha256"] == REFERENCE_PARTITION_CONTRACT.plan_sha256()
    assert len(first["plan_sha256"]) == 64
    assert json.dumps(first, sort_keys=True, allow_nan=False)


def test_calendar_boundaries_are_contiguous_nonoverlapping_and_cover_lock():
    windows = REFERENCE_PARTITION_CONTRACT.windows

    assert [window.name for window in windows] == list(PARTITION_ORDER)
    assert windows[0].start_utc == RESEARCH_START_UTC
    assert windows[0].end_exclusive_utc == windows[1].start_utc
    assert windows[1].end_exclusive_utc == windows[2].start_utc
    assert windows[2].start_utc == EVALUATION_START_UTC
    assert windows[2].end_exclusive_utc == EVALUATION_END_EXCLUSIVE_UTC
    assert [window.expected_calendar_buckets for window in windows] == [1917, 365, 365]
    assert sum(window.expected_calendar_buckets for window in windows) == 2647


def test_partition_roles_and_access_boundaries_are_explicit():
    development = REFERENCE_PARTITION_CONTRACT.window("DEVELOPMENT")
    calibration = REFERENCE_PARTITION_CONTRACT.window("CALIBRATION")
    evaluation = REFERENCE_PARTITION_CONTRACT.window("EVALUATION")

    assert development.role == "MODEL_DEVELOPMENT"
    assert development.inspection_class == "DEVELOPMENT_ONLY"
    assert development.genuinely_untouched is False
    assert development.currently_open_authorized is False
    assert calibration.role == "PARAMETER_SELECTION_AND_FREEZE"
    assert calibration.inspection_class == "INSPECTED_NOT_UNSEEN"
    assert calibration.genuinely_untouched is False
    assert calibration.currently_open_authorized is False
    assert evaluation.role == "ONE_TIME_FINAL_EVALUATION"
    assert evaluation.inspection_class == "SEALED_UNTOUCHED"
    assert evaluation.genuinely_untouched is True
    assert evaluation.currently_open_authorized is False


@pytest.mark.parametrize(
    "asset,expected_counts",
    [
        ("BTC-USD", [1916, 365, 365]),
        ("ETH-USD", [1917, 365, 365]),
        ("XRP-USD", [1915, 365, 365]),
    ],
)
def test_exact_observed_counts_reconcile_by_asset(asset, expected_counts):
    counts = [
        len(REFERENCE_PARTITION_CONTRACT.expected_index(asset, name))
        for name in PARTITION_ORDER
    ]

    assert counts == expected_counts
    assert sum(counts) == {
        "BTC-USD": 2646,
        "ETH-USD": 2647,
        "XRP-USD": 2645,
    }[asset]


def test_all_known_provider_gaps_are_preserved_inside_development():
    for asset, gaps in KNOWN_GAPS_UTC.items():
        development = REFERENCE_PARTITION_CONTRACT.expected_index(
            asset, "DEVELOPMENT"
        )
        for gap in gaps:
            timestamp = pd.Timestamp(gap)
            assert timestamp < pd.Timestamp("2024-04-01T00:00:00Z")
            assert timestamp not in development


def test_inspected_btc_episode_is_calibration_and_never_unseen_evaluation():
    inspected_start = pd.Timestamp(INSPECTED_BTC_START_UTC)
    inspected_end = pd.Timestamp(INSPECTED_BTC_END_UTC)
    calibration = REFERENCE_PARTITION_CONTRACT.window("CALIBRATION")
    evaluation = REFERENCE_PARTITION_CONTRACT.window("EVALUATION")

    assert calibration.contains(inspected_start)
    assert calibration.contains(inspected_end)
    assert not evaluation.contains(inspected_start)
    assert not evaluation.contains(inspected_end)
    assert evaluation.genuinely_untouched is True


@pytest.mark.parametrize(
    "asset,partition,segment_lengths",
    [
        ("BTC-USD", "DEVELOPMENT", [1916]),
        ("ETH-USD", "DEVELOPMENT", [1917]),
        ("XRP-USD", "DEVELOPMENT", [1226, 689]),
        ("BTC-USD", "CALIBRATION", [365]),
        ("ETH-USD", "EVALUATION", [365]),
    ],
)
def test_materialized_segments_split_only_at_recorded_gaps(
    asset, partition, segment_lengths
):
    source = REFERENCE_PARTITION_CONTRACT.expected_index(asset, partition)
    segments = REFERENCE_PARTITION_CONTRACT.materialize_segments(
        asset, partition, source
    )

    assert [len(segment) for segment in segments] == segment_lengths
    assert sum(len(segment) for segment in segments) == len(source)
    for segment in segments:
        if len(segment) > 1:
            assert all(
                delta == pd.Timedelta(days=1)
                for delta in segment[1:] - segment[:-1]
            )


def test_validation_and_segmentation_do_not_mutate_or_alias_source_index():
    source = REFERENCE_PARTITION_CONTRACT.expected_index("XRP-USD", "DEVELOPMENT")
    before = source.copy()

    validated = REFERENCE_PARTITION_CONTRACT.validate_partition_index(
        "XRP-USD", "DEVELOPMENT", source
    )
    segments = REFERENCE_PARTITION_CONTRACT.materialize_segments(
        "XRP-USD", "DEVELOPMENT", source
    )

    pd.testing.assert_index_equal(source, before)
    pd.testing.assert_index_equal(validated, before)
    assert validated is not source
    assert all(segment is not source for segment in segments)


@pytest.mark.parametrize(
    "asset,partition,index_factory,error",
    [
        (
            "BTC-USD",
            "DEVELOPMENT",
            lambda expected: pd.RangeIndex(len(expected)),
            "DatetimeIndex",
        ),
        (
            "BTC-USD",
            "DEVELOPMENT",
            lambda expected: expected.tz_localize(None),
            "timezone-aware",
        ),
        (
            "BTC-USD",
            "DEVELOPMENT",
            lambda expected: expected[::-1],
            "increase",
        ),
        (
            "BTC-USD",
            "DEVELOPMENT",
            lambda expected: expected.append(expected[-1:]),
            "unique",
        ),
        (
            "BTC-USD",
            "DEVELOPMENT",
            lambda expected: expected + pd.Timedelta(hours=1),
            "UTC midnight",
        ),
        (
            "ETH-USD",
            "CALIBRATION",
            lambda expected: expected.delete(10),
            "exact expected",
        ),
        (
            "ETH-USD",
            "EVALUATION",
            lambda expected: expected.append(
                pd.DatetimeIndex([pd.Timestamp(EVALUATION_END_EXCLUSIVE_UTC)])
            ),
            "exact expected",
        ),
    ],
)
def test_partition_index_validation_fails_closed(
    asset, partition, index_factory, error
):
    expected = REFERENCE_PARTITION_CONTRACT.expected_index(asset, partition)

    with pytest.raises((TypeError, ValueError), match=error):
        REFERENCE_PARTITION_CONTRACT.validate_partition_index(
            asset, partition, index_factory(expected)
        )


@pytest.mark.parametrize(
    "asset,partition,error",
    [
        ("DOGE-USD", "DEVELOPMENT", "asset"),
        ("BTC-USD", "TRAIN", "partition"),
        (True, "DEVELOPMENT", "asset"),
    ],
)
def test_unknown_asset_or_partition_is_rejected(asset, partition, error):
    with pytest.raises((TypeError, ValueError), match=error):
        REFERENCE_PARTITION_CONTRACT.expected_index(asset, partition)


def test_reference_contract_cannot_be_reconfigured_under_same_identity():
    with pytest.raises(TypeError):
        KrakenAIDrivenV2PartitionContract(
            windows=(
                replace(
                    REFERENCE_PARTITION_CONTRACT.windows[0],
                    end_exclusive_utc="2024-05-01T00:00:00Z",
                    expected_calendar_buckets=1947,
                ),
            )
        )


@pytest.mark.parametrize(
    "kwargs,error",
    [
        ({"expected_calendar_buckets": 1}, "calendar bucket"),
        ({"start_utc": "2024-04-01"}, "timezone-aware"),
        ({"end_exclusive_utc": "2024-03-01T00:00:00Z"}, "after start"),
    ],
)
def test_partition_window_invariants_fail_closed(kwargs, error):
    valid = {
        "name": "CALIBRATION",
        "role": "PARAMETER_SELECTION_AND_FREEZE",
        "start_utc": "2024-04-01T00:00:00Z",
        "end_exclusive_utc": "2025-04-01T00:00:00Z",
        "expected_calendar_buckets": 365,
        "inspection_class": "INSPECTED_NOT_UNSEEN",
        "genuinely_untouched": False,
        "currently_open_authorized": False,
    }
    valid.update(kwargs)

    with pytest.raises(ValueError, match=error):
        PartitionWindow(**valid)


def test_contract_exposes_no_performance_or_execution_authority():
    payload = json.dumps(
        REFERENCE_PARTITION_CONTRACT.configuration(), sort_keys=True
    ).lower()

    for prohibited in (
        "pnl",
        "return",
        "sharpe",
        "drawdown",
        "win_rate",
        "real_order",
        "live_execution_authorized\": true",
    ):
        assert prohibited not in payload
    assert REFERENCE_PARTITION_CONTRACT.configuration()[
        "performance_evaluation_authorized"
    ] is False
    assert REFERENCE_PARTITION_CONTRACT.configuration()[
        "state_carry_across_partitions"
    ] is False
    assert REFERENCE_PARTITION_CONTRACT.configuration()[
        "state_carry_across_gaps"
    ] is False
