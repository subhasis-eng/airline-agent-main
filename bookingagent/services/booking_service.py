from models.booking import Booking
from datetime import datetime


class BookingService:
    def __init__(self):
        self.bookings = {}  # In-memory storage

    def create_booking(self, booking_id, passenger_name, flight_number, date):
        booking = Booking(booking_id, passenger_name, flight_number, date)
        self.bookings[booking_id] = booking
        return booking

    def get_booking(self, booking_id):
        return self.bookings.get(booking_id)

    def update_status(self, booking_id, status):
        if booking_id in self.bookings:
            self.bookings[booking_id].status = status
            return self.bookings[booking_id]
        return None
