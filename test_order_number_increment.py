from simulation import Simulation
from agents import Agent
from strategies import Random
from order_book import Order
from requestsobj import Request

def test_order_ids_are_generated():
    sim = Simulation()

    strat1 = Random(
        buy_probability=1,
        sell_probability=0,
        cancel_probability=0,
        limit_probability=1,
        max_quantity=1,
        max_price_offset=0,
    )

    sim.agents[1] = Agent(
        agent_id=1,
        initial_cash=1000,
        strategy=strat1,
        initial_position=10,
    )

    assert sim.order_count == 0
    sim.get_requests()
    assert sim.order_count == 1

    ord1: Request = sim.requests[0]

    sim.get_requests()
    assert sim.order_count == 2

    ord2: Request = sim.requests[1]

    assert ord1.order.order_id == 0
    assert ord2.order.order_id == 1
