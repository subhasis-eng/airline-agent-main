from sqlalchemy import (
    Column,
    String,
    Integer,
    Float,
    Text,
    DateTime,
    Boolean,
    ForeignKey,
    Enum,
    PrimaryKeyConstraint,
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime

Base = declarative_base()


# ----------------------
# Aircraft
# ----------------------
class Aircraft(Base):
    __tablename__ = "aircraft"
    aircraft_id = Column(String, primary_key=True, index=True)
    registration_number = Column(String)
    aircraft_type = Column(String)
    manufacturer = Column(String)
    total_seats = Column(Integer)
    economy_seats = Column(Integer)
    business_seats = Column(Integer)
    first_seats = Column(Integer)
    current_location = Column(String, ForeignKey("airport.airport_code"))
    maintenance_status = Column(String)
    last_maintenance = Column(DateTime)
    next_maintenance = Column(DateTime)

    flights = relationship("Flight", back_populates="aircraft")


# ----------------------
# Aircraft Maintenance
# ----------------------
class AircraftMaintenance(Base):
    __tablename__ = "aircraft_maintenance"
    maintenance_id = Column(String, primary_key=True, index=True)
    aircraft_id = Column(String, ForeignKey("aircraft.aircraft_id"))
    maintenance_type = Column(String)
    scheduled_start = Column(DateTime)
    scheduled_end = Column(DateTime)
    actual_start = Column(DateTime)
    actual_end = Column(DateTime)
    status = Column(
        Enum(
            "Scheduled",
            "In Progress",
            "Completed",
            "Cancelled",
            name="maintenance_status_enum",
        )
    )
    description = Column(Text)


# ----------------------
# Airport
# ----------------------
class Airport(Base):
    __tablename__ = "airport"
    airport_code = Column(String, primary_key=True, index=True)
    airport_name = Column(String)
    city = Column(String)
    country = Column(String)
    timezone = Column(String)
    max_hourly_slots = Column(Integer)
    operational_status = Column(
        Enum("Open", "Closed", "TRUE", "Limited", name="airport_status_enum")
    )

    flights_origin = relationship(
        "Flight", back_populates="origin", foreign_keys="Flight.origin_airport"
    )
    flights_destination = relationship(
        "Flight",
        back_populates="destination",
        foreign_keys="Flight.destination_airport",
    )
    aircrafts = relationship("Aircraft", backref="current_airport")


# ----------------------
# Crew
# ----------------------
class Crew(Base):
    __tablename__ = "crew"
    crew_id = Column(String, primary_key=True, index=True)
    first_name = Column(String)
    last_name = Column(String)
    crew_role = Column(String)
    base_airport = Column(String, ForeignKey("airport.airport_code"))
    certification = Column(String)
    is_available = Column(Boolean)
    last_duty = Column(DateTime)

    assignments = relationship("CrewAssignment", back_populates="crew")
    duty_times = relationship("CrewDutyTime", back_populates="crew")


"Scheduled", "Active", "Suspended", "Completed", "Standby"


class CrewAssignment(Base):
    __tablename__ = "crew_assignment"
    assignment_id = Column(String, primary_key=True, index=True)
    crew_id = Column(String, ForeignKey("crew.crew_id"))
    flight_id = Column(String, ForeignKey("flight.flight_id"))
    role = Column(String)
    assignment_date = Column(DateTime)
    status = Column(
        Enum(
            "Scheduled",
            "Active",
            "Suspended",
            "Completed",
            "Standby",
            name="crew_assignment_status_enum",
        )
    )

    crew = relationship("Crew", back_populates="assignments")
    flight = relationship("Flight", back_populates="crew_assignments")


class CrewDutyTime(Base):
    __tablename__ = "crew_duty_time"
    duty_id = Column(String, primary_key=True, index=True)
    crew_id = Column(String, ForeignKey("crew.crew_id"))
    duty_start = Column(DateTime)
    duty_end = Column(DateTime)
    hours_worked = Column(Float)
    remaining_hours = Column(Float)
    requires_rest = Column(Boolean)

    crew = relationship("Crew", back_populates="duty_times")


# ----------------------
# Flight
# ----------------------
"En Route", "Cancelled", "Landed", "Delayed", "Scheduled"


class Flight(Base):
    __tablename__ = "flight"
    flight_id = Column(String, primary_key=True, index=True)
    flight_number = Column(String)
    aircraft_id = Column(String, ForeignKey("aircraft.aircraft_id"))
    origin_airport = Column(String, ForeignKey("airport.airport_code"))
    destination_airport = Column(String, ForeignKey("airport.airport_code"))
    layover_airport = Column(String, ForeignKey("airport.airport_code"), nullable=True)
    scheduled_departure = Column(DateTime)
    scheduled_arrival = Column(DateTime)
    actual_departure = Column(DateTime, nullable=True)
    actual_arrival = Column(DateTime, nullable=True)
    status = Column(
        Enum(
            "En Route",
            "Cancelled",
            "Landed",
            "Delayed",
            "Scheduled",
            name="flight_status_enum",
        )
    )
    available_seats = Column(Integer)

    aircraft = relationship("Aircraft", back_populates="flights")
    origin = relationship(
        "Airport", foreign_keys=[origin_airport], back_populates="flights_origin"
    )
    destination = relationship(
        "Airport",
        foreign_keys=[destination_airport],
        back_populates="flights_destination",
    )
    crew_assignments = relationship("CrewAssignment", back_populates="flight")
    bookings = relationship("PassengerBooking", back_populates="flight")
    disruptions = relationship("FlightDisruption", back_populates="flight")


# ----------------------
# Disruption
# ----------------------
class Disruption(Base):
    __tablename__ = "disruption"
    event_id = Column(String, primary_key=True, index=True)
    event_type = Column(
        Enum(
            "Delay",
            "Bomb Threat",
            "Weather",
            "Mechanical failure",
            "Crew Unavailability",
            "Traffic",
            name="disruption_type_enum",
        )
    )
    severity = Column(Enum("Low", "Medium", "High", "Critical", name="severity_enum"))
    impact_description = Column(Text)
    airport_code = Column(String, ForeignKey("airport.airport_code"))
    start_time = Column(DateTime)
    end_time = Column(DateTime)


class DisruptionResolution(Base):
    __tablename__ = "disruption_resolution"
    disruption_id = Column(String, primary_key=True, index=True)
    resolution_type = Column(
        Enum(
            "Rebooking", "Compensation", "Hotel", "Voucher", name="resolution_type_enum"
        )
    )
    resolved_at = Column(DateTime)
    resolution_status = Column(
        Enum("Ongoing", "Resolved", "Escalated", name="resolution_status_enum")
    )
    passengers_booked = Column(Integer)
    hotel_bookings_made = Column(Integer)
    vouchers_issued = Column(Integer)


class FlightDisruption(Base):
    __tablename__ = "flight_disruption"
    disruption_id = Column(String)
    flight_id = Column(String, ForeignKey("flight.flight_id"))
    event_type = Column(
        Enum(
            "Delay",
            "Bomb Threat",
            "Threat",
            "Weather",
            "Mechanical failure",
            "Crew Unavailability",
            "Traffic",
            name="disruption_type_enum",
        )
    )
    severity = Column(Enum("Low", "Medium", "High", "Critical", name="severity_enum"))
    affected_passengers = Column(Integer)
    status = Column(
        Enum(
            "Ongoing",
            "Resolved",
            "Escalated",
            "Active",
            "Cancelled",
            name="disruption_status_enum",
        )
    )
    requires_escalation = Column(Boolean)

    flight = relationship("Flight", back_populates="disruptions")

    __table_args__ = (PrimaryKeyConstraint("disruption_id", "flight_id"),)


# ----------------------
# Passenger
# ----------------------
class Passenger(Base):
    __tablename__ = "passenger"
    passenger_id = Column(String, primary_key=True, index=True)
    first_name = Column(String)
    last_name = Column(String)
    email = Column(String)
    phone = Column(String)
    frequent_flyer_number = Column(String)
    loyalty_tier = Column(String)
    preferred_contact_method = Column(String)

    bookings = relationship("PassengerBooking", back_populates="passenger")


class PassengerBooking(Base):
    __tablename__ = "passenger_booking"
    booking_id = Column(String, primary_key=True, index=True)
    passenger_id = Column(String, ForeignKey("passenger.passenger_id"))
    flight_id = Column(String, ForeignKey("flight.flight_id"))
    pnr = Column(String)
    seat_number = Column(String)
    cabin_class = Column(String)
    ticket_price = Column(Float)
    booking_status = Column(
        Enum("Confirmed", "Cancelled", "Checked In", name="booking_status_enum")
    )
    is_disrupted = Column(Boolean, default=False)

    passenger = relationship("Passenger", back_populates="bookings")
    flight = relationship("Flight", back_populates="bookings")
    vouchers = relationship("Voucher", back_populates="booking")


class Voucher(Base):
    __tablename__ = "voucher"
    voucher_id = Column(String, primary_key=True, index=True)
    booking_id = Column(String, ForeignKey("passenger_booking.booking_id"))
    voucher_type = Column(
        Enum(
            "Meal Voucher",
            "Lounge Access",
            "Refund Voucher",
            "Hotel Booking",
            name="voucher_type_enum",
        )
    )
    expiry_date = Column(DateTime)
    status = Column(Enum("Issued", "Redeemed", "Expired", name="voucher_status_enum"))

    booking = relationship("PassengerBooking", back_populates="vouchers")


# ----------------------
# Rebooking
# ----------------------
class Rebooking(Base):
    __tablename__ = "rebooking"
    booking_id = Column(String, primary_key=True)  # new booking
    old_booking_id = Column(String, ForeignKey("passenger_booking.booking_id"))
    flight_id = Column(String, ForeignKey("flight.flight_id"))
    old_flight_id = Column(String, ForeignKey("flight.flight_id"))
    rebooking_reason = Column(String)
    auto_rebooked = Column(Boolean)
    confirmation_status = Column(
        Enum("Pending", "Confirmed", "Failed", name="rebooking_status_enum")
    )


# ----------------------
# Hotel Booking
# ----------------------
class HotelBooking(Base):
    __tablename__ = "hotel_booking"
    hotel_booking_id = Column(String, primary_key=True, index=True, autoincrement=True)
    crew_id = Column(String, ForeignKey("crew.crew_id"), nullable=True)
    passenger_id = Column(String, ForeignKey("passenger.passenger_id"), nullable=True)
    hotel_name = Column(String)
    hotel_address = Column(String)
    check_in = Column(DateTime)
    check_out = Column(DateTime)
    booking_status = Column(
        Enum("Pending", "Confirmed", "Cancelled", name="hotel_booking_status_enum")
    )
    booking_reference = Column(String)


class HotelDetails(Base):
    __tablename__ = "hotel_details"
    hotel_id = Column(String, primary_key=True, index=True)
    hotel_name = Column(String)
    airport_code = Column(String, ForeignKey("airport.airport_code"))
    hotel_location = Column(String)
    rooms_available = Column(Integer)
    rooms_booked = Column(Integer)
    available_from = Column(DateTime)
    available_till = Column(DateTime)
