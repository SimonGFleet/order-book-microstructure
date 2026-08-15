from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from strategies import Strategy
from collections import deque
from dataclasses import dataclass, field
from enum import Enum, auto
from order_book import OrderBook, OrdType, Order, Side
from requestsobj import Request, ReqType




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

        if request is None:
            return None
        else:
            request: Request
        # options: cancel / place
        if request.req_type == ReqType.PLACE:
            if request.order.ord_type == OrdType.MARKET:
                # if its a bid we need a maximum cash we can buy. 
                # if its an ask we need to adjust the effective cash when it runs out - if the trade doesnt go fully through
                pass
            else:   #limit
                if request.order.side == Side.BID:
                    self.effective_cash -= request.order.price * request.order.quantity
                else:
                    self.effective_position -= request.order.quantity

                    

        return request
