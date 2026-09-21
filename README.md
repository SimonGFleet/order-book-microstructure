# Order Book

A Python agent-based order book market microstructure simulator. Experiment with traders using different strategies and observe how market behaviour changes.

## Features

- Limit and market orders
- Cancellation of orders
- Trader creation with strategies
- Run simulations for any number of time steps with specified traders
- Get statistics for the simulation as a whole (and each individual trader soon)
- Tests cover accounting logic and asset conservation.

## Setup

Requires Python 3.14 or newer.

```bash
git clone https://github.com/SimonGFleet/order-book-microstructure.git
cd order-book-microstructure

python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
```
## How it works

Each simulation timestep asks eligible traders for an action.
Each trader’s strategy returns either a request to place or cancel an order, or no action.

Requests enter a priority queue with an arrival time determined by the trader’s latency and latency deviation. At each timestep, requests that are due are collected, shuffled, and processed.

A trader becomes eligible to decide again on the timestep after its request’s scheduled arrival. This lets its next decision use the book state after the previous request was processed. With zero latency, a trader can decide once per timestep.

New orders receive a sequential ID and creation timestamp when their requests are generated. After processing requests, the simulation records market and trader snapshots, then advances the timestamp.

## Reproducible simulations

Set the seed once when constructing the simulation:

```python
sim = Simulation(seed=42)

# Omitting the seed generates one that you can record and reuse.
sim = Simulation()
print(sim.seed)
```

The master seed deterministically derives separate generators for request ordering,
each trader's strategy decisions, and each trader's latency. Seeds use a versioned
SHA-256 encoding of the master seed, purpose and trader ID; creating extra traders
or drawing from another stream does not change an existing stream's sequence.
Strategies no longer accept a `seed` argument. Traders require a `Simulation` model
and obtain their generators from it, even when sharing a strategy object.

To replay a run, construct fresh simulation and trader objects with the recorded
seed, the same configuration, unique trader IDs and insertion order, and the same
code and Python/dependency versions. Calling `run_sim()` again continues a run;
assigning `sim.seed` does not reset existing generators or simulation state.
Old seeded results are not preserved by this new seed derivation scheme.

For parameter comparisons, reuse the seed and trader IDs and keep run lengths equal.
Changing latency or strategy behaviour can still change the market trajectory and
which decisions consume random draws. Use multiple master seeds to evaluate effects
across runs. The example notebooks use seed 42; latency scenarios each run 100,000 steps.

## Project structure

| File | Purpose |
|---|---|
| `order_book.py` | Orders, trades, price levels, matching, and cancellation |
| `simulation.py` | Simulation loop, settlement, and market statistics |
| `traders.py` | Trader state and strategy integration |
| `strategies` | Folder to hold strategies for traders |
| `models.py` | Stores common objects for other files to import |
| `example.ipynb` | Interactive experimentation |
| `test_*.py` | Automated tests |

## Running the tests

```bash
python -m pytest -v
```

To experiment with the included notebook, run:

```bash
jupyter lab example.ipynb
```
