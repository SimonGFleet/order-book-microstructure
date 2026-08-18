from simulation import Simulation
from agents import Agent
from strategies import Random
from models import Order, OrdType, Request, ReqType, Side
from testing_starters import def_bid, def_agent, def_ask, place


def test_limit_order_affects_effective_cash():
    sim = Simulation()

    strat1 = Random(
        buy_probability=1,
        sell_probability=0,
        cancel_probability=0,
        limit_probability=1,
        max_quantity=1,
        max_price_offset=0,
        reference_price=sim.initial_price,
    )

    strat2 = Random(
        buy_probability=0,
        sell_probability=1,
        cancel_probability=0,
        limit_probability=1,
        max_quantity=1,
        max_price_offset=0,
        reference_price=sim.initial_price,
    )

    sim.agents[1] = Agent(
        agent_id=1,
        initial_cash=1000,
        strategy=strat1,
        initial_position=10,
        )
    sim.agents[2] = Agent(
            agent_id=2,
            initial_cash=1000,
            strategy=strat2,
            initial_position=10,
        )

    # in an empty market:  
    # agent 1 should always try to buy one stock for 100
    # agent 2 should always try to sell one stock for 100

    # Make their choice
    sim.get_requests()
    assert len(sim.requests) == 2

    sim.apply_request()
    assert len(sim.requests) == 1

    sim.apply_request()
    assert len(sim.requests) == 0

    assert sim.agents[1].effective_cash == 900
    assert sim.agents[2].effective_cash == 1100
    assert sim.agents[1].effective_position == 11
    assert sim.agents[2].effective_position == 9

    assert sim.agents[1].current_cash == 900
    assert sim.agents[2].current_cash == 1100
    assert sim.agents[1].current_position == 11
    assert sim.agents[2].current_position == 9


    assert len(sim.book.trades) == 1
    assert sim.book.trades[0].quantity == 1
    assert sim.book.trades[0].price == 100



def test_cancelling_request_returns_effective_cash():
    sim = Simulation()
    strat1 = Random(
            buy_probability=1,
            sell_probability=0,
            cancel_probability=0,
            limit_probability=1,
            max_quantity=1,
            max_price_offset=0,
            reference_price=sim.initial_price,
        )

    sim.agents[1] = Agent(
        agent_id=1,
        initial_cash=1000,
        strategy=strat1,
        initial_position=10,
        )

    order = Order(
        quantity=1,
        side=Side.BID,
        ord_type=OrdType.LIMIT,
        order_id=1,
        price=100,
        agent_id=1,
    )

    sim.get_requests()
    placed_order = sim.requests[0].order
    assert len(sim.requests) == 1

    sim.apply_request()

    assert len(sim.requests) == 0
    assert sim.agents[1].current_cash == 1000
    assert sim.agents[1].effective_cash == 900  
    
    sim.requests.append(Request(ReqType.CANCEL, placed_order))


    sim.apply_request()
    assert len(sim.requests) == 0

    assert sim.agents[1].current_cash == 1000
    assert sim.agents[1].effective_cash == 1000


# effective cash works for limit orders, not for bids in market orders. 



def test_limit_bid_executing_for_less_than_price():
    sim = Simulation()
    sim.agents[1] = def_agent(1)
    sim.agents[2] = def_agent(2)

    ord1 = def_ask(agent_id=1, price=90)
    ord2 = def_bid(agent_id=2)

    req1 = place(ord1)
    req2 = place(ord2)

    sim.requests.append(req1)
    sim.requests.append(req2)


    sim.apply_request()
    sim.apply_request()

    assert sim.agents[1].current_position == 0
    assert sim.agents[1].effective_position == 0



def test_crossing_limit_orders():
    # agent1 submits an ask for 90, then agent2 submits a bid for 100, both start at 1000,
    # finals: agent1: 1900 cash, position == 0. Agent 2: should be: 100 cash, 20 postion.
    sim = Simulation()
    ag1 = def_agent(1)
    ag2 = def_agent(2)
    sim.agents[1] = ag1
    sim.agents[2] = ag2

    ord1 = def_ask(agent_id=1, price=90)
    ord2 = def_bid(agent_id=2)
    req1 = place(ord1)
    req2 = place(ord2)
    sim.requests.append(req1)
    sim.requests.append(req2)
    sim.apply_request()
    sim.apply_request()

    assert ag1.current_position == 0
    assert ag1.effective_position == 0
    assert ag2.current_position == 20
    assert ag2.effective_position == 20

    assert ag1.current_cash == 1900
    assert ag1.effective_cash == 1900
    assert ag2.current_cash == 100
    assert ag2.effective_cash == 100
