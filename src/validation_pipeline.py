from out_of_sample import OutOfSampleValidator
from walk_forward import WalkForwardValidator
from falsification import StatisticalFalsificationEngine
from backtest import BacktestingEngine


class ValidationPolicy:
    """Transparent policy for classifying research evidence.

    Hard rejection gates require positive unseen absolute return, positive unseen
    excess return, and statistical falsification evidence. Walk-forward
    persistence distinguishes VALIDATED from CONDITIONAL once those hard gates
    pass. Monte Carlo drawdown is reported but intentionally not used as a gate
    until the Risk Engine defines normalized drawdown tolerances.
    """

    VALIDATED = "VALIDATED"
    CONDITIONAL = "CONDITIONAL"
    REJECTED = "REJECTED"

    def __init__(self, min_positive_walk_forward_excess_rate=0.60):
        value = min_positive_walk_forward_excess_rate
        if not isinstance(value, (int, float)) or isinstance(value, bool):
            raise TypeError("Minimum positive walk-forward excess rate must be a number.")
        value = float(value)
        if not 0.0 <= value <= 1.0:
            raise ValueError("Minimum positive walk-forward excess rate must be between 0 and 1.")
        self.min_positive_walk_forward_excess_rate = value

    def classify(self, oos_result, walk_forward_result, falsification_result):
        oos_return = oos_result["out_of_sample"]["comparison"]["strategy_return"]
        oos_excess = oos_result["out_of_sample"]["comparison"]["excess_return"]
        persistence = walk_forward_result["summary"]["positive_test_excess_rate"]
        statistical_pass = falsification_result["passes_statistical_falsification"]

        gates = {
            "positive_oos_return": oos_return > 0.0,
            "positive_oos_excess_return": oos_excess > 0.0,
            "passes_statistical_falsification": bool(statistical_pass),
            "walk_forward_persistence": persistence >= self.min_positive_walk_forward_excess_rate,
        }

        hard_gate_names = (
            "positive_oos_return",
            "positive_oos_excess_return",
            "passes_statistical_falsification",
        )
        hard_gates_pass = all(gates[name] for name in hard_gate_names)

        if not hard_gates_pass:
            status = self.REJECTED
        elif gates["walk_forward_persistence"]:
            status = self.VALIDATED
        else:
            status = self.CONDITIONAL

        return {
            "status": status,
            "gates": gates,
            "thresholds": {
                "min_positive_walk_forward_excess_rate": self.min_positive_walk_forward_excess_rate,
            },
        }


class StrategyValidationPipeline:
    """Orchestrate Phase 3 validation without changing strategy logic."""

    def __init__(
        self,
        strategy_engine,
        train_size,
        test_size,
        step_size=None,
        expanding=True,
        in_sample_fraction=0.70,
        initial_capital=10000.0,
        commission_rate=0.0,
        slippage_rate=0.0,
        spread_rate=0.0,
        simulations=1000,
        confidence_level=0.95,
        random_seed=42,
        min_positive_walk_forward_excess_rate=0.60,
        execution_timing=BacktestingEngine.SAME_BAR_CLOSE,
        risk_engine=None,
        risk_stop_column="Stop",
        risk_target_column="Target",
        protective_exit_policy=None,
    ):
        self.strategy_engine = strategy_engine
        self.oos_validator = OutOfSampleValidator(
            strategy_engine,
            in_sample_fraction=in_sample_fraction,
            initial_capital=initial_capital,
            commission_rate=commission_rate,
            slippage_rate=slippage_rate,
            spread_rate=spread_rate,
            execution_timing=execution_timing,
            risk_engine=risk_engine,
            risk_stop_column=risk_stop_column,
            risk_target_column=risk_target_column,
            protective_exit_policy=protective_exit_policy,
        )
        self.walk_forward_validator = WalkForwardValidator(
            strategy_engine,
            train_size=train_size,
            test_size=test_size,
            step_size=step_size,
            expanding=expanding,
            initial_capital=initial_capital,
            commission_rate=commission_rate,
            slippage_rate=slippage_rate,
            spread_rate=spread_rate,
            execution_timing=execution_timing,
            risk_engine=risk_engine,
            risk_stop_column=risk_stop_column,
            risk_target_column=risk_target_column,
            protective_exit_policy=protective_exit_policy,
        )
        self.falsification_engine = StatisticalFalsificationEngine(
            simulations=simulations,
            confidence_level=confidence_level,
            random_seed=random_seed,
        )
        self.policy = ValidationPolicy(min_positive_walk_forward_excess_rate)

    @staticmethod
    def _strategy_name(strategy_engine):
        name = getattr(strategy_engine, "strategy_name", None)
        if name:
            return name
        return strategy_engine.__class__.__name__

    @staticmethod
    def _collect_walk_forward_test_trades(walk_forward_result):
        trades = []
        for window in walk_forward_result["windows"]:
            trades.extend(window["test"]["trade_history"])
        return trades

    def run(self, data):
        oos = self.oos_validator.run(data)
        walk_forward = self.walk_forward_validator.run(data)

        # Falsification consumes repeated unseen walk-forward trades only. This
        # prevents in-sample trades from strengthening statistical evidence.
        unseen_trades = self._collect_walk_forward_test_trades(walk_forward)
        falsification = self.falsification_engine.analyze(unseen_trades)
        classification = self.policy.classify(oos, walk_forward, falsification)

        return {
            "strategy": self._strategy_name(self.strategy_engine),
            "out_of_sample": oos,
            "walk_forward": walk_forward,
            "falsification": falsification,
            "classification": classification,
        }
