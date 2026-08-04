from order_book import Order, Trade, OrderBook
from agents import Agent

from collections import deque
from dataclasses import dataclass
from enum import Enum

class ReqType(Enum):
    CANCEL = 'cancel'
    PLACE = 'place'

@dataclass
class Request:
    req_type: ReqType
    order: Order

class Simulation:
    def __init__(self):
        self.book: OrderBook = OrderBook()
        self.agents: dict[int, Agent] = {} # key = agent_id 
        self.requests: deque[Request] = deque() # queue of orders waiting to be applied



    def get_requests(self):
        # should loop through the agents and check if any of them want to make a request
        # ignoring the potential latency of each agent, it should get in a list/queue of orders to be executed, then randomise it
        # has the ability to see if the agent wants to cancel their current (limit) order
        pass 

    def apply_request(self):
        # might be apply just one order at a time, then the timestep increases
        # we only do one order at a time so that agents can submit or cancel orders at each time step 
        # they can see what the market looks like
        if not self.requests: 
            return

        req: Request = self.requests.popleft()
        if req.req_type == ReqType.CANCEL:
            self.book.cancel_order(req.order)
        elif req.req_type == ReqType.PLACE:
            trades: list[Trade] = self.book.match_order(req.order)
            self.apply_trades(trades)
        else:
            raise ValueError("Request of invalid type")
        
    def apply_trades(self, trades: list[Trade]):
        # goes through the list of trades, possibly empty
        # can just go until empty applying in any order since its just record keeping.
        for trade in trades:
            # apply to both buyer and seller.
            if trade.buy_agent_id is None:
                raise ValueError("No buyer agent id")
            if trade.sell_agent_id is None:
                raise ValueError("No seller agent id")

            self.agents[trade.buy_agent_id].current_cash -= trade.quantity * trade.price
            self.agents[trade.buy_agent_id].position += trade.quantity
            self.agents[trade.sell_agent_id].current_cash += trade.quantity * trade.price
            self.agents[trade.sell_agent_id].position -= trade.quantity



    def run_sim(self, steps: int):
        # at each step we call get_requests and apply_request
        pass
        