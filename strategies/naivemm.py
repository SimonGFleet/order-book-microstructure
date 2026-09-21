from __future__ import annotations

from .strategies import Strategy
from .helper_functions import cancellation_request, placement_request
from order_book import OrderBook
from traders import Trader
from models import Request


class NaiveMM(Strategy):
    '''This strategy does not care what its inventory looks like,
    it will submit around the midprice
    it will cancel orders that are not appropriately situated around the midprice'''
    def __init__(
            self,
            half_spread: int,
            time_req: int,
            tolerance: int,
            quantity: int,
            ):
        self.half_spread = half_spread
        self.time_req = time_req
        self.tolerance = tolerance
        self.quantity = quantity


    def decide(self, trader: Trader, book: OrderBook, timestamp: int) -> Request | None:
        # check if the market has liquidity
        if book.mid_price is None:
            return None

        # get the desired spread
        ask = book.mid_price + self.half_spread
        bid = book.mid_price - self.half_spread

        cancel_request = cancellation_request(
            ask=ask,
            bid=bid,
            trader=trader,
            timestamp=timestamp,
            time_req=self.time_req,
            tolerance=self.tolerance,
            rng=trader.strategy_rng,
        )
        if cancel_request is not None:
            return cancel_request


        return placement_request(
            ask=ask,
            bid=bid,
            trader=trader,
            quantity=self.quantity,
            rng=trader.strategy_rng,
        )
        
