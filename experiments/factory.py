'''Factory - function? should be able to create a simulation or populate it with traders that have strategies.
'''
from simulation import Simulation
from strategies import Strategy, random_strat, inventorymm, naivemm

from traders import Trader
import json
import random
from dataclasses import dataclass


'''config = {
    "random_trader" : {
            qty: 80,
            trader_cfg: {},
            strategy_cfg: {},
        },
    "naive_market_maker": {
            qty: 20,
            trader_cfg: {},
            strategy_cfg: {},
        },
    }'''


@dataclass
class TraderConfig:
    min_starting_position: int = 100
    max_starting_position: int = 100
    min_starting_cash: int = 10000
    max_starting_cash: int = 10000
    min_latency: int = 1
    max_latency: int = 100
    min_latency_dev: int = 0
    max_latency_dev: int = 20

@dataclass
class RandomConfig:
    min_buy_prob: float
    max_buy_prob: float
    min_sell_prob: float
    max_sell_prob: float
    min_cancel_prob: float
    max_cancel_prob: float
    min_limit_prob: float
    max_limit_prob: float
    min_max_quantity: int
    max_max_quantity: int
    min_max_price_offest: int
    max_max_price_offset: int
    reference_price: int

@dataclass
class NaiveMMConfig:
    min_half_spread: int
    max_half_spread: int
    min_time_req: int
    max_time_req: int
    min_tolerance: int
    max_tolerance: int
    min_quantity: int
    max_quantity: int


@dataclass
class InventoryMMConfig:
    min_half_spread: int
    max_half_spread: int
    min_time_req: int
    max_time_req: int
    min_tolerance: int
    max_tolerance: int
    min_quantity: int
    max_quantity: int
    min_target_ratio: float
    max_target_ratio: float
    min_ratio_error: float
    max_ratio_error: float


class ConfigParser:
    def __init__(self):
        self.map = {
            "random_trader": self.parse_random_trader,
            "naive_mm": self.parse_naive_mm,
            "inventory_aware_mm": self.parse_inventory_mm,
        }

    def parse_base_trader(self, config: dict) -> TraderConfig:
        try:
            return TraderConfig(**config)
        except TypeError as e:
            raise ValueError(f"Invalid trader configuration: {e}") from e
        

    def parse_random_trader(self, config: dict) -> RandomConfig:
        try:
            return RandomConfig(**config)
        except TypeError as e:
            raise ValueError(f"Invalid strategy configuration: {e}") from e
        

    def parse_naive_mm(self, config: dict):
        try:
            return NaiveMMConfig(**config)
        except TypeError as e:
            raise ValueError(f"Invalid strategy configuration: {e}") from e

        
    def parse_inventory_mm(self, config: dict):
        try:
            return InventoryMMConfig(**config)
        except TypeError as e:
            raise ValueError(f"Invalid strategy configuration: {e}") from e


