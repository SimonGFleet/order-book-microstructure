# when we do a market ask, it should add the correct positioning
from simulation import Simulation
from testing_starters import def_agent, def_bid, place
from models import Order, OrdType, Side

def test_market_ask_updates_effective_position():
    sim = Simulation()
    sim.traders[1] = def_agent(sim, 1, initial_position=10)
    sim.traders[2] = def_agent(sim, 2, initial_cash=1000, initial_position=0)

    bid = def_bid(agent_id=2, price=100, quantity=5)
    market_ask = Order(
        agent_id=1,
        quantity=5,
        side=Side.ASK,
        ord_type=OrdType.MARKET,
    )

    sim.requests.append(place(bid))
    sim.apply_request()

    sim.requests.append(place(market_ask))
    sim.apply_request()

    assert sim.traders[1].current_position == 5
    assert sim.traders[1].effective_position == 5
    assert sim.traders[2].current_position == 5
    assert sim.traders[2].effective_position == 5
