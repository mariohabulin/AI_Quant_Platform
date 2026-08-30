"""One-shot development-only runner for Kraken AI-driven v2 reference A."""

import argparse
from collections import Counter
import csv
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
import hashlib
import json
from pathlib import Path

import pandas as pd

try:
    from kraken_ai_driven_v2_features import REQUIRED_OHLCV_COLUMNS
    from kraken_ai_driven_v2_partition import (
        ASSET_ORDER,
        DATASET_ID,
        DATASET_MANIFEST_SHA256,
        DEVELOPMENT_END_EXCLUSIVE_UTC,
        KNOWN_GAPS_UTC,
        PARTITION_PROTOCOL_ID,
        REFERENCE_PARTITION_CONTRACT,
        RESEARCH_START_UTC,
    )
    from kraken_ai_driven_v2_risk_execution import (
        REFERENCE_COST_PROFILE,
        REFERENCE_RISK_EXECUTION_POLICY,
        RISK_EXECUTION_POLICY_ID,
        KrakenAIDrivenV2RiskExecutionAdapter,
    )
    from kraken_ai_driven_v2_state_machine import (
        ACTION_INTENT_COLUMN,
        INTENT_ENTER_NEXT_OPEN,
        PARAMETER_SET_COLUMN,
        PARAMETER_SET_ID,
        STATE_AFTER_COLUMN,
        TRANSITION_COLUMN,
        KrakenAIDrivenV2StateMachine,
    )
    from research_evidence import canonical_json_bytes
except ImportError:  # pragma: no cover - package import compatibility
    from .kraken_ai_driven_v2_features import REQUIRED_OHLCV_COLUMNS
    from .kraken_ai_driven_v2_partition import (
        ASSET_ORDER,
        DATASET_ID,
        DATASET_MANIFEST_SHA256,
        DEVELOPMENT_END_EXCLUSIVE_UTC,
        KNOWN_GAPS_UTC,
        PARTITION_PROTOCOL_ID,
        REFERENCE_PARTITION_CONTRACT,
        RESEARCH_START_UTC,
    )
    from .kraken_ai_driven_v2_risk_execution import (
        REFERENCE_COST_PROFILE,
        REFERENCE_RISK_EXECUTION_POLICY,
        RISK_EXECUTION_POLICY_ID,
        KrakenAIDrivenV2RiskExecutionAdapter,
    )
    from .kraken_ai_driven_v2_state_machine import (
        ACTION_INTENT_COLUMN,
        INTENT_ENTER_NEXT_OPEN,
        PARAMETER_SET_COLUMN,
        PARAMETER_SET_ID,
        STATE_AFTER_COLUMN,
        TRANSITION_COLUMN,
        KrakenAIDrivenV2StateMachine,
    )
    from .research_evidence import canonical_json_bytes


SCHEMA_VERSION = 1
DEVELOPMENT_PROTOCOL_ID = (
    "kraken-btc-eth-xrp-ai-driven-v2-development-runner-v1"
)
DEVELOPMENT_RUN_ID = (
    "kraken-btc-eth-xrp-ai-driven-v2-development-reference-a-v1"
)
AUTHORIZATION_PHRASE = (
    "EXECUTE_KRAKEN_AI_V2_DEVELOPMENT_REFERENCE_A_ONCE"
)
INITIAL_CAPITAL = 5000.0
QUOTE_CURRENCY = "USD_RESEARCH_NOTIONAL"
DEVELOPMENT_DIRECTORY_NAME = "development_reference_a_v1"
STAGING_DIRECTORY_NAME = ".development_reference_a_v1.staging"
REPORT_FILENAME = "kraken_ai_v2_development_report.json"
REPORT_SHA256_FILENAME = "kraken_ai_v2_development_report.sha256"
EXPECTED_FULL_ROWS = {"BTC-USD": 2646, "ETH-USD": 2647, "XRP-USD": 2645}
EXPECTED_DEVELOPMENT_ROWS = {
    "BTC-USD": 1916,
    "ETH-USD": 1917,
    "XRP-USD": 1915,
}
CANONICAL_COLUMNS = ("Date", "Open", "High", "Low", "Close", "Volume")


def _canonical_manifest_bytes(payload):
    return (json.dumps(payload, indent=2, sort_keys=True) + "\n").encode("utf-8")


def _file_sha256(path, chunk_bytes=1024 * 1024):
    digest = hashlib.sha256()
    try:
        with Path(path).open("rb") as source:
            for chunk in iter(lambda: source.read(chunk_bytes), b""):
                digest.update(chunk)
    except OSError as exc:
        raise ValueError(f"Unable to hash development input: {path}") from exc
    return digest.hexdigest()


def _decimal(value, label):
    try:
        result = Decimal(value)
    except (InvalidOperation, TypeError, ValueError) as exc:
        raise ValueError(f"Development {label} is not numeric.") from exc
    if not result.is_finite():
        raise ValueError(f"Development {label} must be finite.")
    return result


