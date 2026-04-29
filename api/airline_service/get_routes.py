from fastapi import APIRouter
from api.database import fetch_all

router = APIRouter()


# --- Aircraft ---
@router.get("/aircraft/")
async def get_aircrafts():
    return await fetch_all("aircraft")


# --- Aircraft Maintenance ---
@router.get("/aircraft_maintenance/")
async def get_aircraft_maintenance():
    return await fetch_all("aircraft_maintenance")


# --- Airport ---
@router.get("/airport/")
async def get_airports():
    return await fetch_all("airport")


# --- Crew ---
@router.get("/crew/")
async def get_crew():
    return await fetch_all("crew")


# --- Crew Assignment ---
@router.get("/crew_assignment/")
async def get_crew_assignments():
    return await fetch_all("crew_assignment")


# --- Crew Duty Time ---
@router.get("/crew_duty_time/")
async def get_crew_duty_time():
    return await fetch_all("crew_duty_time")


# --- Disruption ---
@router.get("/disruption/")
async def get_disruptions():
    return await fetch_all("disruption")


# --- Disruption Resolution ---
@router.get("/disruption_resolution/")
async def get_disruption_resolutions():
    return await fetch_all("disruption_resolution")


# --- Flight ---
@router.get("/flight/")
async def get_flights():
    return await fetch_all("flight")


# --- Flight Disruption ---
@router.get("/flight_disruption/")
async def get_flight_disruptions():
    return await fetch_all("flight_disruption")


# --- Flight Segment ---
@router.get("/flight_segment/")
async def get_flight_segments():
    return await fetch_all("flight_segment")


# --- Hotel Booking ---
@router.get("/hotel_booking/")
async def get_hotel_bookings():
    return await fetch_all("hotel_booking")


# --- Hotel Details ---
@router.get("/hotel_details/")
async def get_hotel_details():
    return await fetch_all("hotel_details")


# --- Passenger ---
@router.get("/passenger/")
async def get_passengers():
    return await fetch_all("passenger")


# --- Passenger Booking ---
@router.get("/passenger_booking/")
async def get_passenger_bookings():
    return await fetch_all("passenger_booking")


# --- Rebooking ---
@router.get("/rebooking/")
async def get_rebookings():
    return await fetch_all("rebooking")


# --- Voucher ---
@router.get("/voucher/")
async def get_vouchers():
    return await fetch_all("voucher")


# --- master_decision_table ---
@router.get("/master_decision_table/")
async def get_vouchers():
    return await fetch_all("master_decision_table")
