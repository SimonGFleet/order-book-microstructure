from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from strategies import Strategy
from collections import deque
from dataclasses import dataclass, field
from enum import Enum, auto
from order_book import OrderBook
from models import Order, Request




@dataclass
class Agent:
    agent_id: int
    initial_cash: int
    initial_position: int
    strategy: Strategy
    open_bids: list[Order] = field(default_factory=list)
    open_asks: list[Order] = field(default_factory=list)
    current_position: int = field(init=False)
    current_cash: int = field(init=False)
    effective_cash: int = field(init=False)
    effective_position: int = field(init=False)


    def __post_init__(self) -> None:
        self.current_cash = self.initial_cash
        self.effective_cash = self.initial_cash
        self.current_position = self.initial_position
        self.effective_position = self.initial_position

    def decide_action(self, book: OrderBook) -> Request | None:
        # want this to call the strategy and get the result,
        # then the simulation will call this agent.decide_action and get the request / None that is made.    
        request: Request | None = self.strategy.decide(self, book) # this should call the strategy

        return request
