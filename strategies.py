from order_book import OrderBook
from agents import Agent
from models import Order, OrdType, Request, ReqType, Side, SimulationSnapshot


import random


class Strategy:
    def __init__(self):
        self.open_orders = []


    def decide(self, agent: Agent, book: OrderBook, timestamp: int):
        pass


class Random(Strategy):
    # should cancel orders, at each step just decide on a fairly trivial action,
    # give it some small amount of randomness
    def __init__(
            self,
            buy_probability: float,
            sell_probability: float,
            cancel_probability: float,
            limit_probability: float,
            max_quantity: int,
            max_price_offset: int,
            reference_price: int,
            seed: int | None = None,
    ):
        if not 0 <= cancel_probability <= 1:
            raise ValueError("Invalid cancel probability")
        
        if buy_probability + sell_probability > 1:
            raise ValueError("Buy probability + Sell probability must be less than one.")

        if buy_probability < 0 or sell_probability < 0:
            raise ValueError("Buy/Sell probabilities must be >= 0")

        if not 0 <= limit_probability <= 1:
            raise ValueError("Limit probability not appropriate")

        if max_quantity <= 0:
            raise ValueError("Max quantity must be > 0")

        if max_price_offset < 0:
            raise ValueError("max_price_offset must be >= 0")

        
        self.buy_prob = buy_probability
        self.sell_prob = sell_probability
        self.cancel_prob = cancel_probability
        self.limit_prob = limit_probability
        self.max_quantity = max_quantity            # in current setting, expectation is n / 2
        self.max_price_offset = max_price_offset    # expectation is best_price
        self.reference_price = reference_price
        self.rng = random.Random(seed)



    def decide(self, agent: Agent, book: OrderBook, timestamp: int) -> Request | None:
        '''
        Chooses a float in [0, 1], then based on the assigned probabilities we either attempt to buy or sell
        Same for market order'''
        cancel = self.rng.random() # cancel checker.
        if cancel < self.cancel_prob:
            # choose a random order to cancel out of the open orders?
            a = len(agent.open_asks)
            b = len(agent.open_bids)
            if a + b == 0:
                return None
            
            n = self.rng.randint(0, a+b-1)
            if n >= a:
                n -= a
                return Request(req_type=ReqType.CANCEL, order=agent.open_bids[n])
            else:
                return Request(req_type=ReqType.CANCEL, order=agent.open_asks[n])



        action = self.rng.random() # buy/sell/wait
        type_prob = self.rng.random() # market/limit

        desired_quantity = self.rng.randint(1, self.max_quantity) # if we are trading: how much?
        deviation = self.rng.randint(-self.max_price_offset, self.max_price_offset) # what price
        
        ord_type = OrdType.LIMIT if type_prob < self.limit_prob else OrdType.MARKET
        if action < self.buy_prob: # attempt to buy
            side = Side.BID
            best_bid = book.biggest_bid()
            if best_bid is None:
                price = max(1, self.reference_price + deviation)
            else:
                price = max(1, best_bid + deviation)
            quantity = min(agent.effective_cash // price, desired_quantity) 
        elif action < self.buy_prob + self.sell_prob: # attempt to sell
            side = Side.ASK
            best_ask = book.smallest_ask()
            if best_ask is None:
                price = max(1, self.reference_price + deviation)
            else:
                price = max(1, best_ask + deviation)
            quantity = min(agent.effective_position, desired_quantity) # depends on current position
        else:
            return None


        # if we cant afford the order or dont want one then we dont make one
        if quantity == 0:
            return None

        # Create the desired order
        order = Order(
                    quantity=quantity,
                    side=side,
                    ord_type=ord_type,
                    agent_id=agent.agent_id,
                    price=price,
                )

        # Package it appropriately.
        return Request(
            ReqType.PLACE,
            order=order,
        )




class NaiveMM:
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
        




