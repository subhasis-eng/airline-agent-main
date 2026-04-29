from pydantic import BaseModel
from typing import Optional
from datetime import datetime, date


# -----------------------------
# Aircraft
# -----------------------------
class Aircraft(BaseModel):
    aircraft_id: str
    registration_number: Optional[str]
    aircraft_type: Optional[str]
    manufacturer: Optional[str]
    total_seats: Optional[int]
    economy_seats: Optional[int]
    business_seats: Optional[int]
    first_seats: Optional[int]
    current_location: Optional[str]
    maintenance_status: Optional[str]
    last_maintenance: Optional[datetime]
    next_maintenance: Optional[datetime]

    class Config:
        orm_mode = True


# -----------------------------
# Aircraft Maintenance
# -----------------------------
class AircraftMaintenance(BaseModel):
    maintenance_id: str
    aircraft_id: Optional[str]
    maintenance_type: Optional[str]
    scheduled_start: Optional[datetime]
    scheduled_end: Optional[datetime]
    actual_start: Optional[datetime]
    actual_end: Optional[datetime]
    status: Optional[str]
    description: Optional[str]

    class Config:
        orm_mode = True


# -----------------------------
# Airport
# -----------------------------
class Airport(BaseModel):
    airport_code: str
    airport_name: Optional[str]
    city: Optional[str]
    country: Optional[str]
    timezone: Optional[str]
    max_hourly_slots: Optional[int]
    operational_status: Optional[str]

    class Config:
        orm_mode = True


# -----------------------------
# Crew
# -----------------------------
class Crew(BaseModel):
    crew_id: str
    first_name: Optional[str]
    last_name: Optional[str]
    crew_role: Optional[str]
    base_airport: Optional[str]
    certification: Optional[str]
    is_available: Optional[bool]
    last_duty: Optional[datetime]

    class Config:
        orm_mode = True


# -----------------------------
# Crew Assignment
# -----------------------------
class CrewAssignment(BaseModel):
    assignment_id: str
    crew_id: Optional[str]
    flight_id: Optional[str]
    role: Optional[str]
    assignment_date: Optional[date]
    status: Optional[str]

    class Config:
        orm_mode = True


# -----------------------------
# Crew Duty Time
# -----------------------------
class CrewDutyTime(BaseModel):
    duty_id: str
    crew_id: Optional[str]
    duty_start: Optional[datetime]
    duty_end: Optional[datetime]
    hours_worked: Optional[float]
    remaining_hours: Optional[float]
    requires_rest: Optional[bool]

    class Config:
        orm_mode = True


# -----------------------------
# Disruption (Events)
# -----------------------------
class Disruption(BaseModel):
    event_id: str
    event_type: Optional[str]
    severity: Optional[str]
    impact_description: Optional[str]
    airport_code: Optional[str]
    start_time: Optional[datetime]
    end_time: Optional[datetime]

    class Config:
        orm_mode = True


# -----------------------------
# Disruption Resolution
# -----------------------------
class DisruptionResolution(BaseModel):
    disruption_id: str
    resolution_type: Optional[str]
    resolved_at: Optional[datetime]
    resolution_status: Optional[str]
    passengers_booked: Optional[int]
    hotel_bookings_made: Optional[int]
    vouchers_issued: Optional[int]

    class Config:
        orm_mode = True


# -----------------------------
# Flight
# -----------------------------
class Flight(BaseModel):
    flight_id: str
    flight_number: Optional[str]
    aircraft_id: Optional[str]
    origin_airport: Optional[str]
    destination_airport: Optional[str]
    layover_airport: Optional[str]
    scheduled_departure: Optional[datetime]
    scheduled_arrival: Optional[datetime]
    actual_departure: Optional[datetime]
    actual_arrival: Optional[datetime]
    status: Optional[str]
    available_seats: Optional[int]

    class Config:
        orm_mode = True


# -----------------------------
# Flight Disruption
# -----------------------------
class FlightDisruption(BaseModel):
    disruption_id: str
    flight_id: Optional[str]
    event_type: Optional[str]
    severity: Optional[str]
    affected_passengers: Optional[int]
    status: Optional[str]
    requires_escalation: Optional[bool]

    class Config:
        orm_mode = True


# -----------------------------
# Flight Segment
# -----------------------------
class FlightSegment(BaseModel):
    flight_prefix: str
    primary_airline_name: Optional[str]
    parent_company_airline_group: Optional[str]
    co_company: Optional[str]

    class Config:
        orm_mode = True


# -----------------------------
# Hotel Booking
# -----------------------------
class HotelBooking(BaseModel):
    hotel_booking_id: str
    crew_id: Optional[str]
    passenger_id: Optional[str]
    hotel_name: Optional[str]
    hotel_address: Optional[str]
    check_in: Optional[datetime]
    check_out: Optional[datetime]
    booking_status: Optional[str]
    booking_reference: Optional[str]

    class Config:
        orm_mode = True


# -----------------------------
# Hotel Details
# -----------------------------
class HotelDetails(BaseModel):
    hotel_id: str
    hotel_name: Optional[str]
    airport_code: Optional[str]
    hotel_location: Optional[str]
    rooms_available: Optional[int]
    rooms_booked: Optional[int]
    available_from: Optional[date]
    available_till: Optional[date]

    class Config:
        orm_mode = True


# -----------------------------
# Passenger
# -----------------------------
class Passenger(BaseModel):
    passenger_id: str
    first_name: Optional[str]
    last_name: Optional[str]
    email: Optional[str]
    phone: Optional[str]
    frequent_flyer_number: Optional[str]
    loyalty_tier: Optional[str]
    preferred_contact_method: Optional[str]

    class Config:
        orm_mode = True


# -----------------------------
# Passenger Booking
# -----------------------------
class PassengerBooking(BaseModel):
    booking_id: str
    passenger_id: Optional[str]
    flight_id: Optional[str]
    pnr: Optional[str]
    seat_number: Optional[str]
    cabin_class: Optional[str]
    ticket_price: Optional[float]
    booking_status: Optional[str]
    booking_date: Optional[datetime]
    is_disrupted: Optional[bool]

    class Config:
        orm_mode = True


# -----------------------------
# Rebooking
# -----------------------------
class Rebooking(BaseModel):
    booking_id: str
    old_booking_id: Optional[str]
    flight_id: Optional[str]
    old_flight_id: Optional[str]
    rebooking_reason: Optional[str]
    auto_rebooked: Optional[bool]
    confirmation_status: Optional[str]

    class Config:
        orm_mode = True


# -----------------------------
# Voucher
# -----------------------------
class Voucher(BaseModel):
    voucher_id: str
    booking_id: Optional[str]
    voucher_type: Optional[str]
    expiry_date: Optional[date]
    status: Optional[str]

    class Config:
        orm_mode = True
