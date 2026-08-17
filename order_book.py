from collections import deque
from operator import ge, le
from dataclasses import dataclass, field
from enum import Enum

class Side(Enum):
    BID = 'bid'
    ASK = 'ask'

class OrdType(Enum):
    MARKET = 'market'
    LIMIT = 'limit'

@dataclass
class Order:
    quantity: int
    side: Side
    ord_type: OrdType
    order_id: int | None = None
    cancelled: bool = False

    creation_time: int = None
    price: int | None = None
    agent_id: int | None = None
    stock_id: int | None = None

    remaining_qty: int = field(init=False)

    def __post_init__(self) -> None:
        self.remaining_qty = self.quantity

@dataclass
class Trade:
    price: int
    quantity: int
    buy_order_id: int
    sell_order_id: int
    event_number: int
    timestamp: int | None = None
    buy_agent_id: int | None = None
    sell_agent_id: int | None = None




class MatchResult:
    def __init__(self):
        self.trades: list[Trade] = []
        self.completed_orders: list[Order] = []

    

class OrderBook:

    def __init__(self):
        self.bids: dict[int, deque[Order]] = {} 
        self.asks: dict[int, deque[Order]] = {} # we should have the values of keys being queues
                # could also store these as heaps? how do we get the minimum value?
                # heap then has O(1) look up for min instead of O(n) - not currently essential, dont know how this could change.
                # hash map has O(1) look up for any specific value - when are we looking up a specfic value and not just the minimum?
                    # during order cancellations and when we add orders

        self.trades: list[Trade] = []
        # this is incremented after each trade
        self.event_number = 0



    def add_order(self, order: Order) -> None:
        if order.ord_type == OrdType.MARKET:
            raise ValueError("Market orders cannot go in the order book")

        if order.price is None:
                    raise ValueError("Limit orders require a price")
        
        # we check which side: 'bid' or 'ask', then we add it to the appropriate side.
        if order.side == Side.BID:
            # check if orders already exist at this price
            if order.price in self.bids:
                self.bids[order.price].append(order)
            else:
                self.bids[order.price] = deque([order])


        elif order.side == Side.ASK:
            if order.price in self.asks:
                self.asks[order.price].append(order)
            else:
                self.asks[order.price] = deque([order])
        else:
             raise ValueError("order must be an ask or bid")

    def biggest_bid(self):
        '''returns integer'''
        return max(self.bids) if self.bids else None

    def smallest_ask(self):
            '''returns integer'''
            return min(self.asks) if self.asks else None

    # Need function to complete transactions.
    def match_order(self, order: Order, *, budget: int | None = None) -> MatchResult:
        if order.ord_type == OrdType.LIMIT and order.price is None:
            raise ValueError("Limit orders require a price")
        spent = 0

        result = MatchResult()
        # should take in an order, if it is market then it should be processed immediately - granted the book remains non empty
        # if it is limit then we match at the best possible price and then add to book when we cant go any further
        # should return a list of transactions. - later can add this a data structure holding these, probably just a list.

        if order.side == Side.BID:
            crosses = le
            opposite_book = self.asks
        elif order.side == Side.ASK:
            crosses = ge                # ge(a, b) == a >= b
            opposite_book = self.bids
        else: 
             raise ValueError("must be ask or bid")

        while order.remaining_qty > 0:
            best_price = self.smallest_ask() if order.side == Side.BID else self.biggest_bid()
            if best_price is None or (order.ord_type == OrdType.LIMIT and not crosses(best_price, order.price)):  # no more trades occur 
                if order.ord_type == OrdType.LIMIT:
                    self.add_order(order)
                if result.trades:
                    self.event_number += 1
                return result
            
            resting: Order = opposite_book[best_price][0] # now order object
            if order.side == Side.BID:
                buyer_id = order.order_id
                seller_id = resting.order_id
                buyer_agent_id = order.agent_id
                seller_agent_id = resting.agent_id
            else:
                buyer_id = resting.order_id
                seller_id = order.order_id
                buyer_agent_id = resting.agent_id
                seller_agent_id = order.agent_id


            traded_quantity = min(resting.remaining_qty, order.remaining_qty)

            # if its a market bid then we need to make a max quantity
            if order.ord_type == OrdType.MARKET and order.side == Side.BID:
                # remaining allowed spendage is budget - spent
                if budget is not None:
                    max_quantity = (budget - spent) // best_price
                    if max_quantity == 0:
                        if result.trades:
                            self.event_number += 1
                        return result
                    else:
                        traded_quantity = min(traded_quantity, max_quantity)
                    


            trade = Trade(                                
                        price=best_price,
                        quantity=traded_quantity,
                        buy_order_id=buyer_id,
                        sell_order_id=seller_id,
                        event_number=self.event_number,
                        buy_agent_id=buyer_agent_id,
                        sell_agent_id=seller_agent_id,
                    )

            if order.ord_type == OrdType.MARKET and order.side == Side.BID:
                spent += traded_quantity * best_price
            
            self.trades.append(trade)
            result.trades.append(trade)

            # update remaining quantities          
            order.remaining_qty -= traded_quantity
            resting.remaining_qty -= traded_quantity

            # remove resting order if it is complete
            if resting.remaining_qty == 0:
                result.completed_orders.append(opposite_book[best_price].popleft())
                if not opposite_book[best_price]:
                    opposite_book.pop(best_price)
        if result.trades:
            self.event_number += 1 # only change this at the end of the match so the order is processed 'instantly'
        return result
    
    def cancel_order(self, order: Order) -> Order:
        if order.remaining_qty == 0:
            return Order

        # idea is to repeatedly remove from start and add to end to end until order is removed
        # fetch correct book
        if order.side == Side.BID:
            book = self.bids
        elif order.side == Side.ASK:
            book = self.asks
        else:
            raise ValueError("Bad order")
        found = False
        if order.price in book:
            for i in range(len(book[order.price])):
                z: Order = book[order.price].popleft()
                if z.order_id != order.order_id:
                    book[order.price].append(z)
                else:
                    found = True
            if not book[order.price]:
                book.pop(order.price)
        else:
            raise KeyError("No order at this price in the book")
        
        order.cancelled = found
        if order.cancelled:
            self.event_number += 1         #timestamp only increases when we actually cancel the order
        return order



