from agents.booking_agent import BookingAgent
from datetime import datetime

if __name__ == "__main__":
    agent = BookingAgent()
    agent.process_booking(
        booking_id="B001",
        passenger_name="John Doe",
        flight_number="AI202",
        date=datetime(2025, 12, 15, 10, 0),
        voucher_amount=100.0,
    )
