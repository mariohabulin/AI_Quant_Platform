"""Frozen venue/execution sensitivity assumptions for alpha development."""

from dataclasses import asdict, dataclass

import numpy as np

try:
    from first_strategy_candidate import BASELINE_COSTS, STRESSED_COSTS
except ImportError:  # package import when src is not placed directly on sys.path
    from src.first_strategy_candidate import BASELINE_COSTS, STRESSED_COSTS


@dataclass(frozen=True)
class VenueExecutionScenario:
    label: str
    venue: str
    order_role: str
    commission_rate: float
    slippage_rate: float
    spread_rate: float
    evidence_role: str
    eligibility: str
    source_url: str
    source_accessed_utc: str
    minimum_30_day_volume_usd: float | None = None
    executable_in_v2_runner: bool = True

    def __post_init__(self):
        for value, name in ((self.label, "Label"), (self.venue, "Venue")):
            if not isinstance(value, str) or not value.strip():
                raise ValueError(f"{name} is required.")
        if self.order_role not in ("TAKER", "MAKER"):
            raise ValueError("Order role must be TAKER or MAKER.")
        for value, name in (
            (self.commission_rate, "Commission rate"),
            (self.slippage_rate, "Slippage rate"),
            (self.spread_rate, "Spread rate"),
        ):
            if isinstance(value, bool) or not isinstance(value, (int, float)):
                raise TypeError(f"{name} must be numeric.")
            if not np.isfinite(float(value)) or float(value) < 0.0:
                raise ValueError(f"{name} must be finite and non-negative.")
        if self.minimum_30_day_volume_usd is not None:
            if float(self.minimum_30_day_volume_usd) < 0.0:
                raise ValueError("Minimum 30-day volume cannot be negative.")
        if self.order_role == "MAKER" and self.executable_in_v2_runner:
            raise ValueError("Maker scenarios require a reviewed causal fill model.")

    @property
    def total_rate(self):
        return (
            float(self.commission_rate)
            + float(self.slippage_rate)
            + float(self.spread_rate)
        )

    def as_dict(self):
        result = asdict(self)
        result["total_rate"] = self.total_rate
        return result


COINBASE_SOURCE = (
    "https://help.coinbase.com/en/exchange/trading-and-funding/"
    "exchange-fees"
)
KRAKEN_SOURCE = "https://www.kraken.com/features/fee-schedule"

VENUE_EXECUTION_SCENARIOS = (
    VenueExecutionScenario(
        label=BASELINE_COSTS.label,
        venue="Coinbase",
        order_role="TAKER",
        commission_rate=BASELINE_COSTS.commission_rate,
        slippage_rate=BASELINE_COSTS.slippage_rate,
        spread_rate=BASELINE_COSTS.spread_rate,
        evidence_role="DEPLOYABILITY_BASELINE",
        eligibility="LOW_VOLUME_TAKER_FROZEN_FROM_CANDIDATE_V1",
        source_url=COINBASE_SOURCE,
        source_accessed_utc="2026-08-24",
    ),
    VenueExecutionScenario(
        label=STRESSED_COSTS.label,
        venue="Coinbase",
        order_role="TAKER",
        commission_rate=STRESSED_COSTS.commission_rate,
        slippage_rate=STRESSED_COSTS.slippage_rate,
        spread_rate=STRESSED_COSTS.spread_rate,
        evidence_role="DEPLOYABILITY_STRESS",
        eligibility="ADVERSE_EXECUTION_STRESS_NOT_ACCOUNT_QUOTE",
        source_url=COINBASE_SOURCE,
        source_accessed_utc="2026-08-24",
    ),
    VenueExecutionScenario(
        label="kraken_pro_10k_30d_taker_sensitivity_20260824",
        venue="Kraken Pro",
        order_role="TAKER",
        commission_rate=0.0038,
        slippage_rate=0.0005,
        spread_rate=0.0010,
        evidence_role="VENUE_SENSITIVITY_ONLY",
        eligibility="REVERIFY_ACCOUNT_30_DAY_VOLUME_AND_CURRENT_FEE_TIER",
        source_url=KRAKEN_SOURCE,
        source_accessed_utc="2026-08-24",
        minimum_30_day_volume_usd=10000.0,
    ),
    VenueExecutionScenario(
        label="kraken_pro_10k_30d_maker_deferred_20260824",
        venue="Kraken Pro",
        order_role="MAKER",
        commission_rate=0.0022,
        slippage_rate=0.0,
        spread_rate=0.0,
        evidence_role="DEFERRED_FILL_MODEL_RESEARCH",
        eligibility="REVERIFY_TIER_AND_IMPLEMENT_CAUSAL_PARTIAL_FILL_MODEL",
        source_url=KRAKEN_SOURCE,
        source_accessed_utc="2026-08-24",
        minimum_30_day_volume_usd=10000.0,
        executable_in_v2_runner=False,
    ),
)


def venue_execution_policy():
    return {
        "scenarios": [scenario.as_dict() for scenario in VENUE_EXECUTION_SCENARIOS],
        "runner_allowed_labels": [
            scenario.label
            for scenario in VENUE_EXECUTION_SCENARIOS
            if scenario.executable_in_v2_runner
        ],
        "maker_execution_status": "BLOCKED_PENDING_CAUSAL_FILL_MODEL",
        "static_tier_interpretation": "SENSITIVITY_NOT_ACCOUNT_ELIGIBILITY_PROOF",
        "required_before_deployment": [
            "CURRENT_ACCOUNT_FEE_TIER",
            "CURRENT_SPREAD",
            "ORDER_BOOK_DEPTH",
            "MARKET_IMPACT",
            "ORDER_FILL_AND_PARTIAL_FILL_BEHAVIOR",
        ],
        "cheaper_venue_cannot_override": [
            "DRAWDOWN_GATE",
            "WALK_FORWARD_PERSISTENCE_GATE",
            "STATISTICAL_FALSIFICATION_GATE",
        ],
    }
