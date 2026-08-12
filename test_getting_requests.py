from order_book import OrderBook, Order, Side, OrdType, Trade
from agents import Agent
from simulation import Simulation
from requestsobj import Request, ReqType
from strategies import Random



def test_prob_0_gives_no_requests():
    sim = Simulation()
    strat1 = Random(
            buy_probability=0,
            sell_probability=0,
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

    sim.get_requests()
    sim.get_requests()
    sim.get_requests()
    assert len(sim.requests) == 0

