from __future__ import annotations
from traders import Trader
from experiments.factory import factory
from collections import defaultdict
from dataclasses import dataclass
from simulation import Simulation
from strategies import Strategy, random_strat, inventorymm, naivemm
from enum import Enum
import statistics
from models import TraderResults


class IndependentVariableScope(Enum):
    TRADER = "trader"
    STRATEGY = "strategy"


'''target_cfg = {
    "strategy_name": "naive_mm",
    "trader_cfg": {
        "starting_position": 100,
        "starting_cash": 10000,
        "latency": None,
        "latency_dev": 5,
    },
    "strategy_cfg": {
        "half_spread": 2,
        "time_req": 5,
        "tolerance": 1,
        "quantity": 3,
    }
}'''

@dataclass
class TargetRandomConfig:
    buy_probability: float | None
    sell_probability: float | None
    cancel_probability: float | None
    limit_probability: float | None
    max_quantity: int | None
    max_price_offset: int | None
    reference_price: int | None


@dataclass
class TargetNaiveMMConfig:
    half_spread: int | None
    time_req: int | None
    tolerance: int | None
    quantity: int | None


@dataclass
class TargetInventoryMMConfig:
    half_spread: int | None
    time_req: int | None
    tolerance: int | None
    target_ratio: float | None
    ratio_error: float | None
    quantity: int | None

@dataclass
class TargetTraderConfig:
    initial_cash: int | None
    initial_position:int | None
    latency: int | None
    latency_deviation: int | None
    strategy: TargetRandomConfig | TargetNaiveMMConfig | TargetInventoryMMConfig
    trader_id: int = 0



class TargetTraderFactory:
    def __init__(self):
        self.strategy_builders = {
            TargetRandomConfig: self.create_random,
            TargetNaiveMMConfig: self.create_naive_mm,
            TargetInventoryMMConfig: self.create_inventory_mm,
        }

    def create_trader(self, cfg: TargetTraderConfig, sim: Simulation) -> Trader:
        strategy = self.create_strategy(cfg.strategy)

        return Trader(
            model=sim,
            trader_id=cfg.trader_id,
            initial_cash=cfg.initial_cash,
            initial_position=cfg.initial_position,
            latency=cfg.latency,
            latency_deviation=cfg.latency_deviation,
            strategy=strategy,
        )

    def create_strategy(self, cfg):
        try:
            builder = self.strategy_builders[type(cfg)]
        except KeyError:
            raise TypeError(f"Unsupported target strategy config: {type(cfg)}")

        return builder(cfg)

    def create_random(self, cfg: TargetRandomConfig):
        return random_strat.Random(
            buy_probability=cfg.buy_probability,
            sell_probability=cfg.sell_probability,
            cancel_probability=cfg.cancel_probability,
            limit_probability=cfg.limit_probability,
            max_quantity=cfg.max_quantity,
            max_price_offset=cfg.max_price_offset,
            reference_price=cfg.reference_price,
        )

    def create_naive_mm(self, cfg: TargetNaiveMMConfig):
        return naivemm.NaiveMM(
            half_spread=cfg.half_spread,
            time_req=cfg.time_req,
            tolerance=cfg.tolerance,
            quantity=cfg.quantity,
        )

    def create_inventory_mm(self, cfg: TargetInventoryMMConfig):
        return inventorymm.InventoryMM(
            half_spread=cfg.half_spread,
            time_req=cfg.time_req,
            tolerance=cfg.tolerance,
            target_ratio=cfg.target_ratio,
            ratio_error=cfg.ratio_error,
            quantity=cfg.quantity,
        )



class ExperimentTrader:
    def __init__(self, ind_var: str,
                 ind_var_values: list,
                 target_trader_parameters,
                 sim_config,
                 decision_seeds: list[int],
                 trader_parameter_seeds: list[int],
                 sim_steps: int,
                 ind_var_scope: IndependentVariableScope):
        self.ind_var = ind_var
        self.ind_var_values = ind_var_values
        self.target_trader_parameters = target_trader_parameters
        self.sim_config = sim_config
        self.decision_seeds = decision_seeds
        self.trader_parameter_seeds = trader_parameter_seeds
        self.sim_steps = sim_steps
        self.ind_var_scope = ind_var_scope
        self.total_runs = (len(self.ind_var_values) * len(self.decision_seeds) * len(self.trader_parameter_seeds))


    def run_experiment(self, verbose=False):
        main_results = {}
        completed_runs = 0
        next_percentage = 10

        target_cfg = self.initialise_target_trader_config()

        variable_cfg = (
            target_cfg.strategy
            if self.ind_var_scope is IndependentVariableScope.STRATEGY
            else target_cfg
        )

        if not hasattr(variable_cfg, self.ind_var):
            raise ValueError(
                f"{self.ind_var!r} is not a valid parameter for "
                f"{type(variable_cfg).__name__}"
            )

        for value in self.ind_var_values:
            setattr(variable_cfg, self.ind_var, value)
            results_for_independent_value: list[TraderResults] = []

            for decision_seed in self.decision_seeds:
                for parameter_seed in self.trader_parameter_seeds:
                    sim = factory(
                        self.sim_config,
                        decision_seed=decision_seed,
                        trader_parameter_seed=parameter_seed,
                    )
                    target_trader = self.create_target_trader(target_cfg, sim)
                    sim.traders[0] = target_trader

                    sim.run_sim(self.sim_steps)
                    results_for_seed = sim.results_for_trader(
                        trader_id=target_trader.trader_id
                    )
                    results_for_independent_value.append(results_for_seed)

                    completed_runs += 1

                    if verbose:
                        while (
                            next_percentage <= 100
                            and completed_runs * 100
                            >= next_percentage * self.total_runs
                        ):
                            print(
                                f"Experiment {next_percentage}% complete",
                                flush=True,
                            )
                            next_percentage += 10

            main_results[value] = self.get_statistics(
                results_for_independent_value
            )

        return main_results




    def get_statistics(self, results: list[TraderResults]) -> dict:
        summary = {}
        
        for metric in (
                "total_pnl",
                "avg_pnl",
                "sharpe_ratio",
                "drawdown",
                "buy_and_hold_pnl",
                "excess_pnl",
            ):
            values = [getattr(result, metric) for result in results]
            values = [value for value in values if value is not None]

            summary[metric] = {
                "count": len(values),
                "mean": statistics.mean(values) if values else None,
                "variance": statistics.variance(values) if len(values) >= 2 else None,
            }

        return summary



    def initialise_target_trader_config(self) -> TargetTraderConfig:
        strategy_config_map = {
            "random_trader": TargetRandomConfig,
            "naive_mm": TargetNaiveMMConfig,
            "inventory_aware_mm": TargetInventoryMMConfig,
        }

        params = self.target_trader_parameters
        strategy_cfg = strategy_config_map[params["strategy_name"]](
            **params["strategy_cfg"]
        )

        return TargetTraderConfig(
            **params["trader_cfg"],
            strategy=strategy_cfg,
        )

    def create_target_trader(self, cfg, sim) -> Trader:
        trader_factory = TargetTraderFactory()
        return trader_factory.create_trader(cfg, sim)


