import random

from agents import Agent
from models import Order, OrdType, Request, ReqType, Side


def cancellation_request(
    ask: float,
    bid: float,
    agent: Agent,
    timestamp: int,
    time_req: int,
    tolerance: float,
    rng: random.Random,
) -> Request | None:
    """Return a request to cancel the worst stale quote, if there is one."""

    eligible_asks = (
        order
        for order in agent.open_asks
        if order.creation_time is not None
        and order.price is not None
        and timestamp >= order.creation_time + time_req
    )
    worst_ask = max(
        eligible_asks,
        key=lambda order: abs(order.price - ask),
        default=None,
    )

    eligible_bids = (
        order
        for order in agent.open_bids
        if order.creation_time is not None
        and order.price is not None
        and timestamp >= order.creation_time + time_req
    )
    worst_bid = max(
        eligible_bids,
        key=lambda order: abs(order.price - bid),
        default=None,
    )

    ask_diff = abs(worst_ask.price - ask) if worst_ask else 0
    bid_diff = abs(worst_bid.price - bid) if worst_bid else 0

    if max(ask_diff, bid_diff) <= tolerance:
        return None

    if ask_diff > bid_diff:
        order = worst_ask
    elif bid_diff > ask_diff:
        order = worst_bid
    else:
        order = rng.choice([worst_ask, worst_bid])

    return Request(req_type=ReqType.CANCEL, order=order)


def placement_request(
    ask: float,
    bid: float,
    agent: Agent,
    quantity: int,
    rng: random.Random,
    side: Side | None = None,
) -> Request | None:
    """Return an affordable limit-order request at a missing target quote.

    When ``side`` is omitted, the missing side is selected using the naive
    market-maker policy. Inventory-aware strategies can provide a side after
    applying their own inventory policy.
    """

    has_ask = any(order.price == ask for order in agent.open_asks)
    has_bid = any(order.price == bid for order in agent.open_bids)

    if side is None:
        if not has_ask and not has_bid:
            side = Side.ASK if rng.randint(0, 1) == 0 else Side.BID
        elif not has_bid:
            side = Side.BID
        elif not has_ask:
            side = Side.ASK
        else:
            return None
    elif (side == Side.ASK and has_ask) or (side == Side.BID and has_bid):
        return None

    if side == Side.ASK:
        price = ask
        order_quantity = min(agent.effective_position, quantity)
    else:
        if bid <= 0:
            return None
        price = bid
        order_quantity = min(int(agent.effective_cash // bid), quantity)

    if order_quantity <= 0:
        return None

    return Request(
        req_type=ReqType.PLACE,
        order=Order(
            quantity=order_quantity,
            side=side,
            ord_type=OrdType.LIMIT,
            agent_id=agent.agent_id,
            price=price,
        ),
    )
