import json
import asyncio
from dotenv import load_dotenv

from langchain_openai import ChatOpenAI
from langchain.schema import HumanMessage, SystemMessage

from tools.tools import get_flights, get_airport, get_passenger_booking, get_crew_assignment, get_disruption
from tools.generate_bomb_threat_query import generate_bomb_threat_query
from tools.send_email import send_email
from database import get_pool

load_dotenv()

async def notify_bomb_threat_passengers():
    """Confirms bomb threat notifications for recent events."""
    pool = await get_pool()
    results = []
    
    query = """
        SELECT booking_id, flight_id, passenger_id, passenger_name, passenger_email,
               airport_code, reason, rescheduled_at
        FROM public.rescheduled_bookings
        WHERE reason LIKE 'BOMB_THREAT%'
        AND rescheduled_at >= NOW() - INTERVAL '1 hour'
    """

    async with pool.acquire() as conn:
        rows = await conn.fetch(query)

    print(f"[Notifications] Found {len(rows)} passengers to alert.")

    for row in rows:
        p_name = row['passenger_name']
        p_email = row['passenger_email']
        flight_id = row['flight_id']
        reason = row['reason']
        t_stamp = row['rescheduled_at'].strftime('%Y-%m-%d %H:%M') if row['rescheduled_at'] else 'N/A'
        
        if not p_email:
            results.append({"passenger_id": row['passenger_id'], "status": "missing_email"})
            continue

        # Notification content depends on whether they were rerouted or cancelled
        if 'REROUTED' in reason:
            subject = f"Flight {flight_id} Diverted - Security Alert"
            body = f"""
Dear {p_name},

Due to a security incident at {row['airport_code']}, flight {flight_id} has been diverted.

Status: {reason}
Time: {t_stamp}

Please follow ground crew instructions upon landing. Transportation to your original destination will be provided.

Regards,
Airline Operations
"""
        else:
            subject = f"Flight {flight_id} Cancelled - Refund Voucher Issued"
            body = f"""
Dear {p_name},

Due to a security incident at {row['airport_code']}, flight {flight_id} is cancelled.

Status: {reason}
Time: {t_stamp}

A refund voucher has been credited to your account, valid for 12 months.

Regards,
Airline Operations
"""

        if send_email(p_email, subject, body):
            print(f" -> Sent to {p_email}")
            status = "sent"
        else:
            print(f" -> Failed to send to {p_email}")
            status = "failed"

        results.append({
            "passenger_id": row['passenger_id'],
            "email": p_email,
            "status": status,
            "flight_id": flight_id
        })

    return {
        "processed": len(rows),
        "sent": sum(1 for r in results if r['status'] == 'sent'),
        "failed": sum(1 for r in results if r['status'] == 'failed')
    }

