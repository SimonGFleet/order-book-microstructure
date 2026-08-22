from order_book import OrderBook
from agents import Agent


class Strategy:
    def __init__(self):
        self.open_orders = []


    def decide(self, agent: Agent, book: OrderBook, timestamp: int):
        pass
