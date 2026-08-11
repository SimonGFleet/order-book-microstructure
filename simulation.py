from order_book import Order, Trade, OrderBook, Side
from agents import Agent
from requestsobj import ReqType, Request

from collections import deque
from dataclasses import dataclass
from enum import Enum
import random


class Simulation:
    def __init__(self):
        self.book: OrderBook = OrderBook()
        self.agents: dict[int, Agent] = {} # key = agent_id 
        self.requests: deque[Request] = deque() # queue of orders waiting to be applied



    def get_requests(self):
        temp_requests: list[Request] = []
        
        for agent in self.agents.values():
            decision = agent.decide_action(self.book)

            if decision is not None:
                temp_requests.append(decision)

        random.shuffle(temp_requests)
        self.requests += temp_requests

        return

    def apply_request(self):
        # might be apply just one order at a time, then the timestep increases
        # we only do one order at a time so that agents can submit or cancel orders at each time step 
        # they can see what the market looks like
        if not self.requests: 
            return

        req: Request = self.requests.popleft()
        if req.req_type == ReqType.CANCEL: # cancel: needs to remove the order from the book, then change the effective stats.
            order: Order = self.book.cancel_order(req.order)
            if order.cancelled:
                if order.side == Side.BID: # if we stop our buy, then we should gain effective cash again, 
                    self.agents[order.agent_id].effective_cash += order.remaining_qty * order.price
                elif order.side == Side.ASK:
                    self.agents[order.agent_id].effective_position += order.remaining_qty
                else:
                    raise ValueError("Invalid order type")

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
            self.agents[trade.buy_agent_id].current_position += trade.quantity
            self.agents[trade.sell_agent_id].current_cash += trade.quantity * trade.price
            self.agents[trade.sell_agent_id].current_position -= trade.quantity


    def run_sim(self, steps: int):
        # at each step we call get_requests and apply_request
        pass
        