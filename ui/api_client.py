# api_client.py

import streamlit as st
import requests

BASE_URL = "http://localhost:5000"


def fetch_data(endpoint: str):
    """Fetches data from the specified API endpoint."""
    try:
        response = requests.get(f"{BASE_URL}{endpoint}")
        response.raise_for_status()
        return response.json()
    except requests.exceptions.ConnectionError:
        # Silently fail on connection errors to keep the dashboard loop running
        return None
    except requests.exceptions.RequestException as e:
        # st.error(f"API Error fetching {endpoint}: {e}") # Suppress this error to avoid flooding the UI
        return None


def post_threat_simulation(city: str, alternate_airport: str | None) -> dict | str:
    """Posts a bomb threat to the Flask API."""
    try:
        params = {"city": city}
        if alternate_airport:
            params["alternate_airport"] = alternate_airport

        response = requests.post(f"{BASE_URL}/disruption/city", params=params)
        
        response.raise_for_status()
        
        return f"Threat successfully simulated in **{city}**!"

    except requests.exceptions.HTTPError as e:
        try:
            error_data = response.json()
            return error_data
        except:
            return {"error": f"HTTP Error {response.status_code}: {e}"}

    except requests.exceptions.RequestException as e:
        return {"error": f"Connection or unexpected error: {e}"}
    

def post_upload_pdf(file):
    """Uploads PDF and triggers threat processing in Flask API."""
    try:
        BASE_URL_ = "http://localhost:8000"
        files = {
            "file": (file.name, file.getbuffer(), "application/pdf")
        }

        response = requests.post(
            f"{BASE_URL_}/upload",
            files=files,
            timeout=30
        )

        response.raise_for_status()
        return response.json()

    except requests.exceptions.HTTPError:
        try:
            return response.json()
        except:
            return {"error": f"HTTP Error {response.status_code}"}

    except requests.exceptions.RequestException as e:
        return {"error": f"Connection or unexpected error: {e}"}