def _development_row(line, asset):
    try:
        decoded = line.decode("utf-8")
        row = next(csv.reader([decoded]))
    except (UnicodeError, csv.Error) as exc:
        raise ValueError(f"Unable to parse development row for {asset}.") from exc
    if len(row) != len(CANONICAL_COLUMNS):
        raise ValueError(f"Development row has wrong column count for {asset}.")
    timestamp = pd.Timestamp(row[0])
    if timestamp.tzinfo is None:
        raise ValueError("Development timestamp must be timezone-aware.")
    timestamp = timestamp.tz_convert("UTC")
    if timestamp != timestamp.normalize():
        raise ValueError("Development timestamp must align to UTC midnight.")
    values = [
        _decimal(value, name)
        for value, name in zip(row[1:], CANONICAL_COLUMNS[1:])
    ]
    open_, high, low, close, volume = values
    if min(open_, high, low, close) <= 0 or volume < 0:
        raise ValueError(f"Development OHLCV sign is invalid for {asset}.")
    if high < max(open_, close) or low > min(open_, close) or high < low:
        raise ValueError(f"Development price geometry is invalid for {asset}.")
    return timestamp, values


@dataclass(frozen=True)
class LockedDevelopmentDataset:
    dataset_id: str
    manifest_sha256: str
    source_mode: str
    development_frames: dict
    asset_file_sha256: dict
    full_observed_rows: dict
    opaque_non_development_rows: dict
    calibration_rows_parsed: int
    evaluation_rows_parsed: int

    def __post_init__(self):
        if self.dataset_id != DATASET_ID:
            raise ValueError("Development dataset identity mismatch.")
        if self.source_mode != "OFFICIAL_OHLCVT_ARCHIVES_ONLY":
            raise ValueError("Development dataset source mode mismatch.")
        for mapping, name in (
            (self.development_frames, "development frames"),
            (self.asset_file_sha256, "asset hashes"),
            (self.full_observed_rows, "full row counts"),
            (self.opaque_non_development_rows, "opaque row counts"),
        ):
            if tuple(mapping) != ASSET_ORDER:
                raise ValueError(f"Development {name} asset order mismatch.")
        if self.calibration_rows_parsed != 0 or self.evaluation_rows_parsed != 0:
            raise ValueError("Nondevelopment OHLCV must remain unparsed.")

    def frame(self, asset):
        if asset not in ASSET_ORDER:
            raise ValueError(f"Unknown development asset: {asset}.")
        return self.development_frames[asset].copy(deep=True)


