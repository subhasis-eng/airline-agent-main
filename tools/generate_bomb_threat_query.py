import re
from langchain_openai import ChatOpenAI
from langchain.schema import HumanMessage, SystemMessage
from database import get_pool

async def execute_sql(statements: list[str]):
    """Execute raw SQL statements sequentially."""
    pool = await get_pool()
    async with pool.acquire() as conn:
        for idx, sql in enumerate(statements, 1):
            try:
                # print(f"Executing: {sql[:50]}...")
                async with conn.transaction():
                    await conn.execute(sql)
                print(f"✅ [DB] Step {idx} complete")
            except Exception as e:
                print(f"❌ [DB] Step {idx} failed: {e}")

async def generate_bomb_threat_query(airport_code: str, reroute_destination: str, event_time: str):
    print(f"[SQL] Generating queries for {airport_code} -> {reroute_destination}")
    
    # We use a strict prompt to ensure valid PGSQL is generated
    system_instruction = (
        "You are a senior PostgreSQL expert for airline bomb threat response. "
        "You must generate production-ready SQL that handles bomb threat scenarios."
    )
    
    user_context = f"""
You are generating SQL for a PRODUCTION PostgreSQL system.
Incorrect SQL will break execution.

Context:
BOMB THREAT detected at airport: {airport_code}
Event time: {event_time} (Extracted Date: {event_time.split(' ')[0]})
Reroute destination for arriving flights: {reroute_destination}

Your task:
Handle bomb threat by:
1. ARRIVING flights (destination = {airport_code} AND date = {event_time.split(' ')[0]}) → Reroute to {reroute_destination}
2. DEPARTING flights (origin = {airport_code} AND date = {event_time.split(' ')[0]}) → Cancel and issue refund voucher

-------------------------------------------------
ABSOLUTE RULES (DO NOT VIOLATE)
-------------------------------------------------
1. Use ONLY PostgreSQL syntax.
2. Use ONLY the public schema:
   - public.passenger_booking
   - public.passenger
   - public.flight
   - public.rescheduled_bookings
   - public.voucher
3. DO NOT invent or assume columns.
4. Output ONLY SQL inside ONE ```sql``` code block.
5. Statements MUST be executable step-by-step.
6. **CRITICAL:** Filter flights strictly by DATE of {event_time.split(' ')[0]}. Do NOT affect future dates.

-------------------------------------------------
STEP 1: CREATE TABLE IF NOT EXISTS rescheduled_bookings
-------------------------------------------------
public.rescheduled_bookings (
    booking_id VARCHAR,
    flight_id VARCHAR,
    passenger_id VARCHAR,
    passenger_name VARCHAR,
    passenger_email VARCHAR,
    airport_code VARCHAR,
    reason TEXT,
    rescheduled_at TIMESTAMP
)

-------------------------------------------------
STEP 2: INSERT ARRIVING FLIGHT PASSENGERS (REROUTED)
-------------------------------------------------
INSERT INTO public.rescheduled_bookings
SELECT pb.booking_id, f.flight_id, pb.passenger_id, 
       p.first_name AS passenger_name, p.email AS passenger_email,
       '{airport_code}' AS airport_code,
       'BOMB_THREAT - REROUTED TO {reroute_destination}' AS reason,
       NOW() AS rescheduled_at
FROM public.passenger_booking pb
JOIN public.flight f ON pb.flight_id = f.flight_id
JOIN public.passenger p ON pb.passenger_id = p.passenger_id
WHERE f.destination_airport = '{airport_code}'
  AND f.scheduled_arrival::date = '{event_time.split(' ')[0]}'::date
  AND f.status != 'Cancelled'
  AND f.status != 'Landed'

-------------------------------------------------
STEP 3: INSERT DEPARTING FLIGHT PASSENGERS (CANCELLED)
-------------------------------------------------
INSERT INTO public.rescheduled_bookings
SELECT pb.booking_id, f.flight_id, pb.passenger_id,
       p.first_name AS passenger_name, p.email AS passenger_email,
       '{airport_code}' AS airport_code,
       'BOMB_THREAT - CANCELLED' AS reason,
       NOW() AS rescheduled_at
FROM public.passenger_booking pb
JOIN public.flight f ON pb.flight_id = f.flight_id
JOIN public.passenger p ON pb.passenger_id = p.passenger_id
WHERE f.origin_airport = '{airport_code}'
  AND f.scheduled_departure::date = '{event_time.split(' ')[0]}'::date
  AND f.status != 'Cancelled'
  AND f.status != 'Landed'

-------------------------------------------------
STEP 4: UPDATE PASSENGER BOOKINGS - MARK AS DISRUPTED
-------------------------------------------------
UPDATE public.passenger_booking
SET is_disrupted = true
WHERE booking_id IN (
    SELECT booking_id FROM public.rescheduled_bookings
    WHERE reason LIKE 'BOMB_THREAT%'
    AND rescheduled_at >= NOW() - INTERVAL '1 hour'
)

-------------------------------------------------
STEP 5: UPDATE PASSENGER BOOKINGS - CANCEL DEPARTING
-------------------------------------------------
UPDATE public.passenger_booking
SET booking_status = 'Cancelled'
WHERE booking_id IN (
    SELECT booking_id FROM public.rescheduled_bookings
    WHERE reason = 'BOMB_THREAT - CANCELLED'
    AND rescheduled_at >= NOW() - INTERVAL '1 hour'
)

-------------------------------------------------
STEP 6: CANCEL DEPARTING FLIGHTS
-------------------------------------------------
UPDATE public.flight
SET status = 'Cancelled'
WHERE origin_airport = '{airport_code}'
  AND scheduled_departure::date = '{event_time.split(' ')[0]}'::date
  AND status != 'Cancelled'
  AND status != 'Landed'

-------------------------------------------------
STEP 7: INSERT REFUND VOUCHERS FOR CANCELLED PASSENGERS
-------------------------------------------------
INSERT INTO public.voucher (voucher_id, booking_id, voucher_type, expiry_date, status)
SELECT 
    'V-BT-' || pb.booking_id AS voucher_id,
    pb.booking_id,
    'Refund Voucher' AS voucher_type,
    NOW() + INTERVAL '1 year' AS expiry_date,
    'Issued' AS status
FROM public.passenger_booking pb
JOIN public.flight f ON pb.flight_id = f.flight_id
WHERE f.origin_airport = '{airport_code}'
  AND f.scheduled_departure::date = '{event_time.split(' ')[0]}'::date
  AND f.status = 'Cancelled'
  AND NOT EXISTS (
      SELECT 1 FROM public.voucher v 
      WHERE v.booking_id = pb.booking_id 
      AND v.voucher_type = 'Refund Voucher'
  )

-------------------------------------------------
FINAL OUTPUT RULES
-------------------------------------------------
- Do NOT explain anything
- Do NOT add comments
- Do NOT change column names or types
- Output SQL ONLY
"""

    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)
    
    response = await llm.ainvoke([
        SystemMessage(content=system_instruction),
        HumanMessage(content=user_context)
    ])
    
    content = response.content
    if "```sql" in content:
        sql_block = re.search(r"```sql(.*?)```", content, re.S).group(1)
    elif "```" in content:
        # Fallback if specific sql tag missing
        sql_block = re.search(r"```(.*?)```", content, re.S).group(1)
    else:
        sql_block = content

    # Clean up and split statements
    statements = [s.strip() + ";" for s in sql_block.split(";") if s.strip()]
    
    if statements:
        await execute_sql(statements)
    else:
        print("⚠️ No SQL statements generated")

