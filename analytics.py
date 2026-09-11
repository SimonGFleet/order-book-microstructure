from __future__ import annotations

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

    def plot_trader_wealth(self, trader_id: int):
        trader = self.sim.traders[trader_id]

        timestamps = [snap.timestamp for snap in trader.snapshots]
        wealth = [snap.wealth for snap in trader.snapshots]

        plt.plot(timestamps, wealth)
        plt.xlabel("Time Steps")
        plt.ylabel("wealth")
        plt.title("Wealth over Time")
        plt.show()

    def plot_trader_pnl(self, trader_id: int):
        trader = self.sim.traders[trader_id]

        timestamps = [snap.timestamp for snap in trader.snapshots]
        pnl = [snap.pnl for snap in trader.snapshots]

        plt.plot(timestamps, pnl)
        plt.xlabel("Time Steps")
        plt.ylabel("PnL")
        plt.title("PnL over Time")
        plt.show()




    def plot_portfolio_summary(self, sim, market_maker_id: int, save_path: str | None = None):
        """
        Create a clean portfolio figure showing:
        - market mid-price
        - bid/ask spread
        - market-maker inventory

        Assumes sim.run_sim(...) has already been called.
        """

        timestamps = [snap.timestamp for snap in sim.sim_history]
        mid_prices = [snap.mid_price for snap in sim.sim_history]
        spreads = [snap.spread for snap in sim.sim_history]

        mm = sim.traders[market_maker_id]
        mm_timestamps = [snap.timestamp for snap in mm.snapshots]
        mm_inventory = [snap.current_position for snap in mm.snapshots]

        # Wider than tall so it works well as a portfolio image
        fig = plt.figure(figsize=(14, 8))

        # Main chart gets the full top row
        ax_price = fig.add_axes([0.08, 0.53, 0.84, 0.36])

        # Two smaller charts below
        ax_inventory = fig.add_axes([0.08, 0.12, 0.39, 0.27])
        ax_spread = fig.add_axes([0.53, 0.12, 0.39, 0.27])

        # --------------------
        # Mid-price
        # --------------------
        ax_price.plot(timestamps, mid_prices, linewidth=1.5)

        ax_price.set_title(
            "Market Mid-Price",
            loc="left",
            fontsize=16,
            fontweight="bold"
        )

        ax_price.set_ylabel("Price")
        ax_price.set_xlabel("Simulation step")

        # --------------------
        # Market-maker inventory
        # --------------------
        ax_inventory.plot(
            mm_timestamps,
            mm_inventory,
            linewidth=1.3
        )

        ax_inventory.set_title(
            "Market-Maker Inventory",
            loc="left",
            fontsize=13,
            fontweight="bold"
        )

        ax_inventory.set_ylabel("Position")
        ax_inventory.set_xlabel("Simulation step")

        # --------------------
        # Spread
        # --------------------
        ax_spread.plot(
            timestamps,
            spreads,
            linewidth=1.3
        )

        ax_spread.set_title(
            "Bid–Ask Spread",
            loc="left",
            fontsize=13,
            fontweight="bold"
        )

        ax_spread.set_ylabel("Spread")
        ax_spread.set_xlabel("Simulation step")

        # --------------------
        # Clean up all axes
        # --------------------
        for ax in [ax_price, ax_inventory, ax_spread]:
            ax.spines["top"].set_visible(False)
            ax.spines["right"].set_visible(False)
            ax.grid(alpha=0.15)

        fig.suptitle(
            "Market Microstructure Simulation",
            x=0.08,
            y=0.97,
            ha="left",
            fontsize=20,
            fontweight="bold"
        )

        fig.text(
            0.08,
            0.925,
            "10 random traders + 1 naive market maker · price-time priority · limit and market orders",
            fontsize=11,
            alpha=0.7
        )

        if save_path:
            plt.savefig(
                save_path,
                dpi=200,
                bbox_inches="tight"
            )

        plt.show()