async def bomb_threat_agent(event: dict) -> dict:
    event_id = event.get('event_id')
    print(f"[Agent] Processing Bomb Threat: {event_id}")

    # 1. Parsing Input
    try:
        airport_code = event.get('airport_code')
        # Handle cases where airport code might be a list or nested in json
        if not airport_code:
            raw_json = event.get('event_json', {})
            if isinstance(raw_json, str):
                raw_json = json.loads(raw_json)
            airport_code = raw_json.get('airport_code')
        
        if isinstance(airport_code, list):
            airport_code = airport_code[0]
            
        start_time = event.get('start_time', '')
        date_str = start_time.split(' ')[0] if start_time else None

        if not airport_code:
            return {"status": "error", "error": "Missing airport_code"}

        print(f"[Agent] Location: {airport_code} | Date: {date_str or 'All'}")

        # 2. Gathering Context (Parallel Fetch)
        tasks = [
            get_flights.ainvoke({}),
            get_airport.ainvoke({}),
            get_passenger_booking.ainvoke({}),
            get_crew_assignment.ainvoke({})
        ]
        flights, airports, bookings, crew = await asyncio.gather(*tasks)
        
        # 3. Filtering Data
        # We need to split flights into arriving (reroute) vs departing (cancel)
        arriving = [f for f in flights if f.get('destination_airport') == airport_code]
        departing = [f for f in flights if f.get('origin_airport') == airport_code]

        if date_str:
            arriving = [f for f in arriving if str(f.get('scheduled_arrival')).startswith(date_str)]
            departing = [f for f in departing if str(f.get('scheduled_departure')).startswith(date_str)]

        flight_ids_arr = {f.get('flight_id') for f in arriving}
        flight_ids_dep = {f.get('flight_id') for f in departing}
        all_ids = flight_ids_arr | flight_ids_dep

        affected_pax_arr = [b for b in bookings if b.get('flight_id') in flight_ids_arr]
        affected_pax_dep = [b for b in bookings if b.get('flight_id') in flight_ids_dep]
        affected_crew = [c for c in crew if c.get('flight_id') in all_ids]

        # 4. LLM Analysis
        system_prompt = """You are a Bomb Threat Response Agent for an airline operations center.
Your job is to analyze a bomb threat event and determine the appropriate response actions.

For a bomb threat at an airport:
- ARRIVING flights (destination = threat airport) → REROUTE to nearby airport (same flight, different landing)
- DEPARTING flights (origin = threat airport) → CANCEL and issue refund voucher

You will receive:
1. The bomb threat event details
2. ARRIVING flights that need rerouting
3. DEPARTING flights that need cancellation
4. All airport data for rerouting options
5. Passenger bookings for affected flights
6. Crew assignments for affected flights

Analyze the data and provide a response in this EXACT JSON format:
{
    "status": "completed",
    "affected_airport": "<airport code>",
    "threat_level": "CRITICAL",
    "reroute_destination": "<nearby airport for arriving flights>",
    "summary": {
        "arriving_flights": <count>,
        "departing_flights": <count>,
        "passengers_rerouted": <count on arriving flights>,
        "passengers_cancelled": <count on departing flights>,
        "crew_affected": <count>
    },
    "actions": [
        "Reroute <N> arriving flights to <airport>",
        "Cancel <N> departing flights",
        "Issue refund vouchers to <N> passengers",
        "Mark <N> bookings as disrupted",
        "Update <N> crew assignments to Standby"
    ],
    "reroute_options": ["<airport1>", "<airport2>", "<airport3>"]
}

IMPORTANT:
- Count the actual flights, passengers, and crew from the data provided
- Select the BEST nearby airport for rerouting based on proximity/region
- Return ONLY valid JSON, no extra text"""

        user_prompt = f"""
BOMB THREAT EVENT:
{json.dumps(event, indent=2)}

ARRIVING FLIGHTS (destination = {airport_code}) - TO BE REROUTED ({len(arriving)} flights):
{json.dumps(arriving, indent=2)}

DEPARTING FLIGHTS (origin = {airport_code}) - TO BE CANCELLED ({len(departing)} flights):
{json.dumps(departing, indent=2)}

PASSENGERS ON ARRIVING FLIGHTS ({len(affected_pax_arr)} bookings):
{json.dumps(affected_pax_arr, indent=2)}

PASSENGERS ON DEPARTING FLIGHTS ({len(affected_pax_dep)} bookings):
{json.dumps(affected_pax_dep, indent=2)}

ALL AIRPORTS (for rerouting options):
{json.dumps(airports, indent=2)}

CREW ASSIGNMENTS ({len(affected_crew)}):
{json.dumps(affected_crew, indent=2)}
"""

        print("[Agent] Consulting LLM...")
        llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)
        response_msg = await llm.ainvoke([
            SystemMessage(content=system_prompt),
            HumanMessage(content=user_prompt)
        ])
        
        # Clean response
        raw_text = response_msg.content
        if "```json" in raw_text:
            cleaned = raw_text.split("```json")[1].split("```")[0].strip()
        elif "```" in raw_text:
            cleaned = raw_text.split("```")[1].split("```")[0].strip()
        else:
            cleaned = raw_text
            
        try:
            decision = json.loads(cleaned)
        except:
            print("[Agent] Failed to parse JSON, returning raw output")
            return {"status": "error", "raw": raw_text}

        # 5. Execution
        dest = decision.get('reroute_destination')
        if dest:
            print(f"[Agent] Executing DB Updates -> Reroute: {dest}")
            await generate_bomb_threat_query(airport_code, dest, start_time or 'NOW()')
            
            print("[Agent] sending notifications...")
            stats = await notify_bomb_threat_passengers()
            decision['notifications'] = stats
        else:
            print("[Agent] No reroute destination provided - skipping DB updates.")

        return decision

    except Exception as e:
        print(f"[Agent] Critical Error: {e}")
        import traceback; traceback.print_exc()
        return {"status": "error", "error": str(e)}
