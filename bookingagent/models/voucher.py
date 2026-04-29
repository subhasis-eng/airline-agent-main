from dataclasses import dataclass
from datetime import datetime


@dataclass
class Voucher:
    voucher_id: str
    booking_id: str
    issued_on: datetime
    amount: float
