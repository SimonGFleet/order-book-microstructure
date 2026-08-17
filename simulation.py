from order_book import OrderBook
from agents import Agent
from models import MatchResult, Order, OrdType, Request, ReqType, Side, Trade, SimulationSnapshot


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
        self.sim_history: list[SimulationSnapshot] = []

        self.order_count = 0
        self.timestamp = 0




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
            result: MatchResult = self.book.match_order(req.order, budget=self.agents[req.order.agent_id].effective_cash)
            self.apply_trades(result.trades)
            self.update_agent_open_orders(result.completed_orders, req.order)
            agent = self.agents[req.order.agent_id]
            if req.order.ord_type == OrdType.MARKET:
                if req.order.side == Side.BID:
                    agent.effective_cash -= sum(
                        trade.price * trade.quantity for trade in result.trades
                        )
                    
                elif req.order.side == Side.ASK:
                    agent.effective_position -= sum(
                        trade.quantity for trade in result.trades
                        )
                else:
                    raise ValueError("Invalid order side")

            elif req.order.ord_type == OrdType.LIMIT:
                if req.order.side == Side.BID:
                    trade_cost = sum(trade.price * trade.quantity for trade in result.trades)
                    remaining_price = req.order.price * req.order.remaining_qty
                    agent.effective_cash -= trade_cost + remaining_price
                else:
                    agent.effective_position -= req.order.quantity
            
        else:
            raise ValueError("Request of invalid type")

        

    def update_agent_open_orders(self, completed: list[Order], new: Order):
        while completed: # remove completed orders from the agent's open orders
            current: Order = completed.pop()
            if current.side == Side.BID:
                if current in self.agents[current.agent_id].open_bids:
                    self.agents[current.agent_id].open_bids.remove(current)
            elif current.side == Side.ASK:
                if current in self.agents[current.agent_id].open_asks:
                    self.agents[current.agent_id].open_asks.remove(current)
            else:
                raise ValueError("Invalid order side")
            
        # add the new order to agent's open orders
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


    def run_sim(self, steps: int) -> None:
        # at each step we call get_requests and apply_request
        for i in range(steps):
            trades_before = len(self.book.trades)

            # at each step we get requests, then apply a request
            self.get_requests()
            while self.requests:
                self.apply_request()

            # Create snapshots
            self.sim_history.append(self.get_sim_snapshot(trades_before=trades_before))
            
        
            self.timestamp += 1


    def get_sim_snapshot(self, trades_before: int) -> SimulationSnapshot:
        sim_snap = SimulationSnapshot(
            timestamp=self.timestamp,
            best_bid=self.book.biggest_bid(),
            best_ask=self.book.smallest_ask(),
            )
        if sim_snap.best_bid is not None and sim_snap.best_ask is not None:                       # if we can: fetch mid price and spread.
            sim_snap.spread = sim_snap.best_ask - sim_snap.best_bid
            sim_snap.mid_price = (sim_snap.best_ask + sim_snap.best_bid) / 2

        sim_snap.trade_count = len(self.book.trades) - trades_before

        return sim_snap
        

        

    def get_agent_snapshot(self):
        pass

    def get_agents_snapshot(self):
        for agent in self.agents:
            self.get_agent_snapshot(agent)


    def plot_midprice(self):
        timestamps = [snap.timestamp for snap in self.sim_history]
        mid_prices = [snap.mid_price for snap in self.sim_history]

        plt.plot(timestamps, mid_prices)
        plt.xlabel("Time Steps")
        plt.ylabel("Price")
        plt.title("Mid Price over Time")

    def plot_best_bids(self):
        timestamps = [snap.timestamp for snap in self.sim_history]
        best_bids = [snap.best_bid for snap in self.sim_history]

        plt.plot(timestamps, best_bids)
        plt.xlabel("Time Steps")
        plt.ylabel("Price")
        plt.title("Best Bids over Time")

    def plot_best_asks(self):
        timestamps = [snap.timestamp for snap in self.sim_history]
        best_asks = [snap.best_ask for snap in self.sim_history]

        plt.plot(timestamps, best_asks)
        plt.xlabel("Time Steps")
        plt.ylabel("Price")
        plt.title("Best Asks over Time")

    def plot_spread(self):
        timestamps = [snap.timestamp for snap in self.sim_history]
        spreads = [snap.spread for snap in self.sim_history]

        plt.plot(timestamps, spreads)
        plt.xlabel("Time Steps")
        plt.ylabel("Spread")
        plt.title("Spread over Time")

    def plot_trade_count(self):
        timestamps = [snap.timestamp for snap in self.sim_history]
        trade_counts = [snap.trade_count for snap in self.sim_history]

        plt.plot(timestamps, trade_counts)
        plt.xlabel("Time Steps")
        plt.ylabel("Number")
        plt.title("Trade counts over Time")


            
