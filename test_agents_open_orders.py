from simulation import Simulation
from strategies import Random
from agents import Agent
from models import Order, OrdType, ReqType, Request, Side


def test_agent_starts_with_no_open_orders():
    sim = Simulation()
    
    strat1 = Random(            # does nothing every time.
        buy_probability=0,
        sell_probability=0,
        cancel_probability=0,
        limit_probability=0.5,
        max_quantity=1,
        max_price_offset=0,
    )

    sim.agents[1] = Agent(
        agent_id=1,
        initial_cash=1000,
        initial_position=10,
        strategy=strat1,
    )

    sim.get_requests()

    assert len(sim.requests) == len(sim.agents[1].open_asks)
    assert len(sim.requests) == len(sim.agents[1].open_bids)

    sim.apply_request()

    assert len(sim.requests) == len(sim.agents[1].open_asks)
    assert len(sim.requests) == len(sim.agents[1].open_bids)



def test_agents_gains_open_orders():
    # two agents should make orders, they should both gain the order. no matching occurs
    sim = Simulation()

    sim.agents[1] = Agent(
        agent_id=1,
        initial_cash=1000,
        initial_position=10,
        strategy=None,
    )

    sim.agents[2] = Agent(
        agent_id=2,
        initial_cash=1000,
        initial_position=10,
        strategy=None,
    )

    # make the requests by hand.

    ord1: Order = Order(
        quantity=1,
        side=Side.BID,
        ord_type=OrdType.LIMIT,
        order_id=0,
        price=95,
        agent_id=1
    )
    req1: Request = Request(
        req_type=ReqType.PLACE,
        order=ord1,
    )
    ord2: Order = Order(
        quantity=1,
        side=Side.ASK,
        ord_type=OrdType.LIMIT,
        order_id=1,
        price=105,
        agent_id=2
    )
    req2: Request = Request(
        req_type=ReqType.PLACE,
        order=ord2,
    )
    sim.requests.append(req1)
    sim.requests.append(req2)

    assert len(sim.requests) == 2
    assert len(sim.agents[1].open_asks) == 0
    assert len(sim.agents[1].open_bids) == 0
    assert len(sim.agents[2].open_asks) == 0
    assert len(sim.agents[2].open_bids) == 0

    sim.apply_request()

    assert len(sim.requests) == 1
    assert len(sim.agents[1].open_asks) == 0
    assert len(sim.agents[1].open_bids) == 1
    assert len(sim.agents[2].open_asks) == 0
    assert len(sim.agents[2].open_bids) == 0

    sim.apply_request()

    assert len(sim.requests) == 0
    assert len(sim.agents[1].open_asks) == 0
    assert len(sim.agents[1].open_bids) == 1
    assert len(sim.agents[2].open_asks) == 1
    assert len(sim.agents[2].open_bids) == 0


def test_completing_orders():
    sim = Simulation()
    
    sim.agents[1] = Agent(
        agent_id=1,
        initial_cash=1000,
        initial_position=10,
        strategy=None,
    )

    sim.agents[2] = Agent(
        agent_id=2,
        initial_cash=1000,
        initial_position=10,
        strategy=None,
    )

    # make the requests by hand.

    ord1: Order = Order(
        quantity=1,
        side=Side.BID,
        ord_type=OrdType.LIMIT,
        order_id=1,
        price=100,
        agent_id=1
    )
    req1: Request = Request(
        req_type=ReqType.PLACE,
        order=ord1,
    )
    ord2: Order = Order(
        quantity=5,
        side=Side.BID,
        ord_type=OrdType.LIMIT,
        order_id=2,
        price=99,
        agent_id=1
    )
    req2: Request = Request(
        req_type=ReqType.PLACE,
        order=ord2,
    )
    ord3: Order = Order(
        quantity=3,
        side=Side.ASK,
        ord_type=OrdType.LIMIT,
        order_id=3,
        price=99,
        agent_id=2
    )
    req3: Request = Request(
        req_type=ReqType.PLACE,
        order=ord3,
    )
    sim.requests.append(req1)
    sim.requests.append(req2)
    sim.requests.append(req3)

    sim.apply_request()
    sim.apply_request()

    assert len(sim.requests) == 1
    assert len(sim.agents[1].open_asks) == 0
    assert len(sim.agents[1].open_bids) == 2
    assert len(sim.agents[2].open_asks) == 0
    assert len(sim.agents[2].open_bids) == 0

    sim.apply_request()
    assert len(sim.requests) == 0
    assert len(sim.agents[1].open_asks) == 0
    assert len(sim.agents[1].open_bids) == 1
    assert len(sim.agents[2].open_asks) == 0
    assert len(sim.agents[2].open_bids) == 0





def test_cancelling_orders():
    sim = Simulation()
        
    sim.agents[1] = Agent(
        agent_id=1,
        initial_cash=1000,
        initial_position=10,
        strategy=None,
    )
    ord1: Order = Order(
        quantity=1,
        side=Side.BID,
        ord_type=OrdType.LIMIT,
        order_id=1,
        price=100,
        agent_id=1
    )
    req1: Request = Request(
        req_type=ReqType.PLACE,
        order=ord1,
    )
    req2: Request = Request(
        req_type=ReqType.CANCEL,
        order=ord1,
    )
    sim.requests.append(req1)
    sim.requests.append(req2)
    sim.apply_request()
    assert len(sim.agents[1].open_bids) == 1
    assert not ord1.cancelled
    sim.apply_request()
    assert len(sim.agents[1].open_bids) == 0
    assert ord1.cancelled



def test_market_order_doesnt_become_open():
    # two agents, add limit order, then add non-completing market order, they should partially match, 
    # neither agent should have open orders
    sim = Simulation()
            
    sim.agents[1] = Agent(
        agent_id=1,
        initial_cash=1000,
        initial_position=10,
        strategy=None,
    )
    sim.agents[2] = Agent(
        agent_id=2,
        initial_cash=1000,
        initial_position=10,
        strategy=None,
    )
    ord1: Order = Order(
        quantity=1,
        side=Side.ASK,
        ord_type=OrdType.LIMIT,
        order_id=1,
        price=100,
        agent_id=1
    )
    ord2: Order = Order(
        quantity=2,
        side=Side.BID,
        ord_type=OrdType.MARKET,
        order_id=1,
        price=100,
        agent_id=2
    )
    req1 = Request(
        req_type=ReqType.PLACE,
        order=ord1,
    )
    req2 = Request(
        req_type=ReqType.PLACE,
        order=ord2,
    )
    sim.requests.append(req1)
    sim.requests.append(req2)

    sim.apply_request()
    assert len(sim.agents[1].open_asks) == 1
    assert len(sim.agents[1].open_bids) == 0

    sim.apply_request()
    assert len(sim.agents[1].open_asks) == 0
    assert len(sim.agents[1].open_bids) == 0
    assert len(sim.agents[2].open_asks) == 0
    assert len(sim.agents[2].open_bids) == 0
    assert ord2.remaining_qty == 1

    
    
