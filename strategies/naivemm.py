from .strategies import Strategy
from order_book import OrderBook
from agents import Agent
from models import Order, Request, ReqType, OrdType, Side

import random 

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
            seed: int | None = None,
            ):
        self.half_spread = half_spread
        self.time_req = time_req
        self.tolerance = tolerance
        self.quantity = quantity
        self.rng = random.Random(seed)


    def decide(self, agent: Agent, book: OrderBook, timestamp: int) -> Request | None:
        # check if the market has liquidity
        if book.mid_price is None:
            return None

        # get the desired spread
        ask = book.mid_price + self.half_spread
        bid = book.mid_price - self.half_spread

        # cancel a bad order
        # asks - smaller asks are worse than larger asks. 
        # find the smallest ask that was created enough time ago
        
        worst_ask = max(
            (x for x in agent.open_asks if (timestamp >= x.creation_time + self.time_req)), 
                key=lambda x: abs(x.price - ask), default=None
            )
        if worst_ask is not None:
            ask_diff = abs(worst_ask.price - ask)
        else:
            ask_diff = 0
        worst_bid = max(
                    (x for x in agent.open_bids if (timestamp >= x.creation_time + self.time_req)), 
                        key=lambda x: abs(x.price - bid), default=None
                    )
        if worst_bid is not None:
            bid_diff = abs(worst_bid.price - bid)
        else:
            bid_diff = 0


        if ask_diff > bid_diff:
            if ask_diff > self.tolerance:
                return Request(req_type=ReqType.CANCEL, order=worst_ask)
        elif bid_diff > ask_diff:
            if bid_diff > self.tolerance:
                return Request(req_type=ReqType.CANCEL, order=worst_bid)
        elif ask_diff > self.tolerance:
            rng = random.randint(0, 1)
            order = worst_ask if rng == 0 else worst_bid
            return Request(req_type=ReqType.CANCEL, order=order)


        # Place a new order:
        good_ask = False
        for order in agent.open_asks:
            if order.price == ask:
                good_ask = True
                break
        good_bid = False
        for order in agent.open_bids:
            if order.price == bid:
                good_bid = True
                break

        if not good_ask and not good_bid:
            rng = self.rng.randint(0, 1)
            if rng == 0:
                side = Side.ASK
            else:
                side = Side.BID

        elif good_ask:
            side = Side.BID

        elif good_bid:
            side = Side.ASK

        else:
            return None

        if side == Side.ASK:
            price = ask
            quantity = min(agent.effective_position, self.quantity)
        else:
            price = bid
            quantity = min(agent.effective_cash // bid, self.quantity)

        if quantity == 0:
            return None

        return Request(req_type=ReqType.PLACE, 
                        order=Order(
            quantity=quantity,
            side=side,
            ord_type=OrdType.LIMIT,
            agent_id=agent.agent_id,
            price=price,
        ))
        



