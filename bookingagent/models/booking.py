from dataclasses import dataclass
from datetime import datetime


@dataclass
class Booking:
    booking_id: str
    passenger_name: str
    flight_number: str
    date: datetime
    status: str = "pending"
