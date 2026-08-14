from order_book import Order, Trade, OrderBook, Side, MatchResult, OrdType
from agents import Agent
from requestsobj import ReqType, Request


from collections import deque
from dataclasses import dataclass
from enum import Enum
import random
from matplotlib import pyplot as plt

class Simulation:
    def __init__(self):
        self.book: OrderBook = OrderBook()
        self.agents: dict[int, Agent] = {} # key = agent_id 
        self.requests: deque[Request] = deque() # queue of orders waiting to be applied

        self.order_count = 0
        self.timestamp = 0

        # Stats for viewing
        self.best_bids = []
        self.best_asks = []
        self.spreads = []
        self.mid_prices = []
        self.trade_counts = []




    def get_requests(self) -> None:
        temp_requests: list[Request] = []
        
        for agent in self.agents.values():
            decision = agent.decide_action(self.book)

            if decision is not None:

                if decision.req_type == ReqType.PLACE:          # add order_id
                    decision.order.order_id = self.order_count
                    decision.order.creation_time = self.timestamp
                    self.order_count += 1
                
                temp_requests.append(decision)  # add order to current requests

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
                    self.agents[order.agent_id].open_bids.remove(order)
                elif order.side == Side.ASK:
                    self.agents[order.agent_id].effective_position += order.remaining_qty
                    self.agents[order.agent_id].open_asks.remove(order)
                else:
                    raise ValueError("Invalid order type")

        elif req.req_type == ReqType.PLACE:
            result: MatchResult = self.book.match_order(req.order)
            self.apply_trades(result.trades)
            self.update_agent_open_orders(result.completed_orders, req.order)
            
            
        else:
            raise ValueError("Request of invalid type")

    def update_agent_open_orders(self, completed: list[Order], new: Order):
        while completed: # pop off end to get current order, then remove from agent.
            current: Order = completed.pop()
            if current.side == Side.BID:
                if current in self.agents[current.agent_id].open_bids:
                    self.agents[current.agent_id].open_bids.remove(current)
            elif current.side == Side.ASK:
                if current in self.agents[current.agent_id].open_asks:
                    self.agents[current.agent_id].open_asks.remove(current)
            else:
                raise ValueError("Invalid order side")

        if new.remaining_qty > 0 and new.ord_type == OrdType.LIMIT:
            if new.side == Side.BID:
                self.agents[new.agent_id].open_bids.append(new)
            elif new.side == Side.ASK:
                self.agents[new.agent_id].open_asks.append(new)
            else:
                raise ValueError("Invalid order side")
        
    def apply_trades(self, trades: list[Trade]):
        # goes through the list of trades, possibly empty
        # can just go until empty applying in any order since its just record keeping.
        for trade in trades:
            # apply to both buyer and seller.
            if trade.buy_agent_id is None:
                raise ValueError("No buyer agent id")
            if trade.sell_agent_id is None:
                raise ValueError("No seller agent id")

            price = trade.quantity * trade.price
            qty = trade.quantity

            # update the actual stats
            self.agents[trade.buy_agent_id].current_cash -= price
            self.agents[trade.buy_agent_id].current_position += qty
            self.agents[trade.sell_agent_id].current_cash += price
            self.agents[trade.sell_agent_id].current_position -= qty

            # also update the effective position/cash - effective is what we use to guage whether someone can buy
            self.agents[trade.buy_agent_id].effective_position += qty
            self.agents[trade.sell_agent_id].effective_cash += price


    def run_sim(self, steps: int, vb: bool = True):
        
        current_trades = 0
        # at each step we call get_requests and apply_request
        for i in range(steps):
            # at each step we get requests, then apply a request
            self.get_requests()

            while self.requests:
                self.apply_request()

            best_bid = self.book.biggest_bid()
            best_ask = self.book.smallest_ask()

            self.best_bids.append(best_bid)
            self.best_asks.append(best_ask)
            if best_bid and best_ask:                       # if we can: fetch mid price and spread.
                self.spreads.append(best_ask - best_bid)
                self.mid_prices.append((best_ask + best_bid) / 2)
            else:
                self.spreads.append(None)
                self.mid_prices.append(None) # still need to append something to correctly view the time series

            trades_this_step = len(self.book.trades) - current_trades # feels like a long way of doing this
            current_trades += trades_this_step
            self.trade_counts.append(trades_this_step)

            self.timestamp += 1


            
            
    def plot(self, var):
        conv = {"trade counts": self.trade_counts, 
                "best bids": self.best_bids, 
                "best asks" : self.best_asks, 
                "price": self.mid_prices, 
                "spread" : self.spreads}
        if var not in conv:
            raise ValueError("Invalid statistic to plot")

        plt.plot(conv[var])
        plt.xlabel("Time Steps")
        plt.ylabel(var)
        plt.title(var + "over time")

