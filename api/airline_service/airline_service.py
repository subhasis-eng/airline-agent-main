from datetime import datetime, timedelta

from api.airline_console.airline_engine import fetch_realtime_disruptions


def get_realtime_disruption_details(session, minutes=30):
    rows = fetch_realtime_disruptions(session, minutes)
    print("rows", rows)

    data = []
    for r in rows:
        data.append(
            {
                "disruption_id": r.event_id,
                "event_type": r.event_type,
                "severity": r.severity,
                "impact_description": r.impact_description,
                "start_time": r.start_time,
                "end_time": r.end_time,
                "airport": {"name": r.airport_name, "city": r.city},
                "flight": {
                    "flight_id": r.flight_id,
                    "flight_number": r.flight_number,
                    "origin": r.origin_airport,
                    "destination": r.destination_airport,
                    "status": r.flight_status,
                },
                "impact": {
                    "affected_passengers": r.affected_passengers,
                    "requires_escalation": r.requires_escalation,
                    "status": r.flight_disruption_status,
                },
            }
        )

    return {"window_minutes": minutes, "count": len(data), "data": data}
