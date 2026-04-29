# api/services/bomb_threat_service.py

from datetime import datetime, timedelta
import random
import string
import uuid
from functools import lru_cache

from sqlalchemy.orm import joinedload
from geopy.geocoders import Nominatim

from api.reader import get_session_and_engine
from api.models import (
    Disruption,
    FlightDisruption,
    HotelBooking,
    Voucher,
    Flight,
    Airport,
)
from api.airline_console.airline_engine import (
    get_airports_by_city,
    get_flights_by_airports,
    get_bookings_by_flight_ids,
    get_crews_and_aircraft,
    create_disruption,
    close_airports,
    save_flight_disruptions,
    get_available_hotels,
    save_hotel_bookings,
    save_vouchers,
)


geolocator = Nominatim(user_agent="airline_ops_dashboard")


def _generate_booking_ref() -> str:
    date_str = datetime.utcnow().strftime("%Y%m%d")
    unique_id = uuid.uuid4().hex[:6].upper()
    return f"H-{date_str}-{unique_id}"


def _generate_booking_id():
    return f"HB-{uuid.uuid4().hex[:8].upper()}"


def _generate_event_id() -> str:
    return f"EV-{int(datetime.utcnow().timestamp() * 1000)}"


def _generate_voucher_ref() -> str:
    return f"V{''.join(random.choices(string.ascii_uppercase + string.digits, k=6))}"


def bomb_decision(flight, airport_codes, alternate_airport):
    if alternate_airport and flight.status == "En Route":
        return "Rerouted", alternate_airport
    return "Cancelled", flight.destination_airport


def weather_decision(flight, severity, alternate_airport):
    if severity == "Low":
        return "Delayed", flight.destination_airport
    if severity == "Medium":
        return (
            ("Rerouted", alternate_airport)
            if alternate_airport
            else ("Delayed", flight.destination_airport)
        )
    return "Cancelled", flight.destination_airport


def allocate_hotels(session, crews, passengers, airport_code):
    hotels = get_available_hotels(session, airport_code)
    hotel_bookings, vouchers = [], []
    current_time = datetime.utcnow()
    booking_counter = 2000

    def book_room(crew_id=None, passenger_id=None):
        nonlocal booking_counter
        for hotel in hotels:
            print("booking_counter::", booking_counter)
            if hotel.rooms_available <= 0:
                continue
            hotel.rooms_available -= 1
            hotel.rooms_booked += 1
            hotel_booking_id = _generate_booking_id()
            hotel_bookings.append(
                HotelBooking(
                    hotel_booking_id=hotel_booking_id,
                    crew_id=crew_id,
                    passenger_id=passenger_id,
                    hotel_name=hotel.hotel_name,
                    hotel_address=hotel.hotel_location,
                    check_in=current_time,
                    check_out=current_time + timedelta(hours=24),
                    booking_status="Confirmed",
                    booking_reference=_generate_booking_ref(),
                )
            )
            booking_counter += 1
            return True
        return False

    for crew in crews:
        if not book_room(crew_id=crew.crew_id):
            vouchers.append(
                Voucher(
                    passenger_id=None,
                    voucher_type="Meal Voucher",
                    expiry_date=current_time + timedelta(days=1),
                    status="Issued",
                    voucher_reference=_generate_voucher_ref(),
                )
            )

    for passenger in passengers:
        if not book_room(passenger_id=passenger.passenger_id):
            vouchers.append(
                Voucher(
                    voucher_id=_generate_voucher_ref(),
                    booking_id=passenger.booking_id,
                    voucher_type="Meal Voucher",
                    expiry_date=current_time + timedelta(days=1),
                    status="Issued",
                )
            )

    save_hotel_bookings(session, hotel_bookings)
    save_vouchers(session, vouchers)


def handle_flights(
    session, disruption_type, airport_codes, alternate_airport, severity
):
    flights = get_flights_by_airports(session, airport_codes)
    flight_disruptions, affected_flight_ids = [], []
    parent_event_id = _generate_event_id()

    for idx, flight in enumerate(flights):
        status, destination = (
            bomb_decision(flight, airport_codes, alternate_airport)
            if disruption_type == "bomb"
            else weather_decision(flight, severity, alternate_airport)
        )
        flight.status = status
        flight.destination_airport = destination
        affected_flight_ids.append(flight.flight_id)

        flight_disruptions.append(
            FlightDisruption(
                disruption_id=f"{parent_event_id}-{idx}",
                flight_id=flight.flight_id,
                event_type=disruption_type.title(),
                severity=severity or "Critical",
                affected_passengers=flight.available_seats,
                status=status,
                requires_escalation=True,
            )
        )
    return flights, flight_disruptions, affected_flight_ids, parent_event_id


def suspend_crews_and_aircraft(session, affected_flight_ids):
    crews, aircrafts = get_crews_and_aircraft(session, affected_flight_ids)
    for crew in crews:
        crew.status = "Suspended"
    for aircraft in aircrafts:
        aircraft.status = "Security Hold"
    return crews, aircrafts


