# Order Book

A Python agent based order book market microstructure simulator. Experiment creating agents with different strategies and observe how the market behaviour changes.

## Features

- Limit and market orders
- Cancellation of orders
- Agent creation with strategies
- Run simulations for any number of time steps with specified agents
- Get statistics for the simulation as a whole (and each individual agent soon)
- Tests cover accounting logic and asset conservation.

## Setup

Requires Python 3.10 or newer.

```bash
git clone https://github.com/SimonGFleet/order-book-microstructure.git
cd order-book-microstructure

python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
```
## How it works

Each step of the simulation calls get requests on each agent it has. 
The agent calls its strategy to decide what to do, 
The strategy receives the agent object (their wealth and current open orders) and the state of the order book.
The strategy returns either None, or a Request object - this holds an action (cancel/place) and an order.
We then shuffle the requests and apply them - shuffle is currently just random, no defined latency.

Applying each request:
Incoming orders are matched against the best available price, we use a queue to ensure FIFO for orders of the same price in the book. Uncompleted limit orders are then added to the book.

Strategies base decisions on effective cash and effective position, such that they are unable to overspend.

## Project structure

| File | Purpose |
|---|---|
| `order_book.py` | Orders, trades, price levels, matching, and cancellation |
| `simulation.py` | Simulation loop, settlement, and market statistics |
| `agents.py` | Agent state and strategy integration |
| `strategies.py` | Trading-strategy implementations |
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
