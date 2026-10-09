# when we already have asks resting in the book, we should not be able to spend more than the budget we are passing in
from simulation import Simulation
from models import Order, OrdType, ReqType, Request, Side
from traders import Trader
from testing_starters import def_trader, def_ask, place


def test_doesnt_over_spend():
    # want to have an trader that makes some asks (limit) at just one price
    # second trader should make a market order for more than it can afford
    sim = Simulation()
    sim.traders[1] = def_trader(sim, 1)
    sim.traders[2] = def_trader(sim, 2, initial_cash=500)

    ord1 = def_ask(trader_id=1)

    ord2 = Order(
        quantity=10,
        side=Side.BID,
        ord_type=OrdType.MARKET,
        trader_id=2,
    )
    req1 = place(ord1)
    req2 = place(ord2)

    sim.requests.append(req1)
    sim.apply_requests()

    sim.requests.append(req2)
    sim.apply_requests()

    # expecting: trader2 should have 0 cash, trader 1 should have 1500, trader 2 should have 15 position, trader 2 should have 5
    assert sim.traders[2].current_cash == 0
    assert sim.traders[2].effective_cash == 0
    assert sim.traders[2].effective_position == 15
    assert sim.traders[2].current_position == 15
    assert sim.traders[1].current_cash == 1500
    assert sim.traders[1].current_position == 5
    assert sim.traders[1].effective_position == 0



def test_over_spending_multiple_prices():
    sim = Simulation()
    sim.traders[1] = def_trader(sim, 1)
    sim.traders[2] = def_trader(sim, 2)
    sim.traders[3] = def_trader(sim, 3, initial_cash=2000, initial_position=0)

    ord1 = def_ask(1)
    ord2 = def_ask(2, price=150)
    ord3 = Order(
        trader_id=3,
        quantity=20,
        side=Side.BID,
        ord_type=OrdType.MARKET,
    )
    req1 = place(ord1)
    req2 = place(ord2)
    req3 = place(ord3)

    sim.requests.append(req1)
    sim.requests.append(req2)
    sim.apply_requests()

    # Due to shuffling in apply_requests() the market order needs to come in last.
    sim.requests.append(req3)
    sim.apply_requests()

    assert sim.traders[3].current_position == 16
    assert sim.traders[3].current_cash == 100
    assert sim.traders[3].effective_position == 16
    assert sim.traders[3].effective_cash == 100