class KrakenAIDrivenV2DevelopmentDatasetReader:
    """Hash the full lock, but parse OHLCV only before the development end."""

    @staticmethod
    def _parse_development_prefix(path, asset):
        cutoff = pd.Timestamp(DEVELOPMENT_END_EXCLUSIVE_UTC)
        index = []
        values = []
        first_opaque_timestamp = None
        try:
            with Path(path).open("rb") as source:
                header = source.readline()
                if header != b"Date,Open,High,Low,Close,Volume\n":
                    raise ValueError(
                        f"Canonical development header mismatch for {asset}."
                    )
                for line in source:
                    timestamp_token = line.split(b",", 1)[0]
                    try:
                        timestamp = pd.Timestamp(timestamp_token.decode("ascii"))
                    except (UnicodeError, ValueError) as exc:
                        raise ValueError(
                            f"Canonical timestamp is invalid for {asset}."
                        ) from exc
                    if timestamp.tzinfo is None:
                        raise ValueError(
                            f"Canonical timestamp is timezone-naive for {asset}."
                        )
                    timestamp = timestamp.tz_convert("UTC")
                    if timestamp >= cutoff:
                        first_opaque_timestamp = timestamp
                        break
                    parsed_timestamp, parsed_values = _development_row(line, asset)
                    index.append(parsed_timestamp)
                    values.append(parsed_values)
        except OSError as exc:
            raise ValueError(f"Unable to read development prefix for {asset}.") from exc
        if first_opaque_timestamp != cutoff:
            raise ValueError(
                f"First opaque nondevelopment timestamp mismatch for {asset}."
            )
        frame = pd.DataFrame(
            values,
            index=pd.DatetimeIndex(index),
            columns=REQUIRED_OHLCV_COLUMNS,
            dtype="float64",
        )
        return frame

    def read(self, dataset_path):
        dataset_path = Path(dataset_path)
        manifest_path = dataset_path / "manifest.json"
        sidecar_path = dataset_path / "manifest.sha256"
        try:
            manifest_bytes = manifest_path.read_bytes()
            manifest = json.loads(manifest_bytes.decode("utf-8"))
            sidecar = sidecar_path.read_text(encoding="ascii").strip().split()
        except (OSError, UnicodeError, json.JSONDecodeError) as exc:
            raise ValueError("Unable to read locked development manifest.") from exc
        manifest_digest = hashlib.sha256(manifest_bytes).hexdigest()
        if manifest_digest != DATASET_MANIFEST_SHA256:
            raise ValueError("Development manifest SHA-256 mismatch.")
        if sidecar != [manifest_digest, "manifest.json"]:
            raise ValueError("Development manifest sidecar mismatch.")
        if manifest_bytes != _canonical_manifest_bytes(manifest):
            raise ValueError("Development manifest bytes are not canonical.")
        if manifest.get("dataset_id") != DATASET_ID:
            raise ValueError("Development manifest dataset identity mismatch.")
        if manifest.get("source_mode") != "OFFICIAL_OHLCVT_ARCHIVES_ONLY":
            raise ValueError("Development manifest source mode mismatch.")
        if manifest.get("network_requests_executed") is not False:
            raise ValueError("Development input cannot contain network execution.")
        if manifest.get("asset_order") != list(ASSET_ORDER):
            raise ValueError("Development manifest asset order mismatch.")
        if tuple(manifest.get("canonical_columns", ())) != CANONICAL_COLUMNS:
            raise ValueError("Development canonical columns mismatch.")

        inventory = manifest.get("archive_inventory", {})
        inventory_path = dataset_path / str(inventory.get("file", ""))
        if _file_sha256(inventory_path) != inventory.get("sha256"):
            raise ValueError("Development archive inventory SHA-256 mismatch.")

        frames = {}
        hashes = {}
        full_rows = {}
        opaque_rows = {}
        assets = manifest.get("assets", {})
        if tuple(assets) != ASSET_ORDER:
            raise ValueError("Development manifest asset evidence order mismatch.")
        for asset in ASSET_ORDER:
            evidence = assets[asset]
            path = dataset_path / str(evidence.get("file", ""))
            digest = _file_sha256(path)
            if digest != evidence.get("sha256"):
                raise ValueError(f"Development asset SHA-256 mismatch for {asset}.")
            observed_rows = evidence.get("observed_rows")
            if observed_rows != EXPECTED_FULL_ROWS[asset]:
                raise ValueError(f"Full observed-row mismatch for {asset}.")
            if tuple(evidence.get("missing_timestamps", ())) != KNOWN_GAPS_UTC[asset]:
                raise ValueError(f"Development gap evidence mismatch for {asset}.")
            frame = self._parse_development_prefix(path, asset)
            REFERENCE_PARTITION_CONTRACT.validate_partition_index(
                asset, "DEVELOPMENT", frame.index
            )
            if len(frame) != EXPECTED_DEVELOPMENT_ROWS[asset]:
                raise ValueError(f"Development observed-row mismatch for {asset}.")
            frames[asset] = frame
            hashes[asset] = digest
            full_rows[asset] = observed_rows
            opaque_rows[asset] = observed_rows - len(frame)

        return LockedDevelopmentDataset(
            dataset_id=manifest["dataset_id"],
            manifest_sha256=manifest_digest,
            source_mode=manifest["source_mode"],
            development_frames=frames,
            asset_file_sha256=hashes,
            full_observed_rows=full_rows,
            opaque_non_development_rows=opaque_rows,
            calibration_rows_parsed=0,
            evaluation_rows_parsed=0,
        )


def development_configuration():
    return {
        "schema_version": SCHEMA_VERSION,
        "development_protocol_id": DEVELOPMENT_PROTOCOL_ID,
        "development_run_id": DEVELOPMENT_RUN_ID,
        "dataset_id": DATASET_ID,
        "dataset_manifest_sha256": DATASET_MANIFEST_SHA256,
        "partition_protocol_id": PARTITION_PROTOCOL_ID,
        "partition_plan_sha256": REFERENCE_PARTITION_CONTRACT.plan_sha256(),
        "partition": "DEVELOPMENT",
        "development_start_utc": RESEARCH_START_UTC,
        "development_end_exclusive_utc": DEVELOPMENT_END_EXCLUSIVE_UTC,
        "asset_order": list(ASSET_ORDER),
        "same_timestamp_entry_order": list(ASSET_ORDER),
        "same_timestamp_phase_order": [
            "EXISTING_POSITION_OPEN_EXITS",
            "PENDING_ENTRIES_IN_ASSET_ORDER",
            "ACTIVE_POSITION_INTRABAR_PROTECTION",
            "COMPLETED_BAR_EXIT_SCHEDULING",
            "CLOSE_LIQUIDATION_MARK",
        ],
        "initial_capital": INITIAL_CAPITAL,
        "quote_currency": QUOTE_CURRENCY,
        "parameter_set_id": PARAMETER_SET_ID,
        "risk_execution_policy_id": RISK_EXECUTION_POLICY_ID,
        "terminal_position_policy": (
            "PRESERVE_UNRESOLVED_NO_SYNTHETIC_FORCE_CLOSE"
        ),
        "gap_with_open_position_policy": "HALT_INCONCLUSIVE_PRESERVE_UNRESOLVED",
        "following_open_missing_policy": "CANCEL_PENDING_ENTRY_INTENT",
        "equity_mark": "ADVERSE_SELL_AND_COMMISSION_AT_COMPLETED_CLOSE",
        "full_asset_file_verification": "OPAQUE_BYTE_SHA256",
        "nondevelopment_ohlcv_parsing": False,
        "parameter_sweep_authorized": False,
        "automatic_ranking_authorized": False,
        "automatic_promotion_authorized": False,
        "calibration_access_authorized": False,
        "evaluation_access_authorized": False,
        "real_order_submission": False,
        "live_execution_authorized": False,
    }


