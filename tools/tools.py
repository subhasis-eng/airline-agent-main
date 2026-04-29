from langchain.tools import tool
import httpx

BASE_URL = "http://localhost:8001"


def safe_json(resp):
    if resp.status_code == 204:
        return []
    try:
        data = resp.json()
        return data if data is not None else []
    except Exception:
        return []


@tool
async def get_aircraft():
    """Get all aircraft"""
    async with httpx.AsyncClient() as client:
        resp = await client.get(f"{BASE_URL}/aircraft/")
        resp.raise_for_status()  # Raises exception if API fails
        return resp.json()


@tool
async def get_aircraft_maintenance():
    """Get all aircraft_maintenance"""
    async with httpx.AsyncClient() as client:
        resp = await client.get(f"{BASE_URL}/aircraft_maintenance/")
        resp.raise_for_status()  # Raises exception if API fails
        return resp.json()


@tool
async def get_airport():
    """Get all airport"""
    async with httpx.AsyncClient() as client:
        resp = await client.get(f"{BASE_URL}/airport/")
        resp.raise_for_status()  # Raises exception if API fails
        return resp.json()


@tool
async def get_crew():
    """Get all crew"""
    async with httpx.AsyncClient() as client:
        resp = await client.get(f"{BASE_URL}/crew/")
        resp.raise_for_status()  # Raises exception if API fails
        return safe_json(resp)


@tool
async def get_crew_assignment():
    """Get all crew_assignment"""
    async with httpx.AsyncClient() as client:
        resp = await client.get(f"{BASE_URL}/crew_assignment/")
        resp.raise_for_status()  # Raises exception if API fails
        return safe_json(resp)


@tool
async def get_crew_duty_time():
    """Get all crew_duty_time"""
    async with httpx.AsyncClient() as client:
        resp = await client.get(f"{BASE_URL}/crew_duty_time/")
        resp.raise_for_status()  # Raises exception if API fails
        return safe_json(resp)


@tool
async def get_disruption():
    """Get all disruption"""
    async with httpx.AsyncClient() as client:
        resp = await client.get(f"{BASE_URL}/disruption/")
        resp.raise_for_status()  # Raises exception if API fails
        return safe_json(resp)


@tool
async def disruption_resolution():
    """Get all disruption_resolution"""
    async with httpx.AsyncClient() as client:
        resp = await client.get(f"{BASE_URL}/disruption/")
        resp.raise_for_status()  # Raises exception if API fails
        return resp.json()


@tool
async def get_flights():
    """Get all flights"""
    async with httpx.AsyncClient() as client:
        resp = await client.get(f"{BASE_URL}/flight/")
        resp.raise_for_status()  # Raises exception if API fails
        return safe_json(resp)


@tool
async def get_flight_disruption():
    """Get all flight_disruption"""
    async with httpx.AsyncClient() as client:
        resp = await client.get(f"{BASE_URL}/flight_disruption/")
        resp.raise_for_status()  # Raises exception if API fails
        return resp.json()


@tool
async def get_flight_segment():
    """Get all flight_segment"""
    async with httpx.AsyncClient() as client:
        resp = await client.get(f"{BASE_URL}/flight_segment/")
        resp.raise_for_status()  # Raises exception if API fails
        return resp.json()


@tool
async def get_hotel_booking():
    """Get all hotel_booking"""
    async with httpx.AsyncClient() as client:
        resp = await client.get(f"{BASE_URL}/hotel_booking/")
        resp.raise_for_status()  # Raises exception if API fails
        return resp.json()


@tool
async def get_hotel_details():
    """Get all hotel_details"""
    async with httpx.AsyncClient() as client:
        resp = await client.get(f"{BASE_URL}/hotel_details/")
        resp.raise_for_status()  # Raises exception if API fails
        return resp.json()


@tool
async def get_passengers():
    """Get all passengers"""
    async with httpx.AsyncClient() as client:
        resp = await client.get(f"{BASE_URL}/passengers/")
        resp.raise_for_status()  # Raises exception if API fails
        return resp.json()


@tool
async def get_passenger_booking():
    """Get all passenger bookings"""
    async with httpx.AsyncClient() as client:
        resp = await client.get(f"{BASE_URL}/passenger_booking/")
        resp.raise_for_status()  # Raises exception if API fails
        return resp.json()


@tool
async def get_rebooking():
    """Get all rebooking"""
    async with httpx.AsyncClient() as client:
        resp = await client.get(f"{BASE_URL}/rebooking/")
        resp.raise_for_status()  # Raises exception if API fails
        return resp.json()


@tool
async def get_voucher():
    """Get all voucher"""
    async with httpx.AsyncClient() as client:
        resp = await client.get(f"{BASE_URL}/voucher/")
        resp.raise_for_status()  # Raises exception if API fails
        return resp.json()


@tool
async def get_incidents():
    """Get all incident decisions"""
    async with httpx.AsyncClient() as client:
        resp = await client.get(f"{BASE_URL}/master_decision_table/")
        resp.raise_for_status()  # Raises exception if API fails
        return resp.json()
