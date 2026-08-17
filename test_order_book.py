#price priority, FIFO, quantities, and resting behaviour absolutely qualify.
from order_book import OrderBook
from models import MatchResult, Order, OrdType, Side, Trade

def test_bid_partially_fills_resting_ask():
    # Arrange
    book = OrderBook()

    resting_ask = Order(
        order_id=1,
        agent_id=10,
        side=Side.ASK,
        ord_type=OrdType.LIMIT,
        quantity=10,
        price=100,
    )

    incoming_bid = Order(
        order_id=2,
        agent_id=20,
        side=Side.BID,
        ord_type=OrdType.LIMIT,
        quantity=4,
        price=100,
    )

    book.match_order(resting_ask)

    # Act
    book.match_order(incoming_bid)

    # Assert
    assert incoming_bid.remaining_qty == 0
    assert resting_ask.remaining_qty == 6

    assert 100 in book.asks
    assert len(book.asks[100]) == 1
    assert book.asks[100][0] is resting_ask
    assert book.bids == {}


def test_market_order_does_not_rest():

    book = OrderBook()

    incoming_bid = Order(
        order_id=1,
        quantity=100,
        side = Side.BID,
        ord_type=OrdType.MARKET,
        price=None,
    )

    book.match_order(incoming_bid)

    assert book.bids == {}
    assert book.asks == {}


def test_fifo_for_same_price():
    book = OrderBook()

    first = Order(
        order_id=1,
        quantity=100,
        side=Side.ASK,
        ord_type=OrdType.LIMIT,
        price=100,
    )
    second = Order(
            order_id=2,
            quantity=100,
            side=Side.ASK,
            ord_type=OrdType.LIMIT,
            price=100,
        )
    third = Order(
            order_id=3,
            quantity=100,
            side=Side.ASK,
            ord_type=OrdType.LIMIT,
            price=100,
        )

    incoming_bid = Order(
        order_id=4,
        quantity=150,
        side=Side.BID,
        ord_type=OrdType.MARKET
    )
    
    book.match_order(first)
    book.match_order(second)
    book.match_order(third)

    res: MatchResult = book.match_order(incoming_bid)

    assert book.bids == {}
    assert first.remaining_qty == 0
    assert second.remaining_qty == 50
    assert third.remaining_qty == 100
    assert incoming_bid.remaining_qty == 0
    assert len(book.asks[100]) == 2

    assert book.asks[100][0] is second
    assert book.asks[100][1] is third

    assert book.trades[0].quantity == 100
    assert book.trades[1].quantity == 50
    assert res.trades[0].quantity == 100
    assert res.trades[1].quantity == 50
    assert res.trades[0].event_number == 0
    assert res.trades[1].event_number == 0


def test_non_crossing_limit_order_rests():
    book = OrderBook()

    incoming_bid = Order(
        order_id=1,
        quantity = 100,
        side=Side.BID,
        ord_type=OrdType.LIMIT,
        price=100,
        )

    resting_ask = Order(
        order_id=2,
        quantity=100,
        side=Side.ASK,
        ord_type=OrdType.LIMIT,
        price=105,
    )

    book.match_order(resting_ask)
    res: MatchResult = book.match_order(incoming_bid)

    assert incoming_bid.remaining_qty == incoming_bid.quantity
    assert book.bids[100][0] is incoming_bid
    assert book.asks[105][0] is resting_ask
    assert res.trades == []



def test_cancel_only_order_removes_price_level():
    book = OrderBook()

    order = Order(
        order_id=1,
        quantity=100,
        side=Side.BID,
        ord_type=OrdType.LIMIT,
        price=100,
    )

    book.match_order(order)

    cancelled_order = book.cancel_order(order)

    assert cancelled_order is order
    assert order.cancelled is True
    assert 100 not in book.bids
    assert book.asks == {}



def test_multiple_orders_receive_batch_event_numbers():
    book = OrderBook()

    first_ask = Order(
        order_id=1,
        quantity=5,
        side=Side.ASK,
        ord_type=OrdType.LIMIT,
        price=100,
    )
    second_ask = Order(
        order_id=2,
        quantity=7,
        side=Side.ASK,
        ord_type=OrdType.LIMIT,
        price=101,
    )
    third_ask = Order(
        order_id=3,
        quantity=10,
        side=Side.ASK,
        ord_type=OrdType.LIMIT,
        price=102,
    )

    book.match_order(first_ask)
    book.match_order(second_ask)
    book.match_order(third_ask)

    first_bid = Order(
        order_id=4,
        quantity=10,
        side=Side.BID,
        ord_type=OrdType.MARKET,
    )
    first_result = book.match_order(first_bid)

    assert len(first_result.trades) == 2
    assert [trade.price for trade in first_result.trades] == [100, 101]
    assert [trade.quantity for trade in first_result.trades] == [5, 5]
    assert [trade.sell_order_id for trade in first_result.trades] == [1, 2]
    assert [trade.event_number for trade in first_result.trades] == [0, 0]
    assert book.event_number == 1

    second_bid = Order(
        order_id=5,
        quantity=10,
        side=Side.BID,
        ord_type=OrdType.LIMIT,
        price=102,
    )
    second_result = book.match_order(second_bid)

    assert len(second_result.trades) == 2
    assert [trade.price for trade in second_result.trades] == [101, 102]
    assert [trade.quantity for trade in second_result.trades] == [2, 8]
    assert [trade.sell_order_id for trade in second_result.trades] == [2, 3]
    assert [trade.event_number for trade in second_result.trades] == [1, 1]
    assert book.event_number == 2

    final_bid = Order(
        order_id=6,
        quantity=1,
        side=Side.BID,
        ord_type=OrdType.MARKET,
    )
    final_result = book.match_order(final_bid)

    assert len(final_result.trades) == 1
    assert final_result.trades[0].price == 102
    assert final_result.trades[0].quantity == 1
    assert final_result.trades[0].sell_order_id == 3
    assert final_result.trades[0].event_number == 2
    assert book.event_number == 3

    assert [trade.event_number for trade in book.trades] == [0, 0, 1, 1, 2]
    assert [trade.buy_order_id for trade in book.trades] == [4, 4, 5, 5, 6]

    assert first_ask.remaining_qty == 0
    assert second_ask.remaining_qty == 0
    assert third_ask.remaining_qty == 1
    assert book.asks[102][0] is third_ask
    assert book.bids == {}

    assert first_result.completed_orders == [first_ask]
    assert second_result.completed_orders == [second_ask]
    assert final_result.completed_orders == []
