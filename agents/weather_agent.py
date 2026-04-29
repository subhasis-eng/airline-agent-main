from langchain_openai import ChatOpenAI
import sqlparse
from tools.generate_and_execute_query import generate_and_execute_query

from database import get_pool
from tools.send_email import send_email


async def notify_rescheduled_passengers():
    pool = await get_pool()
    results = []

    async with pool.acquire() as conn:
        rows = await conn.fetch(
            """
            SELECT booking_id, flight_id, passenger_id, passenger_name, passenger_email,
                   airport_code, reason, rescheduled_at
            FROM public.rescheduled_bookings
            """
        )

    for row in rows:
        passenger_email = row["passenger_email"]

        if not passenger_email:
            print(f"[notify_agent] No email for passenger {row['passenger_id']}")
            results.append(
                {"passenger_id": row["passenger_id"], "status": "email_missing"}
            )
            continue  # ✅ FIX

        subject = f"Flight {row['flight_id']} Rescheduled Notification"
        body = f"""
Dear {row['passenger_name']},

Your flight {row['flight_id']} scheduled at {row['airport_code']} has been rescheduled.

Reason: {row['reason']}
New rescheduled time: {row['rescheduled_at'].strftime('%Y-%m-%d %H:%M:%S')}

Regards,
Airline Operations Team
"""

        email_status = send_email(passenger_email, subject, body)

        results.append(
            {
                "passenger_id": row["passenger_id"],
                "email": passenger_email,
                "status": "email_sent" if email_status else "email_failed",
                "booking_id": row["booking_id"],
                "flight_id": row["flight_id"],
            }
        )

    return {
        "status": "completed",
        "total_passengers": len(rows),
        "results": results,
    }


async def weather_agent(event):
    """
    Weather agent responsible for rescheduling bookings
    affected by high severity weather incidents.
    """
    print("[weather_agent] Handling event:", event.get("event_id"))

    llm = ChatOpenAI(temperature=0, model="gpt-4o-mini")

    # The SQL generator expects a LIST of incidents
    incidents = [event]

    await generate_and_execute_query(llm, incidents)
    await notify_rescheduled_passengers()

    return {"status": "rescheduling_completed", "event_id": event.get("incident_id")}
