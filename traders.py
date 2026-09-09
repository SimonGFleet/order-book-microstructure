from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from strategies import Strategy
from collections import deque
from dataclasses import dataclass, field
from enum import Enum, auto
from order_book import OrderBook
from models import Order, Request, TraderSnapshot
import random

import mesa


@dataclass(eq=False)
class Trader(mesa.Agent):
    model: mesa.Model
    trader_id: int
    initial_cash: int
    initial_position: int
    strategy: Strategy
    latency: int = 0
    latency_deviation: int = 0
    next_request_time: int = 0

    open_bids: list[Order] = field(default_factory=list)
    open_asks: list[Order] = field(default_factory=list)
    snapshots: list[TraderSnapshot] = field(default_factory=list)

    current_position: int = field(init=False)
    current_cash: int = field(init=False)
    effective_cash: int = field(init=False)
    effective_position: int = field(init=False)


    def __post_init__(self) -> None:
        super().__init__(self.model)
        self.current_cash = self.initial_cash
        self.effective_cash = self.initial_cash
        self.current_position = self.initial_position
        self.effective_position = self.initial_position

    def decide_action(self, book: OrderBook, timestep: int) -> Request | None:
        # want this to call the strategy and get the result,
        # then the simulation will call this trader.decide_action and get the request / None that is made.    
        request: Request | None = self.strategy.decide(self, book, timestep) # this should call the strategy

        latency: int = max(0, self.latency + 
                      random.randint(-self.latency_deviation, self.latency_deviation)) # if deviation is big, latency could go below zero meaning it would have a knock on effect
        if request is not None:
            request.arrival_time = timestep + latency
        self.next_request_time += latency + 1

        

        return request

    def step(self) -> None:
        request = self.decide_action(
            self.model.book,
            self.model.timestamp,
        )

        if request is not None:
            self.model.submit_request(request)