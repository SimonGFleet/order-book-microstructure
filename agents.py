from collections import deque
from dataclasses import dataclass, field
from enum import Enum
from order_book import OrderBook


class Strategies(Enum):
    NONE = 0
    RANDOM = 1
    MARKET_MAKER = 2
    MOMENTUM = 3



strategy_classes = {}

@dataclass
class Agent:
    agent_id: int
    initial_cash: int
    strategy: Strategies = Strategies.NONE
    position: int = 0
    current_cash: int = field(init=False)

    def __post_init__(self) -> None:
        self.current_cash = self.initial_cash

    def decide_action(self, book: OrderBook):
        # want this to call the strategy and get the result,
        # then the simulation will call this agent.decide_action and get the request / None that is made.
        # we should be making a request object - see simulation.py
        result = None