@dataclass(frozen=True)
class RecordedDevelopmentEvidence:
    report_path: Path
    checksum_path: Path
    report_sha256: str
    development_status: str
    closed_trade_count: int
    terminal_open_position_count: int
    status: str = "KRAKEN_AI_V2_DEVELOPMENT_EVIDENCE_RECORDED"

    def as_dict(self):
        return {
            "status": self.status,
            "report_path": str(self.report_path),
            "checksum_path": str(self.checksum_path),
            "report_sha256": self.report_sha256,
            "development_status": self.development_status,
            "closed_trade_count": self.closed_trade_count,
            "terminal_open_position_count": self.terminal_open_position_count,
            "development_run_authorized": True,
            "development_run_executed": True,
            "development_data_opened": True,
            "calibration_data_opened": False,
            "evaluation_data_opened": False,
            "candidate_v2_authorized": False,
            "bounded_forward_paper_authorized": False,
            "live_execution_authorized": False,
        }


@dataclass(frozen=True)
class LockedDevelopmentEvidence:
    report_path: Path
    checksum_path: Path
    report_sha256: str
    report: dict
    status: str = "KRAKEN_AI_V2_DEVELOPMENT_EVIDENCE_LOCK_PASS"


class KrakenAIDrivenV2DevelopmentEvidenceLock:
    """Independently validate canonical one-shot development evidence."""

    def lock(self, evidence_directory):
        evidence_directory = Path(evidence_directory)
        report_path = evidence_directory / REPORT_FILENAME
        checksum_path = evidence_directory / REPORT_SHA256_FILENAME
        try:
            report_bytes = report_path.read_bytes()
            checksum = checksum_path.read_text(encoding="ascii").strip().split()
        except (OSError, UnicodeError) as exc:
            raise ValueError(
                "Unable to read Kraken AI v2 development evidence."
            ) from exc
        digest = hashlib.sha256(report_bytes).hexdigest()
        if checksum != [digest, REPORT_FILENAME]:
            raise ValueError("Development evidence SHA-256 sidecar mismatch.")
        try:
            report = json.loads(report_bytes.decode("utf-8"))
        except (UnicodeError, json.JSONDecodeError) as exc:
            raise ValueError(
                "Unable to decode Kraken AI v2 development evidence."
            ) from exc
        if report_bytes != canonical_json_bytes(report):
            raise ValueError("Development report bytes are not canonical.")
        expected = {
            "schema_version": SCHEMA_VERSION,
            "development_protocol_id": DEVELOPMENT_PROTOCOL_ID,
            "development_run_id": DEVELOPMENT_RUN_ID,
            "dataset_id": DATASET_ID,
            "dataset_manifest_sha256": DATASET_MANIFEST_SHA256,
            "partition_protocol_id": PARTITION_PROTOCOL_ID,
            "partition_plan_sha256": REFERENCE_PARTITION_CONTRACT.plan_sha256(),
            "configuration": development_configuration(),
            "dataset_opened": True,
            "development_data_opened": True,
            "calibration_data_opened": False,
            "evaluation_data_opened": False,
            "development_run_authorized": True,
            "development_run_executed": True,
            "real_orders_submitted": False,
            "parameter_sweep_executed": False,
            "candidate_v2_authorized": False,
            "bounded_forward_paper_authorized": False,
            "cloud_execution_authorized": False,
            "live_execution_authorized": False,
        }
        for key, value in expected.items():
            if report.get(key) != value:
                raise ValueError(
                    f"Development evidence field is invalid: {key}."
                )
        allowed_statuses = {
            "KRAKEN_AI_V2_DEVELOPMENT_COMPLETED_FLAT",
            (
                "KRAKEN_AI_V2_DEVELOPMENT_COMPLETED_WITH_"
                "UNRESOLVED_TERMINAL_POSITION"
            ),
            "KRAKEN_AI_V2_DEVELOPMENT_INCONCLUSIVE_OPEN_POSITION_AT_GAP",
        }
        if report.get("status") not in allowed_statuses:
            raise ValueError("Development evidence status is invalid.")
        if report.get("calibration_rows_parsed") != 0:
            raise ValueError("Development evidence parsed calibration rows.")
        if report.get("evaluation_rows_parsed") != 0:
            raise ValueError("Development evidence parsed evaluation rows.")
        return LockedDevelopmentEvidence(
            report_path=report_path,
            checksum_path=checksum_path,
            report_sha256=digest,
            report=report,
        )


