from services.booking_service import BookingService
from services.voucher_service import VoucherService


class BookingAgent:
    def __init__(self):
        self.booking_service = BookingService()
        self.voucher_service = VoucherService()

    def process_booking(
        self, booking_id, passenger_name, flight_number, date, voucher_amount=None
    ):
        booking = self.booking_service.create_booking(
            booking_id, passenger_name, flight_number, date
        )
        print(f"Booking created: {booking}")

        if voucher_amount:
            voucher = self.voucher_service.generate_voucher(booking_id, voucher_amount)
            print(f"Voucher generated: {voucher}")

        self.booking_service.update_status(booking_id, "confirmed")
        print(f"Booking status updated: {self.booking_service.get_booking(booking_id)}")
