from dataclasses import dataclass
from order_book import Trade, Order

@dataclass
class MatchResult:
    trades: list[Trade] = []
    completed_orders: list[Order] = []

    
