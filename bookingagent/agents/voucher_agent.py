from services.voucher_service import VoucherService
from services.booking_service import BookingService


class VoucherAgent:
    def __init__(self):
        self.voucher_service = VoucherService()
        self.booking_service = BookingService()  # Only needed if validating booking

    def issue_voucher(self, booking_id, amount):
        """
        Issues a voucher for the given booking.
        """

        # Optional: Validate booking exists
        booking = self.booking_service.get_booking(booking_id)
        if not booking:
            raise ValueError(f"Booking {booking_id} not found. Cannot issue voucher.")

        voucher = self.voucher_service.generate_voucher(booking_id, amount)

        print(f"Voucher issued: {voucher}")
        return voucher
