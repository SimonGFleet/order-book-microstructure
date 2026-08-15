from order_book import Order, OrdType, Side
from requestsobj import ReqType, Request
from agents import Agent



def def_bid(agent_id, quantity: int = 10, price: int = 100, side: Side = Side.BID, ord_type: OrdType = OrdType.LIMIT) -> Order:
    return Order(
        quantity=quantity,
        side=side,
        ord_type=ord_type,
        price=price,
        agent_id=agent_id,
    )

def def_ask(agent_id: int, quantity: int = 10, price: int = 100, side: Side = Side.ASK, ord_type: OrdType = OrdType.LIMIT) -> Order:
    return Order(
        quantity=quantity,
        side=side,
        ord_type=ord_type,
        price=price,
        agent_id=agent_id,
    )

def def_agent(agent_id, strategy=None, initial_cash=1000, initial_position=10,) -> Agent:
    return Agent(
        agent_id=agent_id,
        initial_cash=initial_cash,
        initial_position=initial_position,
        strategy=strategy,
    )

def place(ord: Order) -> Request:
    return Request(
        req_type=ReqType.PLACE,
        order=ord,
    )