from datetime import datetime, timezone
from decimal import Decimal

from live_book import liveBook


def test_new_book_is_empty():
    book = liveBook()
    timestamp = datetime(2026, 1, 1, tzinfo=timezone.utc)

    assert book.bids == {}
    assert book.asks == {}
    assert book.best_bid() is None
    assert book.best_ask() is None
    assert book.get_observation(timestamp) is None



def test_highest_bid():
    book = liveBook()

    book.apply_level("bid", 100, 1)
    book.apply_level("bid", 102, 1)
    book.apply_level("bid", 99, 1)

    assert book.best_bid() == Decimal("102")


def test_lowest_ask():
    book = liveBook()

    book.apply_level("offer", 100, 1)
    book.apply_level("offer", 102, 1)
    book.apply_level("offer", 99, 1)

    assert book.best_ask() == Decimal("99")


def test_updating_existing_prices():
    book = liveBook()

    book.apply_level("bid", 90, 5)
    book.apply_level("offer", 110, 5)

    assert book.bids[90] == Decimal("5")
    assert book.asks[110] == Decimal("5")

    book.apply_level("bid", 90, 3)
    book.apply_level("offer", 110, 3)

    assert book.bids[90] == Decimal("3")
    assert book.asks[110] == Decimal("3")

def test_setting_to_zero_deletes_level():
    book = liveBook()

    book.apply_level("bid", Decimal(90), Decimal(5))
    book.apply_level("offer", Decimal(110), Decimal(5))

    assert book.bids[Decimal(90)] == Decimal("5")
    assert book.asks[Decimal(110)] == Decimal("5")

    book.apply_level("bid", Decimal(90), Decimal(0))
    book.apply_level("offer", Decimal(110), Decimal(0))

    assert Decimal(90) not in book.bids
    assert Decimal(110) not in book.asks

    assert book.best_bid() is None
    assert book.best_ask() is None

def test_deleting_best_level_reveals_next_best():
    book = liveBook()
    book.apply_level("bid", Decimal(90), Decimal(5))
    book.apply_level("bid", Decimal(89), Decimal(3))
    book.apply_level("offer", Decimal(110), Decimal(5))
    book.apply_level("offer", Decimal(111), Decimal(3))

    book.apply_level("bid", Decimal(90), Decimal(0))
    book.apply_level("offer", Decimal(110), Decimal(0))

    assert book.best_bid() == Decimal(89)
    assert book.best_ask() == Decimal(111)
    assert book.bids == {Decimal(89): Decimal(3)}
    assert book.asks == {Decimal(111): Decimal(3)}


def test_deleting_missing_level_leaves_book_unchanged():
    book = liveBook()
    book.apply_level("bid", Decimal(90), Decimal(5))
    book.apply_level("offer", Decimal(110), Decimal(3))

    book.apply_level("bid", Decimal(89), Decimal(0))
    book.apply_level("offer", Decimal(111), Decimal(0))

    assert book.bids == {Decimal(90): Decimal(5)}
    assert book.asks == {Decimal(110): Decimal(3)}


def test_reconstruct_initial_replaces_existing_book():
    book = liveBook()
    book.apply_level("bid", Decimal(90), Decimal(5))
    book.apply_level("offer", Decimal(110), Decimal(3))
    snapshot_rows = [
        {"side": "bid", "price": "100", "quantity": "6"},
        {"side": "offer", "price": "102", "quantity": "2"},
    ]

    book.reconstruct_initial(snapshot_rows)

    assert book.bids == {Decimal(100): Decimal(6)}
    assert book.asks == {Decimal(102): Decimal(2)}
    for levels in (book.bids, book.asks):
        for price, quantity in levels.items():
            assert isinstance(price, Decimal)
            assert isinstance(quantity, Decimal)
