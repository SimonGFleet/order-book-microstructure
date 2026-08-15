# when we already have asks resting in the book, we should not be able to spend more than the budget we are passing in
from simulation import Simulation
from order_book import Order, OrdType, Side
from agents import Agent
from testing_starters import def_agent, def_ask, place
from requestsobj import ReqType, Request


def test_doesnt_over_spend():
    # want to have an agent that makes some asks (limit) at just one price
    # second agent should make a market order for more than it can afford
    sim = Simulation()
    sim.agents[1] = def_agent(1)
    sim.agents[2] = def_agent(2, initial_cash=500)

    ord1 = def_ask(agent_id=1)

    ord2 = Order(
        quantity=10,
        side=Side.BID,
        ord_type=OrdType.MARKET,
        agent_id=2,
    )
    req1 = place(ord1)
    req2 = place(ord2)

    sim.requests.append(req1)
    sim.apply_request()

    sim.requests.append(req2)
    sim.apply_request()

    # expecting: agent2 should have 0 cash, agent 1 should have 1500, agent 2 should have 15 position, agent 2 should have 5
    assert sim.agents[2].current_cash == 0
    assert sim.agents[2].effective_cash == 0
    assert sim.agents[2].effective_position == 15
    assert sim.agents[2].current_position == 15
    assert sim.agents[1].current_cash == 1500
    assert sim.agents[1].current_position == 5
    assert sim.agents[1].effective_position == 10



def test_over_spending_multiple_prices():
    sim = Simulation()
    sim.agents[1] = def_agent(1)
    sim.agents[2] = def_agent(2)
    sim.agents[3] = def_agent(3, initial_cash=2000, initial_position=0)

    ord1 = def_ask(1)
    ord2 = def_ask(2, price=150)
    ord3 = Order(
        agent_id=3,
        quantity=20,
        side=Side.BID,
        ord_type=OrdType.MARKET,
    )
    req1 = place(ord1)
    req2 = place(ord2)
    req3 = place(ord3)

    sim.requests.append(req1)
    sim.requests.append(req2)
    sim.requests.append(req3)

    sim.apply_request()
    sim.apply_request()
    sim.apply_request()

    assert sim.agents[3].current_position == 16
    assert sim.agents[3].current_cash == 100
    assert sim.agents[3].effective_position == 16
    assert sim.agents[3].effective_cash == 100
