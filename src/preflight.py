from dataclasses import dataclass
from pathlib import Path
import os
import tempfile

import pandas as pd


@dataclass(frozen=True)
class PreFlightCheck:
    name: str
    status: str
    reason: str


@dataclass(frozen=True)
class PreFlightReport:
    status: str
    checks: tuple

    @property
    def passed(self):
        return self.status == "PASS"


class PaperPreFlightGate:
    """Side-effect-minimized safety gate before a controlled real-time paper run.

    The gate validates configuration, credential presence, feed/provider scope,
    risk policy, account state, checkpoint writability and an injected
    connectivity probe. It never submits an order and never exposes credential
    values in the report.
    """

    PLACEHOLDERS = {"", "changeme", "replace_me", "your_api_key", "your_api_secret"}

    def __init__(self, runtime, credentials=None, connectivity_probe=None,
                 expected_symbol="BTC/USD", expected_timeframe="1min",
                 execution_enabled=False):
        if runtime is None:
            raise ValueError("runtime is required.")
        self.runtime = runtime
        self.credentials = credentials if credentials is not None else os.environ
        self.connectivity_probe = connectivity_probe
        self.expected_symbol = str(expected_symbol).upper()
        self.expected_timeframe = pd.Timedelta(expected_timeframe)
        self.execution_enabled = bool(execution_enabled)

    @staticmethod
    def _check(name, ok, success, failure):
        return PreFlightCheck(name, "PASS" if ok else "FAIL", success if ok else failure)

    def _credentials_check(self):
        key = str(self.credentials.get("ALPACA_API_KEY", "")).strip()
        secret = str(self.credentials.get("ALPACA_API_SECRET", "")).strip()
        ok = key.lower() not in self.PLACEHOLDERS and secret.lower() not in self.PLACEHOLDERS
        return self._check(
            "credentials", ok,
            "Required Alpaca credentials are present (values redacted).",
            "Required Alpaca credentials are missing or placeholder values.",
        )

    def _scope_check(self):
        feed = self.runtime.realtime_feed
        symbol = getattr(getattr(feed, "adapter", None), "symbol", None)
        ok = symbol == self.expected_symbol and feed.timeframe == self.expected_timeframe
        return self._check(
            "market_scope", ok,
            f"Market scope is {self.expected_symbol} / {self.expected_timeframe}.",
            "Configured provider symbol/timeframe does not match controlled pre-flight scope.",
        )

    def _risk_check(self):
        risk = self.runtime.session.engine.risk_engine
        explicit = (
            risk.risk_per_trade <= 0.01
            and risk.max_position_fraction <= 1.0
            and risk.max_drawdown_fraction is not None
            and risk.daily_loss_limit is not None
            and risk.weekly_loss_limit is not None
            and risk.min_reward_risk is not None
        )
        return self._check(
            "risk_policy", explicit,
            "Conservative position risk and explicit protection guards are configured.",
            "Paper pre-flight requires explicit drawdown/daily/weekly and reward-risk guards with <=1% trade risk.",
        )

    def _account_check(self):
        broker = self.runtime.session.engine.paper_broker
        clean = broker.cash > 0 and broker.position_quantity == 0 and broker.position_cost_basis == 0
        return self._check(
            "paper_account", clean,
            "Paper account has positive cash and no unexpected open position.",
            "Paper account is not in the expected clean initial state; restore/reconcile intentionally before proceeding.",
        )

    def _checkpoint_check(self):
        store = self.runtime.checkpoint_store
        if store is None:
            return self._check("checkpoint", False, "", "Checkpoint store is required for real-time paper pre-flight.")
        path = Path(store.path)
        try:
            path.parent.mkdir(parents=True, exist_ok=True)
            with tempfile.NamedTemporaryFile(dir=path.parent, prefix=".preflight-", delete=True):
                pass
            ok = True
        except OSError:
            ok = False
        return self._check(
            "checkpoint", ok,
            "Checkpoint destination is writable.",
            "Checkpoint destination is not writable.",
        )

    def _execution_check(self):
        return self._check(
            "execution_lock", not self.execution_enabled,
            "Order execution is hard-disabled for pre-flight dry-run.",
            "Order execution must be disabled during pre-flight.",
        )

    def _connectivity_check(self):
        if not callable(self.connectivity_probe):
            return self._check("connectivity", False, "", "A connectivity/subscription probe is required.")
        try:
            result = self.connectivity_probe()
            ok = result is True
        except Exception:
            ok = False
        return self._check(
            "connectivity", ok,
            "Provider connectivity/authentication/subscription probe passed.",
            "Provider connectivity/authentication/subscription probe failed.",
        )

    def _runtime_check(self):
        ok = not self.runtime.stop_requested and self.runtime.health.status in {"STARTING", "HEALTHY"}
        return self._check(
            "runtime_state", ok,
            "Runtime is startable and not halted.",
            "Runtime is stopping, degraded or halted; resolve state before pre-flight.",
        )

    def run(self):
        checks = (
            self._credentials_check(), self._scope_check(), self._risk_check(),
            self._account_check(), self._checkpoint_check(), self._execution_check(),
            self._connectivity_check(), self._runtime_check(),
        )
        return PreFlightReport("PASS" if all(c.status == "PASS" for c in checks) else "FAIL", checks)
