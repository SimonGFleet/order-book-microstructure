from order_book import OrderBook
from models import MatchResult, Order, OrdType, Request, ReqType, Side, Trade
from traders import Trader
from simulation import Simulation
from strategies import Strategy

def test_empty_requests():
    sim: Simulation = Simulation()

    sim.apply_requests()

    assert len(sim.requests) == 0
    assert len(sim.book.trades) == 0


def test_place_non_crossing_order():
    sim: Simulation = Simulation()

    sim.traders[1] = Trader(
            model=sim,
        trader_id=1,
        initial_cash=1000,
        strategy=Strategy(),
        initial_position=10,
        )
    sim.traders[2] = Trader(
            model=sim,
            trader_id=2,
            initial_cash=1000,
            strategy=Strategy(),
            initial_position=0,
        )
    sim.requests.append(
        Request(
            req_type=ReqType.PLACE,
            order=Order(
                order_id=1,
                quantity=10,
                side=Side.ASK,
                ord_type=OrdType.LIMIT,
                price=101,
                trader_id=1,
            )
        )
    )
    sim.requests.append(
        Request(
            req_type=ReqType.PLACE,
            order=Order(
                order_id=2,
                quantity=10,
                side=Side.BID,
                ord_type=OrdType.LIMIT,
                price=99,
                trader_id=2,
            )
        )
    )
    sim.apply_requests() # this should just place the order, not make any trades

    # the traders remain identical to their creation
    assert sim.traders[1].current_cash == 1000
    assert sim.traders[2].current_cash == 1000
    assert sim.traders[1].current_position == 10
    assert sim.traders[2].current_position == 0

    assert len(sim.requests) == 0
    assert len(sim.book.trades) == 0
    assert len(sim.book.asks[101]) == 1
    assert len(sim.book.bids[99]) == 1

def test_place_crossing_order():
    sim: Simulation = Simulation()

    sim.traders[1] = Trader(
            model=sim,
        trader_id=1,
        initial_cash=1000,
        strategy=Strategy(),
        initial_position=10,
        )
    sim.traders[2] = Trader(
            model=sim,
            trader_id=2,
            initial_cash=1000,
            strategy=Strategy(),
            initial_position=0,
        )
    sim.requests.append(
        Request(
            req_type=ReqType.PLACE,
            order=Order(
                order_id=1,
                quantity=10,
                side=Side.ASK,
                ord_type=OrdType.LIMIT,
                price=100,
                trader_id=1,
            )
        )
    )
    sim.requests.append(
        Request(
            req_type=ReqType.PLACE,
            order=Order(
                order_id=2,
                quantity=10,
                side=Side.BID,
                ord_type=OrdType.LIMIT,
                price=100,
                trader_id=2,
            )
        )
    )
    sim.apply_requests() # this should just place the order, not make any trades

    # no requests left - should be one completed trade
    assert len(sim.requests) == 0

    assert len(sim.book.trades) == 1
    assert sim.traders[1].current_position == 0
    assert sim.traders[2].current_position == 10
    assert sim.traders[1].current_cash == 2000
    assert sim.traders[2].current_cash == 0

def test_cancellation_request():
    sim: Simulation = Simulation()

    sim.traders[1] = Trader(
            model=sim,
        trader_id=1,
        initial_cash=1000,
        strategy=Strategy(),
        initial_position=10,
        )

    ord1: Order = Order(
                        order_id=1,
                        quantity=10,
                        side=Side.ASK,
                        ord_type=OrdType.LIMIT,
                        price=100,
                        trader_id=1,
                    )

    sim.requests.append(
        Request(
            req_type=ReqType.PLACE,
            order=ord1,
        )
    )
    sim.apply_requests()

    sim.requests.append(
        Request(
            req_type=ReqType.CANCEL,
            order=ord1,
        )
    )

    sim.apply_requests()

    assert len(sim.requests) == 0

    assert sim.book.asks == {}
