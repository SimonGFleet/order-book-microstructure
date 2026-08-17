from dataclasses import dataclass, field
from enum import Enum


class Side(Enum):
    BID = "bid"
    ASK = "ask"


class OrdType(Enum):
    MARKET = "market"
    LIMIT = "limit"


@dataclass
class Order:
    quantity: int
    side: Side
    ord_type: OrdType
    order_id: int | None = None
    cancelled: bool = False

    creation_time: int | None = None
    price: int | None = None
    agent_id: int | None = None
    stock_id: int | None = None

    remaining_qty: int = field(init=False)

    def __post_init__(self) -> None:
        self.remaining_qty = self.quantity


@dataclass
class Trade:
    price: int
    quantity: int
    buy_order_id: int
    sell_order_id: int
    event_number: int
    timestamp: int | None = None
    buy_agent_id: int | None = None
    sell_agent_id: int | None = None


@dataclass
class MatchResult:
    trades: list[Trade] = field(default_factory=list)
    completed_orders: list[Order] = field(default_factory=list)


class ReqType(Enum):
    CANCEL = "cancel"
    PLACE = "place"


@dataclass
class Request:
    req_type: ReqType
    order: Order


@dataclass
class SimulationSnapshot:
    timestamp: int
    best_bid: int | None
    best_ask: int | None
    mid_price: float | None = None
    spread: int | None = None
    trade_count: int = 0
    traded_volume: int = 0
