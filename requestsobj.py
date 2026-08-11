from dataclasses import dataclass
from enum import Enum

from order_book import Order


class ReqType(Enum):
    CANCEL = 'cancel'
    PLACE = 'place'

@dataclass
class Request:
    req_type: ReqType
    order: Order
