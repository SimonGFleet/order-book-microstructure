from order_book import OrderBook, Side, Order, OrdType
from agents import Agent
import random
from simulation import Request, ReqType


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
            market_probability: float,
            max_quantity: int,
            max_price_offset: int,
            seed: int | None = None,
    ):
        if buy_probability + sell_probability > 1:
            raise ValueError("Buy probability + Sell probability must be less than one.")

        if buy_probability < 0 or sell_probability < 0:
            raise ValueError("Buy/Sell probabilities must be >= 0")

        if market_probability < 0:
            raise ValueError("Market probability must be >= 0")

        if max_quantity <= 0:
            raise ValueError("Max quantity must be > 0")

        if max_price_offset < 0:
            raise ValueError("max_price_offset must be >= 0")

        
        self.buy_prob = buy_probability
        self.sell_prob = sell_probability
        self.market_prob = market_probability
        self.max_quantity = max_quantity
        self.max_price_offset = max_price_offset
        self.rng = random.Random(seed)



    def decide(self, agent: Agent, book: OrderBook) -> Request | None:
        action = self.rng.random() # returns float 0 \leq x \leq 1
        desired_quantity = self.rng.randint(1, self.max_quantity)
        deviation = self.rng.randint(-self.max_price_offset, self.max_price_offset)
        type_prob = self.rng.random()
        ord_type = OrdType.LIMIT #if type_prob < self.market_prob else OrdType.LIMIT
        if action < self.buy_prob: # attempt to buy
            side = Side.BID
            best_bid = book.biggest_bid()
            if best_bid is None:
                price = 100
            else:
                price = best_bid + deviation
            quantity = min(agent.current_cash // price, desired_quantity) 
        elif action <= self.buy_prob + self.sell_prob:
            side = Side.ASK
            best_ask = book.smallest_ask()
            if best_ask is None:
                price = 100
            else:
                price = best_ask + deviation
            quantity = min(agent.position, desired_quantity)
        else:
            return None

        if quantity == 0:
            return None

        order = Order(
                    quantity=quantity,
                    side=side,
                    ord_type=ord_type,
                    agent_id=agent.agent_id,
                    price=price,
                )

        return Request(
            ReqType.PLACE,
            order=order,
        )
        