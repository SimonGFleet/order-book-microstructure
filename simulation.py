from order_book import OrderBook
from traders import Trader
from models import MatchResult, Order, OrdType, Request, ReqType, Side, Trade, SimulationSnapshot, TraderSnapshot

from collections import deque
import random
import hashlib
import json
import secrets
from matplotlib import pyplot as plt
import mesa
import heapq


class Simulation(mesa.Model):
    def __init__(self, initial_price: int = 100, seed: int | None = None):
        if seed is not None and (isinstance(seed, bool) or not isinstance(seed, int)):
            raise TypeError("seed must be an integer or None")
        self.seed = secrets.randbits(128) if seed is None else seed
        self._random_streams: dict[tuple[str, int | None], random.Random] = {}
        super().__init__(rng=self._derive_seed("request_ordering", None))
        self._random_streams[("request_ordering", None)] = self.random
        self.book: OrderBook = OrderBook()
        self.traders: dict[int, Trader] = {} # key = trader_id
        self.requests: list[Request] = [] # heap of requests waiting to be applied with their arrival time as the differentiator
        self.sim_history: list[SimulationSnapshot] = []
        
        self.order_count = 0
        self.timestamp = 0
        self.initial_price = initial_price

    def _derive_seed(self, purpose: str, trader_id: int | None) -> int:
        # Version the encoding: changing it changes every experiment's streams.
        key = json.dumps(["order-book-rng-v1", self.seed, purpose, trader_id],
                         separators=(",", ":")).encode("utf-8")
        return int.from_bytes(hashlib.sha256(key).digest(), "big")

    def get_rng(self, purpose: str, trader_id: int | None = None) -> random.Random:
        """Return a persistent stream independent of other streams' creation/draw order."""
        key = (purpose, trader_id)
        if key not in self._random_streams:
            self._random_streams[key] = random.Random(self._derive_seed(purpose, trader_id))
        return self._random_streams[key]






    def get_requests(self) -> None:
        '''Goes through each trader, checks when they can next make a request
        if they can, they are asked for a decision, 
        if not none, its pushed to the requests heap in the form: (arrival_time, request)'''
        
        for trader in self.traders.values():
            if trader.next_request_time <= self.timestamp:
                decision = trader.decide_action(self.book, self.timestamp)
            else:
                continue

            if decision is None:
                continue

            if decision.req_type == ReqType.PLACE:          # add order_id
                decision.order.order_id = self.order_count
                decision.order.creation_time = self.timestamp
                self.order_count += 1
            
            heapq.heappush(self.requests, decision)  # add request


    def apply_requests(self) -> None:
        '''Pops from requests until the lowest arrival time is after the current timestamp
        saves these to a temporary array, shuffles, then applies one at a time.
        Shuffling randomizes processing order reproducibly using the simulation seed.'''
        reqs_to_apply: list[Request] = []

        while self.requests and self.requests[0].arrival_time <= self.timestamp:
            reqs_to_apply.append(heapq.heappop(self.requests))   # the request is the second part

        self.random.shuffle(reqs_to_apply)
        for request in reqs_to_apply:
            self.apply_request(request)

    
    def apply_request(self, req: Request) -> None:
        '''Takes in a specific request, will always be Request object, and will have arrival_time <= sim timestamp
        Processes the request and updates the traders attributes'''

        if req.req_type == ReqType.CANCEL: # cancel: needs to remove the order from the book, then change the effective stats.
            order: Order = self.book.cancel_order(req.order)
            if order.cancelled:
                if order.side == Side.BID: # if we stop our buy, then we should gain effective cash again, 
                    self.traders[order.trader_id].effective_cash += order.remaining_qty * order.price
                    self.traders[order.trader_id].open_bids.remove(order)
                elif order.side == Side.ASK:
                    self.traders[order.trader_id].effective_position += order.remaining_qty
                    self.traders[order.trader_id].open_asks.remove(order)
                else:
                    raise ValueError("Invalid order type")

        elif req.req_type == ReqType.PLACE:
            result: MatchResult = self.book.match_order(req.order, budget=self.traders[req.order.trader_id].effective_cash)
            self.apply_trades(result.trades)
            self.update_trader_open_orders(result.completed_orders, req.order)
            trader = self.traders[req.order.trader_id]
            if req.order.ord_type == OrdType.MARKET:
                if req.order.side == Side.BID:
                    trader.effective_cash -= sum(
                        trade.price * trade.quantity for trade in result.trades
                        )
                    
                elif req.order.side == Side.ASK:
                    trader.effective_position -= sum(
                        trade.quantity for trade in result.trades
                        )
                else:
                    raise ValueError("Invalid order side")

            elif req.order.ord_type == OrdType.LIMIT:
                if req.order.side == Side.BID:
                    trade_cost = sum(trade.price * trade.quantity for trade in result.trades)
                    remaining_price = req.order.price * req.order.remaining_qty
                    trader.effective_cash -= trade_cost + remaining_price
                else:
                    trader.effective_position -= req.order.quantity
            
        else:
            raise ValueError("Request of invalid type")

        

    def update_trader_open_orders(self, completed: list[Order], new: Order) -> None:
        while completed: # remove completed orders from the trader's open orders
            current: Order = completed.pop()
            if current.side == Side.BID:
                if current in self.traders[current.trader_id].open_bids:
                    self.traders[current.trader_id].open_bids.remove(current)
            elif current.side == Side.ASK:
                if current in self.traders[current.trader_id].open_asks:
                    self.traders[current.trader_id].open_asks.remove(current)
            else:
                raise ValueError("Invalid order side")
            
        # add the new order to trader's open orders
        if new.remaining_qty > 0 and new.ord_type == OrdType.LIMIT:
            if new.side == Side.BID:
                self.traders[new.trader_id].open_bids.append(new)
            elif new.side == Side.ASK:
                self.traders[new.trader_id].open_asks.append(new)
            else:
                raise ValueError("Invalid order side")
        
    def apply_trades(self, trades: list[Trade]) -> None:
        # goes through the list of trades, possibly empty
        # can just go until empty applying in any order since its just record keeping.
        for trade in trades:
            # apply to both buyer and seller.
            if trade.buyer_trader_id is None:
                raise ValueError("No buyer trader id")
            if trade.seller_trader_id is None:
                raise ValueError("No seller trader id")

            price = trade.quantity * trade.price
            qty = trade.quantity

            # update the actual stats
            self.traders[trade.buyer_trader_id].current_cash -= price
            self.traders[trade.buyer_trader_id].current_position += qty
            self.traders[trade.seller_trader_id].current_cash += price
            self.traders[trade.seller_trader_id].current_position -= qty

            # also update the effective position/cash - effective is what we use to guage whether someone can buy
            self.traders[trade.buyer_trader_id].effective_position += qty
            self.traders[trade.seller_trader_id].effective_cash += price


    def run_sim(self, steps: int) -> None:
        # at each step we call get_requests and apply_request
        for i in range(steps):
            trades_before = len(self.book.trades)

            # update mid_price
            self.book.get_mid_price()

            # at each step we get requests, then apply the appropriately timed ones
            self.get_requests()
            self.apply_requests()

            

            # Create snapshots
            self.sim_history.append(self.get_sim_snapshot(trades_before=trades_before))
            self.get_traders_snapshot()  # appends individual snapshots to each trader
        
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

        
    def get_trader_snapshot(self, trader: Trader) -> TraderSnapshot:
        
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

        wealth = trader.current_cash + trader.current_position * price
        pnl = wealth - (trader.initial_cash + trader.initial_position * self.initial_price)

        return TraderSnapshot(
                    timestamp=self.timestamp,
                    current_cash=trader.current_cash,
                    current_position=trader.current_position,
                    effective_cash=trader.effective_cash,
                    effective_position=trader.effective_position,
                    wealth=wealth,
                    pnl=pnl,
                )

    def get_traders_snapshot(self) -> None:
        for trader_id in self.traders:
            trader = self.traders[trader_id]
            trader.snapshots.append(self.get_trader_snapshot(trader))
