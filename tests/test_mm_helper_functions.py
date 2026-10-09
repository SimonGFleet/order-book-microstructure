import random
from simulation import Simulation

from models import ReqType, Side
from strategies.helper_functions import cancellation_request, placement_request
from testing_starters import def_trader, def_ask, def_bid


def test_cancellation_request_selects_worst_stale_order():
    trader = def_trader(Simulation(seed=1), 1)
    near_ask = def_ask(1, price=103)
    far_ask = def_ask(1, price=110)
    bid = def_bid(1, price=98)
    near_ask.creation_time = 0
    far_ask.creation_time = 0
    bid.creation_time = 0
    trader.open_asks = [near_ask, far_ask]
    trader.open_bids = [bid]

    request = cancellation_request(
        ask=102,
        bid=98,
        trader=trader,
        timestamp=10,
        time_req=5,
        tolerance=2,
        rng=random.Random(1),
    )

    assert request is not None
    assert request.req_type == ReqType.CANCEL
    assert request.order is far_ask


def test_cancellation_request_ignores_recent_orders():
    trader = def_trader(Simulation(seed=1), 1)
    ask = def_ask(1, price=110)
    ask.creation_time = 8
    trader.open_asks = [ask]

    request = cancellation_request(
        ask=102,
        bid=98,
        trader=trader,
        timestamp=10,
        time_req=5,
        tolerance=2,
        rng=random.Random(1),
    )

    assert request is None


def test_cancellation_request_keeps_orders_within_tolerance():
    trader = def_trader(Simulation(seed=1), 1)
    ask = def_ask(1, price=104)
    ask.creation_time = 0
    trader.open_asks = [ask]

    request = cancellation_request(
        ask=102,
        bid=98,
        trader=trader,
        timestamp=10,
        time_req=5,
        tolerance=2,
        rng=random.Random(1),
    )

    assert request is None


def test_placement_request_places_the_missing_bid():
    trader = def_trader(Simulation(seed=1), 1)
    existing_ask = def_ask(1, price=102)
    trader.open_asks = [existing_ask]

    request = placement_request(
        ask=102,
        bid=98,
        trader=trader,
        quantity=5,
        rng=random.Random(1),
    )

    assert request is not None
    assert request.req_type == ReqType.PLACE
    assert request.order.side == Side.BID
    assert request.order.price == 98
    assert request.order.quantity == 5


def test_placement_request_respects_available_inventory():
    trader = def_trader(Simulation(seed=1), 1, initial_position=3)

    request = placement_request(
        ask=102,
        bid=98,
        trader=trader,
        quantity=5,
        rng=random.Random(1),
        side=Side.ASK,
    )

    assert request is not None
    assert request.order.side == Side.ASK
    assert request.order.quantity == 3


def test_placement_request_respects_available_cash():
    trader = def_trader(Simulation(seed=1), 1, initial_cash=250)

    request = placement_request(
        ask=102,
        bid=100,
        trader=trader,
        quantity=5,
        rng=random.Random(1),
        side=Side.BID,
    )

    assert request is not None
    assert request.order.side == Side.BID
    assert request.order.quantity == 2
