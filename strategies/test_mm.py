import random

from traders import Trader
from models import Order, OrdType, Request, ReqType, Side
from strategies.helper_functions import cancellation_request, placement_request
from simulation import Simulation
from order_book import OrderBook
from testing_starters import def_trader, def_ask, def_bid, place

# we need to check the cancellation_request function
# should have situations for cancelling both sides as well as nothing

def test_cancellation_request_tolerance_check():
    sim = Simulation()
    sim.traders[1] = def_trader(sim, 1)
    sim.traders[2] = def_trader(sim, 2)

    ask = def_ask(trader_id=1,
                  price=110)
    bid = def_bid(trader_id=1,
                  price=90)

    req1 = place(ask)
    req2 = place(bid)

    bad_ask = def_ask(trader_id=2,
                      price=100)
    bad_ask.creation_time = 0

    req3 = place(bad_ask)

    sim.requests.append(req1)
    sim.requests.append(req2)
    sim.requests.append(req3)

    sim.apply_request()
    sim.apply_request()
    sim.apply_request()

    assert sim.traders[2].open_asks == [bad_ask]

    # say halfspread == 2
    # ask = midprice + halfspread
    halfspread = 2
    sim.book.get_mid_price() 
       
    ask = sim.book.mid_price + halfspread
    bid = sim.book.mid_price - halfspread

    print(ask, bid)

    req4 = cancellation_request(
        ask=ask,
        bid=bid,
        trader=sim.traders[2],
        timestamp=0,
        time_req=0,
        tolerance=3,
        rng=None
    )

    assert req4 is None

    print(ask, bid)

    req5 = cancellation_request(
        ask=ask,
        bid=bid,
        trader=sim.traders[2],
        timestamp=0,
        time_req=0,
        tolerance=0,
        rng=None
    )

    assert req5.req_type == ReqType.CANCEL

    sim.requests.append(req5)

    sim.apply_request()

    assert sim.traders[2].open_asks == []



def test_cancellation_request_chooses_correct_order():
    sim = Simulation()
    sim.traders[1] = def_trader(sim, 1)
    sim.traders[2] = def_trader(sim, 2)

    ask = def_ask(trader_id=1,
                  price=110)
    bid = def_bid(trader_id=1,
                  price=90)

    req1 = place(ask)
    req2 = place(bid)

    bad_ask = def_ask(trader_id=2,
                      price=100)
    bad_ask.creation_time = 0

    bad_bid = def_bid(trader_id=2,
                          price=60)
    bad_bid.creation_time = 0

    req3 = place(bad_ask)
    req4 = place(bad_bid)

    sim.requests.append(req1)
    sim.requests.append(req2)
    sim.requests.append(req3)
    sim.requests.append(req4)

    sim.apply_request()
    sim.apply_request()
    sim.apply_request()
    sim.apply_request()

    assert sim.traders[2].open_asks == [bad_ask]
    assert sim.traders[2].open_bids == [bad_bid]

    # say halfspread == 2
    # ask = midprice + halfspread
    halfspread = 2
    sim.book.get_mid_price() 
       
    ask = sim.book.mid_price + halfspread
    bid = sim.book.mid_price - halfspread

    print(ask, bid)

    req4 = cancellation_request(
        ask=ask,
        bid=bid,
        trader=sim.traders[2],
        timestamp=0,
        time_req=0,
        tolerance=3,
        rng=None
    )

    assert req4.req_type == ReqType.CANCEL
    assert req4.order == bad_bid

    sim.requests.append(req4)
    sim.apply_request()

    assert sim.traders[2].open_bids == []
    assert sim.traders[2].open_asks == [bad_ask]


# young order doesnt cancel
def test_cancellation_request_young_order():
    sim = Simulation()
    sim.traders[1] = def_trader(sim, 1)
    sim.traders[2] = def_trader(sim, 2)

    ask = def_ask(trader_id=1,
                    price=110)
    bid = def_bid(trader_id=1,
                    price=90)

    req1 = place(ask)
    req2 = place(bid)

    bad_ask = def_ask(trader_id=2,
                        price=100)
    bad_ask.creation_time = 0

    req3 = place(bad_ask)

    sim.requests.append(req1)
    sim.requests.append(req2)
    sim.requests.append(req3)

    sim.apply_request()
    sim.apply_request()
    sim.apply_request()

    assert sim.traders[2].open_asks == [bad_ask]

    # say halfspread == 2
    # ask = midprice + halfspread
    halfspread = 2
    sim.book.get_mid_price() 
        
    ask = sim.book.mid_price + halfspread
    bid = sim.book.mid_price - halfspread

    print(ask, bid)

    req4 = cancellation_request(
        ask=ask,
        bid=bid,
        trader=sim.traders[2],
        timestamp=0,
        time_req=2,
        tolerance=0,
        rng=None
    )

    assert req4 is None

    

