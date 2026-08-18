from simulation import Simulation

from matplotlib import pyplot as plt



class Analytics():
    def __init__(self, sim: Simulation):
        self.sim = sim

    # SIMULATION PLOTS:

    def plot_midprice(self):
        timestamps = [snap.timestamp for snap in self.sim.sim_history]
        mid_prices = [snap.mid_price for snap in self.sim.sim_history]

        plt.plot(timestamps, mid_prices)
        plt.xlabel("Time Steps")
        plt.ylabel("Price")
        plt.title("Mid Price over Time")
        plt.show()

    def plot_best_bids(self):
        timestamps = [snap.timestamp for snap in self.sim.sim_history]
        best_bids = [snap.best_bid for snap in self.sim.sim_history]

        plt.plot(timestamps, best_bids)
        plt.xlabel("Time Steps")
        plt.ylabel("Price")
        plt.title("Best Bids over Time")
        plt.show()

    def plot_best_asks(self):
        timestamps = [snap.timestamp for snap in self.sim.sim_history]
        best_asks = [snap.best_ask for snap in self.sim.sim_history]

        plt.plot(timestamps, best_asks)
        plt.xlabel("Time Steps")
        plt.ylabel("Price")
        plt.title("Best Asks over Time")
        plt.show()

    def plot_spread(self):
        timestamps = [snap.timestamp for snap in self.sim.sim_history]
        spreads = [snap.spread for snap in self.sim.sim_history]

        plt.plot(timestamps, spreads)
        plt.xlabel("Time Steps")
        plt.ylabel("Spread")
        plt.title("Spread over Time")
        plt.show()

    def plot_trade_count(self):
        timestamps = [snap.timestamp for snap in self.sim.sim_history]
        trade_counts = [snap.trade_count for snap in self.sim.sim_history]

        plt.plot(timestamps, trade_counts)
        plt.xlabel("Time Steps")
        plt.ylabel("Number")
        plt.title("Trade counts over Time")
        plt.show()


    # AGENT PLOTS:

    def plot_agent_wealth(self, agent_id: int):
        agent = self.sim.agents[agent_id]

        timestamps = [snap.timestamp for snap in agent.snapshots]
        wealth = [snap.wealth for snap in agent.snapshots]

        plt.plot(timestamps, wealth)
        plt.xlabel("Time Steps")
        plt.ylabel("wealth")
        plt.title("Wealth over Time")
        plt.show()

    def plot_agent_pnl(self, agent_id: int):
        agent = self.sim.agents[agent_id]

        timestamps = [snap.timestamp for snap in agent.snapshots]
        pnl = [snap.pnl for snap in agent.snapshots]

        plt.plot(timestamps, pnl)
        plt.xlabel("Time Steps")
        plt.ylabel("PnL")
        plt.title("PnL over Time")
        plt.show()

