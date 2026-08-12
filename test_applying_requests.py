from order_book import OrderBook, Order, Side, OrdType, Trade
from agents import Agent
from simulation import Simulation
from requestsobj import Request, ReqType
from strategies import Strategy

def test_empty_requests():
    sim: Simulation = Simulation()

    sim.apply_request()

    assert len(sim.requests) == 0
    assert len(sim.book.trades) == 0


def test_place_non_crossing_order():
    sim: Simulation = Simulation()

    sim.agents[1] = Agent(
        agent_id=1,
        initial_cash=1000,
        strategy=Strategy(),
        initial_position=10,
        )
    sim.agents[2] = Agent(
            agent_id=2,
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
                agent_id=1,
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
                agent_id=2,
            )
        )
    )
    sim.apply_request() # this should just place the order, not make any trades
    sim.apply_request() # this should do similar

    # the agents remain identical to their creation
    assert sim.agents[1].current_cash == 1000
    assert sim.agents[2].current_cash == 1000
    assert sim.agents[1].current_position == 10
    assert sim.agents[2].current_position == 0

    assert len(sim.requests) == 0
    assert len(sim.book.trades) == 0
    assert len(sim.book.asks[101]) == 1
    assert len(sim.book.bids[99]) == 1

def test_place_crossing_order():
    sim: Simulation = Simulation()

    sim.agents[1] = Agent(
        agent_id=1,
        initial_cash=1000,
        strategy=Strategy(),
        initial_position=10,
        )
    sim.agents[2] = Agent(
            agent_id=2,
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
                agent_id=1,
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
                agent_id=2,
            )
        )
    )
    sim.apply_request() # this should just place the order, not make any trades
    sim.apply_request() # this should do similar

    # no requests left - should be one completed trade
    assert len(sim.requests) == 0

    assert len(sim.book.trades) == 1
    assert sim.agents[1].current_position == 0
    assert sim.agents[2].current_position == 10
    assert sim.agents[1].current_cash == 2000
    assert sim.agents[2].current_cash == 0

def test_cancellation_request():
    sim: Simulation = Simulation()

    sim.agents[1] = Agent(
        agent_id=1,
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
                        agent_id=1,
                    )

    sim.requests.append(
        Request(
            req_type=ReqType.PLACE,
            order=ord1,
        )
    )

    sim.requests.append(
        Request(
            req_type=ReqType.CANCEL,
            order=ord1,
        )
    )

    sim.apply_request()
    assert len(sim.requests) == 1

    sim.apply_request()
    assert len(sim.requests) == 0

    assert sim.book.asks == {}