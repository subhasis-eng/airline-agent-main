# api/db/engine.py

from datetime import datetime
from sqlalchemy.orm import Session
from api.models import *


# ---------- READ OPERATIONS ----------


def get_airports_by_city(session: Session, city: str):
    return session.query(Airport).filter(Airport.city.ilike(f"%{city}%")).all()


def get_flights_by_airports(session: Session, airport_codes: list[str]):
    return (
        session.query(Flight)
        .filter(
            (Flight.origin_airport.in_(airport_codes))
            | (Flight.destination_airport.in_(airport_codes))
        )
        .all()
    )


def get_bookings_by_flight_ids(session: Session, flight_ids: list[int]):
    return (
        session.query(PassengerBooking)
        .filter(PassengerBooking.flight_id.in_(flight_ids))
        .all()
    )


def get_crews_and_aircraft(session: Session, flight_ids: list[int]):
    crews = (
        session.query(CrewAssignment)
        .filter(CrewAssignment.flight_id.in_(flight_ids))
        .all()
    )

    aircraft_ids = (
        session.query(Flight.aircraft_id)
        .filter(Flight.flight_id.in_(flight_ids))
        .distinct()
        .all()
    )

    aircraft_ids = [a[0] for a in aircraft_ids]

    aircrafts = (
        session.query(Aircraft).filter(Aircraft.aircraft_id.in_(aircraft_ids)).all()
    )

    return crews, aircrafts


# ---------- WRITE OPERATIONS ----------


def create_disruption(session: Session, disruption: Disruption):
    session.add(disruption)
    session.flush()
    return disruption


def close_airports(session: Session, airport_codes: list[str]):
    airports = (
        session.query(Airport).filter(Airport.airport_code.in_(airport_codes)).all()
    )
    for airport in airports:
        airport.operational_status = "Closed"


def reopen_airports(session: Session, airport_codes: list[str]):
    airports = (
        session.query(Airport).filter(Airport.airport_code.in_(airport_codes)).all()
    )

    for airport in airports:
        airport.operational_status = "Open"


def save_flight_disruptions(session: Session, records: list[FlightDisruption]):
    session.bulk_save_objects(records)


def resolve_disruption(session: Session, disruption_id: str):
    disruption = session.query(Disruption).filter_by(event_id=disruption_id).first()
    if disruption:
        disruption.end_time = datetime.utcnow()
        disruption.resolution_status = "Resolved"


def get_allocated_crews_and_aircraft(session: Session, flight_ids: list[int]):
    crews = (
        session.query(CrewAssignment)
        .filter(CrewAssignment.flight_id.in_(flight_ids))
        .all()
    )

    aircrafts = session.query(Aircraft).filter(Aircraft.flight_id.in_(flight_ids)).all()

    return crews, aircrafts


def deallocate_crews_and_aircraft(session: Session, crews, aircrafts):
    for crew in crews:
        crew.flight_id = None
        crew.status = "Suspended"

    for aircraft in aircrafts:
        aircraft.flight_id = None
        aircraft.status = "Security Hold"


def get_available_hotels(session: Session, airport_code: str):
    """
    Fetch all hotels near an airport with available rooms.
    """
    return (
        session.query(HotelDetails)
        .filter(
            HotelDetails.airport_code == airport_code, HotelDetails.rooms_available > 0
        )
        .all()
    )


def save_hotel_bookings(session: Session, bookings: list[HotelBooking]):
    """
    Bulk save hotel bookings.
    """
    session.bulk_save_objects(bookings)
    session.flush()


def save_vouchers(session, vouchers: list):
    """
    Save voucher records in bulk.
    """
    if not vouchers:
        return
    session.bulk_save_objects(vouchers)
    session.flush()


def get_city_by_airport_code(session, airport_code: str) -> str:
    airport_code = airport_code[0]
    print("airport_code::",airport_code)
    airport = session.query(Airport).filter_by(airport_code=airport_code).first()
    if not airport:
        raise ValueError(f"Invalid airport code: {airport_code}")
    return airport.city