from order_book import OrderBook
from agents import Trader


class Strategy:
    def __init__(self):
        self.open_orders = []


    def decide(self, agent: Trader, book: OrderBook, timestamp: int):
        pass
