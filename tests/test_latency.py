from simulation import Simulation
from traders import Trader
from models import Order, OrdType, Side
from testing_starters import def_trader
from strategies import Random



def test_frequency_of_order():
    '''We create a trader with a latency of say x, and 0 deviation to make it deterministic. 
    Then we run the simulation and after y timesteps we should have y // x orders submitted'''

    sim = Simulation()
    strat = Random(buy_probability=1,
                   sell_probability=0,
                   cancel_probability=0,
                   limit_probability=1,
                   max_quantity=1,
                   max_price_offset=0,
                   reference_price=100)
    sim.traders[1] = Trader(model=sim,
                            trader_id=1,
                            initial_cash=100000,
                            initial_position=0,
                            strategy=strat,
                            latency=13,
                            latency_deviation=0)

    # should see it at the start, so first trade will occur at ts 13?
    sim.run_sim(20)
    assert len(sim.traders[1].open_bids) == 1
    sim.run_sim(20)
    assert len(sim.traders[1].open_bids) == 2
    sim.run_sim(10) 
    assert len(sim.traders[1].open_bids) == 3   # whilst timestamp == next_request_time we have the timestamp being incremented after the 
    sim.run_sim(5)
    assert len(sim.traders[1].open_bids) == 3
    sim.run_sim(1)
    assert len(sim.traders[1].open_bids) == 4




