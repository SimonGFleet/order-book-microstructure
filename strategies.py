from order_book import OrderBook, Side, Order, OrdType
from agents import Agent
from requestsobj import Request, ReqType


import random


class Strategy:
    def __init__(self):
        self.open_orders = []


    def decide(self, agent: Agent, book: OrderBook):
        pass



# maybe at each timestep we are deciding what to do so we should then 


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
            reference_price: int = 100,
            seed: int | None = None,
    ):
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
        self.limit_prob = limit_probability
        self.max_quantity = max_quantity            # in current setting, expectation is n / 2
        self.max_price_offset = max_price_offset    # expectation is best_price
        self.reference_price = reference_price
        self.rng = random.Random(seed)



    def decide(self, agent: Agent, book: OrderBook) -> Request | None:
        '''
        Chooses a float in [0, 1], then based on the assigned probabilities we either attempt to buy or sell
        Same for market order'''
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

        # package it appropriately.
        return Request(
            ReqType.PLACE,
            order=order,
        )
        