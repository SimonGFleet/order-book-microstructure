"""Replay guarantees for the simulation's independent random streams."""
from dataclasses import asdict
import random

import pytest

from simulation import Simulation
from strategies import Random, NaiveMM, InventoryMM
from traders import Trader


def make_sim(seed):
    sim = Simulation(seed=seed)
    # Sharing a strategy must still give each trader an independent stream.
    noise = Random(.4, .4, .1, .8, 5, 5, 100)
    strategies = [noise] * 5 + [
        NaiveMM(2, 2, 2, 5),
        InventoryMM(2, 2, 2, .5, .1, 5),
    ]
    for trader_id, strategy in enumerate(strategies, 1):
        sim.traders[trader_id] = Trader(
            sim, trader_id, 10000, 100, strategy,
            latency=2, latency_deviation=3,
        )
    return sim


def state(sim):
    return {
        'timestamp': sim.timestamp,
        'order_count': sim.order_count,
        'event_number': sim.book.event_number,
        'mid_price': sim.book.mid_price,
        'trades': [asdict(t) for t in sim.book.trades],
        'history': [asdict(s) for s in sim.sim_history],
        'requests': [asdict(r) for r in sim.requests],
        'bids': {p: [asdict(o) for o in q] for p, q in sim.book.bids.items()},
        'asks': {p: [asdict(o) for o in q] for p, q in sim.book.asks.items()},
        'traders': {
            i: (t.next_request_time, [asdict(s) for s in t.snapshots],
                [asdict(o) for o in t.open_bids], [asdict(o) for o in t.open_asks])
            for i, t in sim.traders.items()
        },
        'rngs': {k: rng.getstate() for k, rng in sim._random_streams.items()},
    }


@pytest.mark.parametrize('seed', [0, 42, -7])
def test_full_replay_ignores_global_randomness_and_other_simulations(seed):
    first, second = make_sim(seed), make_sim(seed)
    unrelated = make_sim(99)
    global_state = random.getstate()
    try:
        first.run_sim(200)
        assert random.getstate() == global_state
        random.seed(123)
        for _ in range(200):
            random.random()
            unrelated.run_sim(1)
            second.run_sim(1)
        assert first.book.trades  # Exercise actual matching, not an empty replay.
        assert state(first) == state(second)
    finally:
        random.setstate(global_state)


def test_generated_seed_can_be_replayed():
    original = make_sim(None)
    replay = make_sim(original.seed)
    original.run_sim(100)
    replay.run_sim(100)
    assert isinstance(original.seed, int)
    assert state(original) == state(replay)


def test_chunked_run_matches_single_run():
    whole, chunked = make_sim(42), make_sim(42)
    whole.run_sim(100)
    chunked.run_sim(40)
    chunked.run_sim(60)
    assert state(whole) == state(chunked)


def test_streams_are_distinct_cached_and_independent_of_creation_order():
    first, second = Simulation(seed=42), Simulation(seed=42)
    expected = first.get_rng('strategy', 1)
    second.get_rng('strategy', 99).random()
    latency = second.get_rng('latency', 1)
    for _ in range(100):
        latency.random()
    actual = second.get_rng('strategy', 1)
    assert actual is second.get_rng('strategy', 1)
    assert second.get_rng('request_ordering') is second.random
    assert [expected.random() for _ in range(20)] == [actual.random() for _ in range(20)]
    streams = [first.get_rng(p, i) for p in ('strategy', 'latency') for i in (2, 3)]
    assert len({r.getstate() for r in streams}) == 4
    assert Simulation(seed=43).get_rng('strategy', 2).getstate() != streams[0].getstate()


@pytest.mark.parametrize('seed', [True, 1.5, '42'])
def test_invalid_master_seed(seed):
    with pytest.raises(TypeError, match='seed must be an integer or None'):
        Simulation(seed=seed)