class KrakenAIDrivenV2DevelopmentRunner:
    """Execute reference A exactly once on the frozen development partition."""

    def __init__(
        self,
        *,
        dataset_reader=None,
        state_machine_factory=None,
        adapter_factory=KrakenAIDrivenV2RiskExecutionAdapter,
    ):
        self.dataset_reader = (
            dataset_reader or KrakenAIDrivenV2DevelopmentDatasetReader()
        )
        self.state_machine_factory = state_machine_factory or (
            lambda asset: KrakenAIDrivenV2StateMachine()
        )
        self.adapter_factory = adapter_factory
        if not hasattr(self.dataset_reader, "read"):
            raise TypeError("Development dataset reader must provide read().")
        if not callable(self.state_machine_factory):
            raise TypeError("Development state-machine factory must be callable.")
        if not callable(self.adapter_factory):
            raise TypeError("Development adapter factory must be callable.")

    @staticmethod
    def _validated_frames(frames):
        if not isinstance(frames, dict) or tuple(frames) != ASSET_ORDER:
            raise ValueError("Development frame asset order mismatch.")
        validated = {}
        for asset in ASSET_ORDER:
            frame = frames[asset]
            if not isinstance(frame, pd.DataFrame):
                raise TypeError(f"Development frame must be a DataFrame for {asset}.")
            if tuple(frame.columns) != REQUIRED_OHLCV_COLUMNS:
                raise ValueError(f"Development OHLCV columns mismatch for {asset}.")
            REFERENCE_PARTITION_CONTRACT.validate_partition_index(
                asset, "DEVELOPMENT", frame.index
            )
            validated[asset] = frame.copy(deep=True)
        return validated

    def _state_results(self, frames):
        results = {}
        segment_rows = {}
        transition_counts = {}
        for asset in ASSET_ORDER:
            indexes = REFERENCE_PARTITION_CONTRACT.materialize_segments(
                asset, "DEVELOPMENT", frames[asset].index
            )
            generated = []
            for index in indexes:
                state_machine = self.state_machine_factory(asset)
                segment = frames[asset].loc[index].copy(deep=True)
                result = state_machine.generate(segment)
                if (
                    not isinstance(result, pd.DataFrame)
                    or not result.index.equals(index)
                ):
                    raise ValueError(f"State output identity mismatch for {asset}.")
                required = (
                    ACTION_INTENT_COLUMN,
                    STATE_AFTER_COLUMN,
                    TRANSITION_COLUMN,
                    PARAMETER_SET_COLUMN,
                )
                if any(column not in result for column in required):
                    raise ValueError(
                        f"State output columns are incomplete for {asset}."
                    )
                if not result[PARAMETER_SET_COLUMN].eq(PARAMETER_SET_ID).all():
                    raise ValueError(f"State parameter identity mismatch for {asset}.")
                generated.append(result.copy(deep=True))
            combined = pd.concat(generated).sort_index()
            if not combined.index.equals(frames[asset].index):
                raise ValueError(f"Combined state output mismatch for {asset}.")
            results[asset] = combined
            segment_rows[asset] = [len(index) for index in indexes]
            transition_counts[asset] = dict(
                sorted(Counter(combined[TRANSITION_COLUMN]).items())
            )
        return results, segment_rows, transition_counts

    @staticmethod
    def _position_risk(position, adapter):
        entry_cost = (
            position.units
            * position.entry_fill_price
            + position.entry_commission
        )
        stop_fill = adapter.costs.sell_fill(position.stop_trigger_price)
        stop_proceeds = (
            stop_fill * position.units
            - adapter.costs.commission(stop_fill, position.units)
        )
        return max(0.0, entry_cost - stop_proceeds)

    @staticmethod
    def _liquidation_value(position, reference_price, adapter):
        fill = adapter.costs.sell_fill(float(reference_price))
        return fill * position.units - adapter.costs.commission(
            fill, position.units
        )

    def execute_development(self, frames):
        frames = self._validated_frames(frames)
        state_results, segment_rows, transition_counts = self._state_results(frames)
        adapter = self.adapter_factory()
        if adapter.configuration() != REFERENCE_RISK_EXECUTION_POLICY.configuration():
            raise ValueError("Development risk/execution policy identity changed.")

        cash = INITIAL_CAPITAL
        positions = {}
        position_evidence = {}
        pending_entries = {}
        pending_exits = {}
        entry_ledger = []
        trade_ledger = []
        canceled_entries = []
        rejection_counts = Counter()
        exit_reason_counts = Counter()
        last_close = {}
        equity_curve = []
        peak_equity = INITIAL_CAPITAL
        maximum_drawdown = 0.0
        maximum_positions = 0
        maximum_open_risk_fraction = 0.0
        halt_timestamp = None
        halt_asset = None

        def current_risk():
            return sum(
                self._position_risk(position, adapter)
                for position in positions.values()
            )

        def mark_equity(rows, column):
            value = cash
            for asset, position in positions.items():
                row = rows.get(asset)
                reference = (
                    row[column]
                    if row is not None
                    else last_close.get(asset)
                )
                if reference is None:
                    raise RuntimeError("Position mark is unavailable.")
                value += self._liquidation_value(position, reference, adapter)
            return value

        def record_exit(asset, timestamp, decision):
            nonlocal cash
            position = positions[asset]
            evidence = position_evidence[asset]
            cash += decision.net_proceeds
            net_pnl = decision.net_proceeds - evidence["cash_required"]
            trade_ledger.append(
                {
                    "asset": asset,
                    "signal_timestamp": evidence["signal_timestamp"],
                    "entry_timestamp": position.entry_timestamp.isoformat(),
                    "exit_timestamp": timestamp.isoformat(),
                    "entry_fill_price": position.entry_fill_price,
                    "exit_fill_price": decision.fill_price,
                    "units": position.units,
                    "entry_commission": position.entry_commission,
                    "exit_commission": decision.commission,
                    "cash_required": evidence["cash_required"],
                    "net_proceeds": decision.net_proceeds,
                    "net_pnl": net_pnl,
                    "net_return_fraction": net_pnl / evidence["cash_required"],
                    "bars_held_before_exit": position.bars_held,
                    "exit_reason": decision.reason,
                    "exit_type": decision.exit_type,
                    "same_bar_conflict": decision.same_bar_conflict,
                }
            )
            exit_reason_counts[decision.reason] += 1
            del positions[asset]
            del position_evidence[asset]
            pending_exits.pop(asset, None)

        calendar = pd.date_range(
            RESEARCH_START_UTC,
            DEVELOPMENT_END_EXCLUSIVE_UTC,
            freq="D",
            inclusive="left",
        )
        for timestamp in calendar:
            rows = {
                asset: (
                    frames[asset].loc[timestamp]
                    if timestamp in frames[asset].index
                    else None
                )
                for asset in ASSET_ORDER
            }
            gap_position = next(
                (
                    asset
                    for asset in ASSET_ORDER
                    if rows[asset] is None and asset in positions
                ),
                None,
            )
            if gap_position is not None:
                halt_timestamp = timestamp
                halt_asset = gap_position
                break
            for asset in ASSET_ORDER:
                if rows[asset] is None and asset in pending_entries:
                    signal = pending_entries.pop(asset)
                    canceled_entries.append(
                        {
                            "asset": asset,
                            "signal_timestamp": signal.name.isoformat(),
                            "expected_execution_timestamp": timestamp.isoformat(),
                            "reason": (
                                "FOLLOWING_OPEN_UNAVAILABLE_AT_RECORDED_GAP"
                            ),
                        }
                    )

            for asset in ASSET_ORDER:
                if asset not in positions:
                    continue
                decision = adapter.evaluate_open(
                    positions[asset],
                    float(rows[asset]["Open"]),
                    pending_exit_reason=pending_exits.get(asset),
                )
                if decision.status == "SYNTHETIC_EXIT":
                    record_exit(asset, timestamp, decision)

            for asset in ASSET_ORDER:
                signal = pending_entries.pop(asset, None)
                if signal is None or rows[asset] is None:
                    continue
                if asset in positions:
                    rejection_counts["POSITION_ALREADY_OPEN"] += 1
                    continue
                equity = mark_equity(rows, "Open")
                plan = adapter.plan_entry(
                    signal,
                    execution_timestamp=timestamp,
                    next_open_price=float(rows[asset]["Open"]),
                    equity=equity,
                    available_cash=cash,
                    current_open_risk_amount=current_risk(),
                    open_crypto_positions=len(positions),
                )
                if not plan.approved:
                    rejection_counts[plan.reason] += 1
                    continue
                cash -= plan.cash_required
                position = adapter.position_from_plan(plan)
                positions[asset] = position
                position_evidence[asset] = {
                    "signal_timestamp": plan.signal_timestamp,
                    "cash_required": plan.cash_required,
                    "planned_monetary_risk": plan.planned_monetary_risk,
                }
                maximum_open_risk_fraction = max(
                    maximum_open_risk_fraction,
                    current_risk() / equity,
                )
                maximum_positions = max(maximum_positions, len(positions))
                entry_ledger.append(
                    {
                        "asset": asset,
                        "signal_timestamp": plan.signal_timestamp,
                        "execution_timestamp": plan.execution_timestamp,
                        "entry_fill_price": plan.entry_fill_price,
                        "units": plan.position_size,
                        "cash_required": plan.cash_required,
                        "planned_monetary_risk": plan.planned_monetary_risk,
                        "net_reward_risk_ratio": plan.net_reward_risk_ratio,
                    }
                )

            for asset in ASSET_ORDER:
                if asset not in positions:
                    continue
                decision = adapter.evaluate_intrabar(
                    positions[asset],
                    float(rows[asset]["High"]),
                    float(rows[asset]["Low"]),
                )
                if decision.status == "SYNTHETIC_EXIT":
                    record_exit(asset, timestamp, decision)

            for asset in ASSET_ORDER:
                if asset not in positions:
                    continue
                state_row = state_results[asset].loc[timestamp]
                schedule = adapter.complete_bar(
                    positions[asset], state_row[ACTION_INTENT_COLUMN]
                )
                positions[asset] = schedule.updated_position
                if schedule.pending_exit_reason is None:
                    pending_exits.pop(asset, None)
                else:
                    pending_exits[asset] = schedule.pending_exit_reason

            for asset in ASSET_ORDER:
                if rows[asset] is None:
                    continue
                state_row = state_results[asset].loc[timestamp]
                if state_row[ACTION_INTENT_COLUMN] == INTENT_ENTER_NEXT_OPEN:
                    pending_entries[asset] = state_row.copy(deep=True)
                last_close[asset] = float(rows[asset]["Close"])

            marked_equity = mark_equity(rows, "Close")
            peak_equity = max(peak_equity, marked_equity)
            drawdown = (
                0.0
                if peak_equity <= 0.0
                else (peak_equity - marked_equity) / peak_equity
            )
            maximum_drawdown = max(maximum_drawdown, drawdown)
            equity_curve.append(
                {"timestamp": timestamp.isoformat(), "marked_equity": marked_equity}
            )
            maximum_positions = max(maximum_positions, len(positions))

        if halt_timestamp is None:
            for asset, signal in tuple(pending_entries.items()):
                canceled_entries.append(
                    {
                        "asset": asset,
                        "signal_timestamp": signal.name.isoformat(),
                        "expected_execution_timestamp": (
                            pd.Timestamp(DEVELOPMENT_END_EXCLUSIVE_UTC).isoformat()
                        ),
                        "reason": "FOLLOWING_OPEN_OUTSIDE_DEVELOPMENT_PARTITION",
                    }
                )
                del pending_entries[asset]

        terminal_positions = []
        for asset in ASSET_ORDER:
            if asset not in positions:
                continue
            position = positions[asset]
            marked_value = self._liquidation_value(
                position, last_close[asset], adapter
            )
            terminal_positions.append(
                {
                    "asset": asset,
                    "entry_timestamp": position.entry_timestamp.isoformat(),
                    "units": position.units,
                    "entry_fill_price": position.entry_fill_price,
                    "entry_commission": position.entry_commission,
                    "stop_trigger_price": position.stop_trigger_price,
                    "target_trigger_price": position.target_trigger_price,
                    "bars_held": position.bars_held,
                    "last_development_close": last_close[asset],
                    "adverse_liquidation_mark": marked_value,
                    "resolution": "OPEN_POSITION_UNRESOLVED",
                }
            )
        terminal_marked_equity = cash + sum(
            item["adverse_liquidation_mark"] for item in terminal_positions
        )
        if halt_timestamp is not None:
            status = (
                "KRAKEN_AI_V2_DEVELOPMENT_INCONCLUSIVE_OPEN_POSITION_AT_GAP"
            )
        elif terminal_positions:
            status = (
                "KRAKEN_AI_V2_DEVELOPMENT_COMPLETED_WITH_"
                "UNRESOLVED_TERMINAL_POSITION"
            )
        else:
            status = "KRAKEN_AI_V2_DEVELOPMENT_COMPLETED_FLAT"
        realized_net_pnl = sum(trade["net_pnl"] for trade in trade_ledger)
        winning_trades = sum(trade["net_pnl"] > 0.0 for trade in trade_ledger)
        losing_trades = sum(trade["net_pnl"] < 0.0 for trade in trade_ledger)
        total_commissions = sum(
            entry["entry_fill_price"]
            * entry["units"]
            * REFERENCE_COST_PROFILE.commission_rate
            for entry in entry_ledger
        ) + sum(trade["exit_commission"] for trade in trade_ledger)
        return {
            "status": status,
            "path_completed": halt_timestamp is None,
            "halt_timestamp": (
                None if halt_timestamp is None else halt_timestamp.isoformat()
            ),
            "halt_asset": halt_asset,
            "development_rows": {
                asset: len(frames[asset]) for asset in ASSET_ORDER
            },
            "continuous_segment_rows": segment_rows,
            "state_transition_counts": transition_counts,
            "initial_capital": INITIAL_CAPITAL,
            "realized_cash": cash,
            "terminal_marked_equity": terminal_marked_equity,
            "terminal_marked_return_fraction": (
                terminal_marked_equity / INITIAL_CAPITAL - 1.0
            ),
            "maximum_marked_drawdown_fraction": maximum_drawdown,
            "equity_mark_count": len(equity_curve),
            "closed_trade_count": len(trade_ledger),
            "winning_trade_count": winning_trades,
            "losing_trade_count": losing_trades,
            "flat_trade_count": len(trade_ledger) - winning_trades - losing_trades,
            "realized_net_pnl": realized_net_pnl,
            "total_modeled_commissions": total_commissions,
            "approved_entry_count": len(entry_ledger),
            "rejected_entry_count": sum(rejection_counts.values()),
            "entry_rejection_reason_counts": dict(sorted(rejection_counts.items())),
            "canceled_entry_intent_count": len(canceled_entries),
            "canceled_entry_intents": canceled_entries,
            "maximum_concurrent_positions": maximum_positions,
            "maximum_planned_open_risk_fraction": maximum_open_risk_fraction,
            "exit_reason_counts": dict(sorted(exit_reason_counts.items())),
            "entry_ledger": entry_ledger,
            "closed_trade_ledger": trade_ledger,
            "terminal_open_position_count": len(terminal_positions),
            "terminal_open_positions": terminal_positions,
            "synthetic_terminal_force_close_executed": False,
            "dataset_opened": True,
            "development_data_opened": True,
            "calibration_data_opened": False,
            "evaluation_data_opened": False,
            "development_run_authorized": True,
            "development_run_executed": True,
            "real_orders_submitted": False,
            "performance_evaluation_executed": True,
            "parameter_sweep_executed": False,
            "automatic_ranking_generated": False,
            "automatic_strategy_selection": False,
            "candidate_v2_authorized": False,
            "optimization_authorized": False,
            "bounded_forward_paper_authorized": False,
            "cloud_execution_authorized": False,
            "live_execution_authorized": False,
        }

    @staticmethod
    def _external_paths(dataset_path, evidence_root):
        project_root = Path(__file__).resolve().parents[1]
        dataset = Path(dataset_path).resolve()
        evidence = Path(evidence_root).resolve()
        if dataset == project_root or dataset.is_relative_to(project_root):
            raise ValueError("Development dataset must remain outside the repository.")
        if evidence == project_root or evidence.is_relative_to(project_root):
            raise ValueError("Development evidence must remain outside the repository.")
        if (
            dataset == evidence
            or evidence.is_relative_to(dataset)
            or dataset.is_relative_to(evidence)
        ):
            raise ValueError("Development dataset and evidence must not overlap.")
        return dataset, evidence

    @staticmethod
    def _assert_one_shot(evidence_root):
        final = evidence_root / DEVELOPMENT_DIRECTORY_NAME
        staging = evidence_root / STAGING_DIRECTORY_NAME
        if final.exists():
            raise FileExistsError(
                "Kraken AI v2 development evidence already exists; refusing repeat."
            )
        if staging.exists():
            raise FileExistsError(
                "Incomplete Kraken AI v2 development staging evidence exists."
            )
        return final, staging

    def run(self, dataset_path, evidence_root, authorization_phrase):
        if authorization_phrase != AUTHORIZATION_PHRASE:
            raise PermissionError("Exact development authorization phrase is required.")
        dataset_path, evidence_root = self._external_paths(
            dataset_path, evidence_root
        )
        final, staging = self._assert_one_shot(evidence_root)
        locked = self.dataset_reader.read(dataset_path)
        if locked.manifest_sha256 != DATASET_MANIFEST_SHA256:
            raise ValueError("Locked development manifest identity mismatch.")
        if locked.calibration_rows_parsed or locked.evaluation_rows_parsed:
            raise ValueError("Locked reader exposed nondevelopment OHLCV.")
        execution = self.execute_development(
            {asset: locked.frame(asset) for asset in ASSET_ORDER}
        )
        payload = {
            "schema_version": SCHEMA_VERSION,
            "development_protocol_id": DEVELOPMENT_PROTOCOL_ID,
            "development_run_id": DEVELOPMENT_RUN_ID,
            "dataset_id": locked.dataset_id,
            "dataset_manifest_sha256": locked.manifest_sha256,
            "source_mode": locked.source_mode,
            "partition_protocol_id": PARTITION_PROTOCOL_ID,
            "partition_plan_sha256": REFERENCE_PARTITION_CONTRACT.plan_sha256(),
            "configuration": development_configuration(),
            "asset_file_sha256": locked.asset_file_sha256,
            "full_observed_rows": locked.full_observed_rows,
            "opaque_non_development_rows": locked.opaque_non_development_rows,
            "full_asset_files_hashed_as_opaque_bytes": True,
            "calibration_rows_parsed": 0,
            "evaluation_rows_parsed": 0,
            **execution,
        }
        report_bytes = canonical_json_bytes(payload)
        report_sha256 = hashlib.sha256(report_bytes).hexdigest()
        checksum_bytes = f"{report_sha256}  {REPORT_FILENAME}\n".encode("ascii")
        evidence_root.mkdir(parents=True, exist_ok=True)
        staging.mkdir(exist_ok=False)
        (staging / REPORT_FILENAME).write_bytes(report_bytes)
        (staging / REPORT_SHA256_FILENAME).write_bytes(checksum_bytes)
        staging.rename(final)
        locked_evidence = KrakenAIDrivenV2DevelopmentEvidenceLock().lock(final)
        return RecordedDevelopmentEvidence(
            report_path=locked_evidence.report_path,
            checksum_path=locked_evidence.checksum_path,
            report_sha256=locked_evidence.report_sha256,
            development_status=execution["status"],
            closed_trade_count=execution["closed_trade_count"],
            terminal_open_position_count=execution[
                "terminal_open_position_count"
            ],
        )


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="Execute Kraken AI-driven v2 development reference A once."
    )
    parser.add_argument("--dataset", required=True)
    parser.add_argument("--evidence-root", required=True)
    parser.add_argument("--authorization-phrase", required=True)
    args = parser.parse_args(argv)
    recorded = KrakenAIDrivenV2DevelopmentRunner().run(
        args.dataset,
        args.evidence_root,
        args.authorization_phrase,
    )
    print(json.dumps(recorded.as_dict(), indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
