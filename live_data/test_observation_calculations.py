from datetime import datetime, timezone
from decimal import Decimal

from live_book import liveBook


def test_observation_calculates_values_and_preserves_timestamp():
    book = liveBook()
    book.apply_level("bid", Decimal(100), Decimal(6))
    book.apply_level("offer", Decimal(102), Decimal(2))
    timestamp = datetime(2026, 1, 1, tzinfo=timezone.utc)

    observation = book.get_observation(timestamp)

    assert observation is not None
    assert observation.timestamp == timestamp
    assert observation.best_bid == Decimal(100)
    assert observation.best_ask == Decimal(102)
    assert observation.mid_price == Decimal(101)
    assert observation.spread == Decimal(2)
    assert observation.best_bid_quantity == Decimal(6)
    assert observation.best_ask_quantity == Decimal(2)
    assert observation.imbalance == Decimal("0.5")


def test_observation_returns_none_with_only_bids():
    book = liveBook()
    book.apply_level("bid", Decimal(100), Decimal(6))
    timestamp = datetime(2026, 1, 1, tzinfo=timezone.utc)

    assert book.get_observation(timestamp) is None


def test_observation_returns_none_with_only_offers():
    book = liveBook()
    book.apply_level("offer", Decimal(102), Decimal(2))
    timestamp = datetime(2026, 1, 1, tzinfo=timezone.utc)

    assert book.get_observation(timestamp) is None


def test_observation_imbalance_is_zero_with_equal_quantities():
    book = liveBook()
    book.apply_level("bid", Decimal(100), Decimal(4))
    book.apply_level("offer", Decimal(102), Decimal(4))
    timestamp = datetime(2026, 1, 1, tzinfo=timezone.utc)

    observation = book.get_observation(timestamp)

    assert observation is not None
    assert observation.imbalance == Decimal(0)


def test_observation_imbalance_is_negative_with_more_offer_quantity():
    book = liveBook()
    book.apply_level("bid", Decimal(100), Decimal(2))
    book.apply_level("offer", Decimal(102), Decimal(6))
    timestamp = datetime(2026, 1, 1, tzinfo=timezone.utc)

    observation = book.get_observation(timestamp)

    assert observation is not None
    assert observation.imbalance == Decimal("-0.5")
