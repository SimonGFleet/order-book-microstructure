# timestamp is owned by the simulation
# when we call the function run sim - it gets requests, applies them, then increases the timestamp
from testing_starters import def_agent, def_ask, def_bid
from simulation import Simulation
from models import Request, ReqType
from strategies import Random

def test_timestamps_increase_on_each_step():
    sim = Simulation()

    strat1 = Random(
        buy_probability=0.5,
        sell_probability=0.5,
        cancel_probability=0,
        limit_probability=1,
        max_quantity=1,
        max_price_offset=1,
    )

    sim.agents[1] = def_agent(1, strat1, initial_cash=100000, initial_position=1000)
    sim.agents[2] = def_agent(2, strat1, initial_cash=100000, initial_position=1000)

    sim.run_sim(10)

    assert sim.timestamp == 10

    sim.get_requests()

    assert sim.requests[0].order.creation_time == 10
    assert sim.requests[1].order.creation_time == 10


    

    
