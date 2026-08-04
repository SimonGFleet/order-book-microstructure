from order_book import OrderBook, Order, Side, OrdType, Trade


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

print(book.match_order(first))
print(book.match_order(second))
print(book.match_order(third))

print(book.match_order(incoming_bid))

print(book.trades)