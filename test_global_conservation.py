# total initial cash and initial position should be equal to current cash/position after any simulation is run.
from simulation import Simulation
from strategies import Random
from agents import Agent




def test_cash_position_totals_preserved():
    # create 10 random agents with fixed probabilities
    sim = Simulation()

    for i in range(1, 11):
        strat = Random(
            buy_probability=0.33,
            sell_probability=0.33,
            cancel_probability=0,
            limit_probability=1,
            max_quantity=10,
            max_price_offset=10,
        )
        agent = Agent(
            agent_id=i,
            initial_cash=10000,
            initial_position=100,
            strategy=strat
        )
        sim.agents[i] = agent

    starting_cash = sum(agent.current_cash for agent in sim.agents.values())
    assert starting_cash == 10000 * 10
    starting_position = sum(agent.current_position for agent in sim.agents.values())
    assert starting_position == 100 * 10

    sim.run_sim(1000)

    final_cash = sum(agent.current_cash for agent in sim.agents.values())
    assert final_cash == starting_cash
    final_position = sum(agent.current_position for agent in sim.agents.values())
    assert final_position == starting_position
