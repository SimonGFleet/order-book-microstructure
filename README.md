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
