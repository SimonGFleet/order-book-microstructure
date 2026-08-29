from order_book import OrderBook
from traders import Trader


class Strategy:
    def __init__(self):
        self.open_orders = []


    def decide(self, trader: Trader, book: OrderBook, timestamp: int):
        pass
