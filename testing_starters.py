from models import Order, OrdType, ReqType, Request, Side
from traders import Trader
import mesa



def def_bid(trader_id, quantity: int = 10, price: int = 100, side: Side = Side.BID, ord_type: OrdType = OrdType.LIMIT) -> Order:
    return Order(
        quantity=quantity,
        side=side,
        ord_type=ord_type,
        price=price,
        trader_id=trader_id,
    )

def def_ask(trader_id: int, quantity: int = 10, price: int = 100, side: Side = Side.ASK, ord_type: OrdType = OrdType.LIMIT) -> Order:
    return Order(
        quantity=quantity,
        side=side,
        ord_type=ord_type,
        price=price,
        trader_id=trader_id,
    )

def def_trader(model: mesa.Model, trader_id, strategy=None, initial_cash=1000, initial_position=10,) -> Trader:
    return Trader(
        model=model,
        trader_id=trader_id,
        initial_cash=initial_cash,
        initial_position=initial_position,
        strategy=strategy,
    )

def place(ord: Order) -> Request:
    return Request(
        req_type=ReqType.PLACE,
        order=ord,
    )