class TraderFactory:
    def __init__(self, seed):
        self.rng = random.Random(seed)
        self.map = {
            "random_trader": self.create_random,
            "naive_mm": self.create_naive_mm,
            "inventory_aware_mm": self.create_inventory_mm,
        }

    def create_trader(self, data: tuple[str, TraderConfig, RandomConfig | NaiveMMConfig | InventoryMMConfig], id: int, sim: Simulation) -> Trader:
        # unpack data
        strat = self.map[data[0]]
        trader_cfg = data[1]
        strat_cfg = data[2]

        return Trader(model=sim,
                      trader_id=id,
                      initial_cash=self.rng.randint(trader_cfg.min_starting_cash, trader_cfg.max_starting_cash),
                      initial_position=self.rng.randint(trader_cfg.min_starting_position, trader_cfg.max_starting_position),
                      latency=self.rng.randint(trader_cfg.min_latency, trader_cfg.max_latency),
                      latency_deviation=self.rng.randint(trader_cfg.min_latency_dev, trader_cfg.max_latency_dev),
                      strategy=strat(strat_cfg),
                      )


    def create_random(self, data: RandomConfig) -> Strategy:
        min_total = data.min_buy_prob + data.min_sell_prob
        both_fixed = (data.min_buy_prob == data.max_buy_prob 
                      and data.min_sell_prob == data.max_sell_prob)
        

        if min_total > 1 or (min_total == 1 and not both_fixed):
            raise ValueError(
                "Buy/sell ranges must allow sampling probabilities "
                "whose sum is at most 1."
            )

        buy_prob = self.rng.uniform(data.min_buy_prob, data.max_buy_prob)
        sell_prob = self.rng.uniform(data.min_sell_prob, data.max_sell_prob)

        while buy_prob + sell_prob > 1:
            buy_prob = self.rng.uniform(data.min_buy_prob, data.max_buy_prob)
            sell_prob = self.rng.uniform(data.min_sell_prob, data.max_sell_prob)

        return random_strat.Random(
            buy_probability=buy_prob,
            sell_probability=sell_prob,
            cancel_probability=self.rng.uniform(data.min_cancel_prob, data.max_cancel_prob),
            limit_probability=self.rng.uniform(data.min_limit_prob, data.max_limit_prob),
            max_quantity=self.rng.randint(data.min_max_quantity, data.max_max_quantity),
            max_price_offset=self.rng.randint(data.min_max_price_offest, data.max_max_price_offset),
            reference_price=data.reference_price,
        )



    def create_naive_mm(self, data: NaiveMMConfig) -> Strategy:
        return naivemm.NaiveMM(
            half_spread=self.rng.randint(data.min_half_spread, data.max_half_spread),
            time_req=self.rng.randint(data.min_time_req, data.max_time_req),
            tolerance=self.rng.randint(data.min_tolerance, data.max_tolerance),
            quantity=self.rng.randint(data.min_quantity, data.max_quantity),
        )

    def create_inventory_mm(self, data: InventoryMMConfig) -> Strategy:
        return inventorymm.InventoryMM(
            half_spread=self.rng.randint(data.min_half_spread, data.max_half_spread),
            time_req=self.rng.randint(data.min_time_req, data.max_time_req),
            tolerance=self.rng.randint(data.min_tolerance, data.max_tolerance),
            target_ratio=self.rng.uniform(data.min_target_ratio, data.max_target_ratio),
            ratio_error=self.rng.uniform(data.min_ratio_error, data.max_ratio_error),
            quantity=self.rng.randint(data.min_quantity, data.max_quantity),
        )


def factory(sim_config: str, decision_seed, trader_parameter_seed) -> Simulation:
    '''
    parses the json into its appropriate strategies, 
    extracts the ranges of parameters to be used for each strategy type,
    creates a simulation then goes through the strategies and creates the traders

    Args: 
        - trader_config: JSON string holding the parameters we will want to use for creating the simulation
        - decision_seed: the seed given to all the traders with which they use to make their decision
        - trader_parameter_seed: the seed given when choosing what parameters the traders have from the ranges given
    
    Returns:
        Simulation object with traders attached'''
    sim: Simulation = Simulation(seed=decision_seed)
    parser: ConfigParser = ConfigParser()
    trader_factory: TraderFactory = TraderFactory(seed=trader_parameter_seed)

    trader_id = 1


    config = json.loads(sim_config)

    # create the config classes, get their quantities:
    config_classes = []


    for strategy in config:
        try:
            parse_function = parser.map[strategy]
        except KeyError:
            raise ValueError(f"Unknown trader strategy: {strategy}")

        qty = config[strategy]["quantity"]
        trader_cfg = parser.parse_base_trader(config[strategy]["trader_cfg"])
        strategy_cfg = parse_function(config[strategy]["strategy_cfg"])

        config_classes.append(((strategy, trader_cfg, strategy_cfg), qty))

    # config_classes now has config and qty
    for config, qty in config_classes:
        for i in range(qty):
            # pass in config to create trader:
            trader: Trader = trader_factory.create_trader(config, trader_id, sim=sim)
            sim.traders[trader_id] = trader
            trader_id += 1


    return sim
