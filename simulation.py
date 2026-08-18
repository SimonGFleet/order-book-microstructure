from order_book import OrderBook
from agents import Agent
from models import MatchResult, Order, OrdType, Request, ReqType, Side, Trade, SimulationSnapshot, AgentSnapshot

from collections import deque
import random
from matplotlib import pyplot as plt


class Simulation:
    def __init__(self, initial_price: int = 100):
        self.book: OrderBook = OrderBook()
        self.agents: dict[int, Agent] = {} # key = agent_id 
        self.requests: deque[Request] = deque() # queue of orders waiting to be applied
        self.sim_history: list[SimulationSnapshot] = []

        self.order_count = 0
        self.timestamp = 0
        self.initial_price = initial_price




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

    
    
    def apply_request(self) -> None:
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

        

    def update_agent_open_orders(self, completed: list[Order], new: Order) -> None:
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
        
    def apply_trades(self, trades: list[Trade]) -> None:
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
            self.get_agents_snapshot()  # appends individual snapshots to each agent
        
            self.timestamp += 1





    def get_sim_snapshot(self, trades_before: int) -> SimulationSnapshot:
        sim_snap = SimulationSnapshot(
            timestamp=self.timestamp,
            best_bid=self.book.biggest_bid(),
            best_ask=self.book.smallest_ask(),
            )
        if sim_snap.best_bid is not None and sim_snap.best_ask is not None:     # if we can: fetch mid price and spread.
            sim_snap.spread = sim_snap.best_ask - sim_snap.best_bid
            sim_snap.mid_price = (sim_snap.best_ask + sim_snap.best_bid) / 2

        sim_snap.trade_count = len(self.book.trades) - trades_before

        return sim_snap

        
    def get_agent_snapshot(self, agent: Agent) -> AgentSnapshot:
        
        # Get appropriate price
        best_bid = self.book.biggest_bid()
        best_ask = self.book.smallest_ask()
        if best_bid is not None and best_ask is not None:
            price = (best_ask + best_bid) / 2

        elif best_bid is not None:
            price = best_bid

        elif best_ask is not None:
            price = best_ask

        else:
            price = self.initial_price

        wealth = agent.current_cash + agent.current_position * price
        pnl = wealth - (agent.initial_cash + agent.initial_position * self.initial_price)

        return AgentSnapshot(
                    timestamp=self.timestamp,
                    current_cash=agent.current_cash,
                    current_position=agent.current_position,
                    effective_cash=agent.effective_cash,
                    effective_position=agent.effective_position,
                    wealth=wealth,
                    pnl=pnl,
                )

    def get_agents_snapshot(self) -> None:
        for id in self.agents:
            agent = self.agents[id]
            agent.snapshots.append(self.get_agent_snapshot(agent))