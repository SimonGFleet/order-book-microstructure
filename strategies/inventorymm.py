from .strategies import Strategy
from .helper_functions import cancellation_request, placement_request
from order_book import OrderBook
from traders import Trader
from models import Order, Request, ReqType, OrdType, Side

import random 

# 1. should i cancel an order - copy in from naive strategy
# 2. get our current ratio
# 3. if the current ratio is off by a certain amount then we should place an order appropriately.
# 4. if we are balanced then we should see if we have orders in the right place, else place them

class InventoryMM(Strategy):
    def __init__(
            self,
            half_spread: int,
            time_req: int,
            tolerance: int,
            target_ratio: float,
            ratio_error: float,
            quantity: int,
            seed: int | None = None,
            ):
        self.half_spread = half_spread
        self.time_req = time_req
        self.tolerance = tolerance
        self.target_ratio = target_ratio
        self.ratio_error = ratio_error
        self.quantity = quantity
        self.rng = random.Random(seed)

    def decide(self, trader: Trader, book: OrderBook, timestamp: int) -> Request | None:
        if book.mid_price is None:
            return None

        ask = book.mid_price + self.half_spread
        bid = book.mid_price - self.half_spread

        cancel_request = cancellation_request(
            ask=ask,
            bid=bid,
            trader=trader,
            timestamp=timestamp,
            time_req=self.time_req,
            tolerance=self.tolerance,
            rng=self.rng,
        )
        if cancel_request is not None:
            return cancel_request

        # Inventory-aware order placement will go here.

        side = None

        
        stocks = trader.current_position * book.mid_price
        wealth = stocks + trader.current_cash
        ratio = stocks / wealth
        if abs(ratio - self.target_ratio) > self.ratio_error:
            if ratio - self.target_ratio > 0:   # too much in stocks
                side = Side.ASK
            else:
                side = Side.BID


        return placement_request(
            ask=ask,
            bid=bid,
            trader=trader,
            quantity=self.quantity,
            rng=self.rng,
            side=side
        )
