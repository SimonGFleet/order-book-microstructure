from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from sortedcontainers import SortedDict
from storage import get_boundary_time


@dataclass(frozen=True)
class bookObvservation:
    timestamp: datetime
    best_bid: Decimal
    best_ask: Decimal
    mid_price: Decimal
    spread: Decimal
    best_bid_quantity: Decimal
    best_ask_quantity: Decimal
    imbalance: Decimal | None = None    # using imbalance as [-1,1], how weighted are the current best prices



class liveBook:
    '''Stores a current instance of a book'''
    def __init__(self):
        self.bids = SortedDict()    # access best with -1
        self.asks = SortedDict()    # these are sorted in ascending, so best ask is first (0)
    

    def apply_level(self, side: str, price: Decimal, quantity: Decimal):
        if side == 'bid':
            levels = self.bids
        elif side == 'offer':
            levels = self.asks
        else:
            raise ValueError(f"unknown side: {side!r}.")

        if quantity == 0:
            levels.pop(price, None)
        else:
            levels[price] = quantity

    def reconstruct_initial(self, snapshot_rows):
        '''filters the db by session id and for snapshots
        goes through each row and looks at the side, decides if bid/ask, then adds row to dictionary'''
        self.bids.clear()
        self.asks.clear()
        
        for row in snapshot_rows:
            self.apply_level(
                side=row["side"],
                price=Decimal(row["price"]),
                quantity=Decimal(row["quantity"]),
            )

    def best_bid(self):
        return self.bids.peekitem(-1)[0] if self.bids else None

    def best_ask(self):
        return self.asks.peekitem(0)[0] if self.asks else None


    def get_observation(self, timestamp: datetime) -> bookObvservation | None:

        bid = self.best_bid()
        ask = self.best_ask()

        if bid is None or ask is None:
            return None

        bid_qty = self.bids[bid]
        ask_qty = self.asks[ask]
        imbalance = (bid_qty - ask_qty) / (bid_qty + ask_qty)

        return bookObvservation(timestamp=timestamp, best_bid=bid, best_ask=ask,
                         mid_price=(bid+ask)/2,
                         spread=ask-bid,
                         best_bid_quantity=bid_qty,
                         best_ask_quantity=ask_qty,
                         imbalance=imbalance,
                         )