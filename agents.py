from collections import deque
from dataclasses import dataclass, field
from enum import Enum



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