def process_city_disruption(
    city: str,
    disruption_type: str,
    alternate_airport: str | None = None,
    severity: str | None = None,
):
    session, _ = get_session_and_engine()
    try:
        with session.begin():
            airports = get_airports_by_city(session, city)
            if not airports:
                raise ValueError(f"No airports found for city: {city}")
            airport_codes = [a.airport_code for a in airports]

            disruption = create_disruption_record(
                session, disruption_type, city, airport_codes, severity
            )
            if disruption_type == "bomb":
                close_airports(session, airport_codes)

            flights, flight_disruptions, affected_flight_ids, _ = handle_flights(
                session, disruption_type, airport_codes, alternate_airport, severity
            )
            if flight_disruptions:
                session.add_all(flight_disruptions)

            crews, _ = suspend_crews_and_aircraft(session, affected_flight_ids)
            passengers = get_bookings_by_flight_ids(session, affected_flight_ids)
            for code in airport_codes:
                allocate_hotels(session, crews, passengers, code)

        return {
            "city": city,
            "type": disruption_type,
            "affected_airports": airport_codes,
            "flights_affected": len(flights),
            "disruption_id": disruption.event_id,
        }
    finally:
        session.close()


def get_dashboard_summary(session):
    incidents = session.query(FlightDisruption).all()
    total_incidents = len(incidents)
    escalated_count = sum(1 for i in incidents if i.requires_escalation)
    total_passengers = sum(i.affected_passengers for i in incidents)
    return {
        "Total Incidents": total_incidents,
        "Escalated": escalated_count,
        "Passengers Affected": total_passengers,
        "Automated Actions": total_incidents,
    }


def get_incident_feed(session):
    incidents = session.query(FlightDisruption).all()
    return [
        {
            "Flight": i.flight_id,
            "Issue Type": i.event_type,
            "Status": i.status,
            "Agent Action": "Auto" if i.status != "Resolved" else "Manual",
            "Escalated": i.requires_escalation,
            "Passengers Affected": i.affected_passengers,
        }
        for i in incidents
    ]


def get_incident_map_data(session):
    incidents = session.query(FlightDisruption).all()
    data = []
    for incident in incidents:
        flight = session.query(Flight).filter_by(flight_id=incident.flight_id).first()
        airport = (
            session.query(Airport).filter_by(airport_code=flight.origin_airport).first()
            if flight
            else None
        )
        data.append(
            {
                "Flight": incident.flight_id,
                "City": airport.city if airport else "Unknown",
                "Latitude": 0,
                "Longitude": 0,
                "Status": incident.status,
            }
        )
    return data


def get_bookings(session, flight_id=None, city=None):
    flight_ids = []
    if flight_id:
        flight_ids.append(flight_id)
    elif city:
        airports = get_airports_by_city(session, city)
        airport_codes = [a.airport_code for a in airports]
        flights = (
            session.query(Flight)
            .filter(
                (Flight.origin_airport.in_(airport_codes))
                | (Flight.destination_airport.in_(airport_codes))
            )
            .all()
        )
        flight_ids = [f.flight_id for f in flights]
    bookings = get_bookings_by_flight_ids(session, flight_ids)
    return [
        {
            "Flight": b.flight_id,
            "Passenger ID": b.passenger_id,
            "Booking Status": b.booking_status,
            "Voucher Issued": b.is_disrupted,
        }
        for b in bookings
    ]


def get_status_distribution(session):
    incidents = session.query(FlightDisruption).all()
    status_counts = {}
    for incident in incidents:
        status_counts[incident.status] = status_counts.get(incident.status, 0) + 1
    return status_counts


def get_escalation_rate(session):
    incidents = session.query(FlightDisruption).all()
    total = len(incidents)
    escalated = sum(1 for i in incidents if i.requires_escalation)
    rate = (escalated / total * 100) if total else 0
    return {"Escalation Rate (%)": rate}


@lru_cache(maxsize=128)
def resolve_airport_location(airport_code: str, country: str):
    try:
        location = geolocator.geocode(f"{airport_code} airport, {country}", timeout=10)
        if location:
            return location.latitude, location.longitude
    except Exception:
        pass
    return None, None


def get_dashboard_map_data(session):
    disruptions = (
        session.query(FlightDisruption)
        .options(joinedload(FlightDisruption.flight).joinedload(Flight.destination))
        .all()
    )
    result = []
    for incident in disruptions:
        flight = incident.flight
        airport = flight.destination if flight else None
        if not airport:
            continue
        lat, lon = resolve_airport_location(airport.airport_code, airport.country)
        if lat is None:
            continue
        result.append(
            {
                "flight_number": flight.flight_number,
                "city": airport.city,
                "airport": airport.airport_name,
                "status": incident.status,
                "event_type": incident.event_type,
                "affected_passengers": incident.affected_passengers,
                "latitude": lat,
                "longitude": lon,
            }
        )
    return result


def create_disruption_record(
    session,
    disruption_type: str,
    city: str,
    airport_codes: list,
    severity: str | None = None,
) -> Disruption:
    """
    Create a master disruption record in the Disruption table.
    Returns the created Disruption object.
    """
    disruption = Disruption(
        event_id=_generate_event_id(),
        event_type="Bomb Threat" if disruption_type == "bomb" else "Weather",
        severity=severity or ("Critical" if disruption_type == "bomb" else "High"),
        airport_code=",".join(airport_codes),
        impact_description=f"{disruption_type.title()} disruption in {city}",
        start_time=datetime.utcnow(),
        end_time=None,
    )
    session.add(disruption)
    session.flush()  # flush to assign primary key if needed
    return disruption
