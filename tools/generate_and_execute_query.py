from langchain_openai import ChatOpenAI
from langchain.schema import HumanMessage, SystemMessage
import re
from database import get_pool


async def extract_sql(llm_output: str) -> list[str]:
    """
    Extract SQL code block(s) from LLM response and split into individual statements.
    Returns a list of SQL statements.
    """
    match = re.search(r"```sql(.*?)```", llm_output, re.S)
    if not match:
        raise ValueError("No SQL code block found in LLM output")

    sql_block = match.group(1).strip()
    statements = [s.strip() + ";" for s in sql_block.split(";") if s.strip()]
    return statements


async def execute_sql(statements: list[str]):
    """
    Execute multiple SQL statements step by step.
    """
    pool = await get_pool()
    async with pool.acquire() as conn:
        for i, stmt in enumerate(statements, start=1):
            try:
                async with conn.transaction():
                    await conn.execute(stmt)
                print(f"✅ Step {i} executed successfully")
            except Exception as e:
                print(f"❌ Step {i} failed:", e)


# -----------------------------
# SQL GENERATION (LLM ONLY)
# -----------------------------
async def generate_and_execute_query(llm, incidents):
    """
    incidents: list of dicts with keys:
      - airport_code
      - start_time
      - severity
    """

    incident_str = "\n".join(
        f"- Airport: {i['airport_code']}, Start: {i['start_time']}, Severity: {i['severity']}"
        for i in incidents
    )

    messages = [
        SystemMessage(
            content=(
                "You are a senior PostgreSQL expert for airline disruption management. "
                "You must generate production-ready SQL that correctly handles JSONB arrays."
            )
        ),
        HumanMessage(
            content=f"""
            You are generating SQL for a PRODUCTION PostgreSQL system.
    Incorrect SQL will break execution.

    Context:
    High-severity weather incidents detected in the last 6 hours:

    {incident_str}

    Your task:
    Reschedule passenger bookings impacted by HIGH severity incidents
    AND capture passenger email + reason for notification.

    -------------------------------------------------
    ABSOLUTE RULES (DO NOT VIOLATE)
    -------------------------------------------------
    1. Use ONLY PostgreSQL syntax.
    2. Use ONLY the public schema:
       - public.passenger_booking
       - public.passenger
       - public.flight
       - public.master_decision_table
       - public.rescheduled_bookings
    3. DO NOT invent or assume columns.
    4. master_decision_table MUST be joined using CROSS JOIN only.
    5. JSON fields MUST be handled using:
       - jsonb_array_elements_text(...)
    6. ALWAYS wrap OR conditions in parentheses before AND filters.
    7. NEVER cast booking_id unless explicitly required.
    8. Use mdt.created_at for “last 6 hours” filtering.
    9. Output ONLY SQL inside ONE ```sql``` code block.
    10. Statements MUST be executable step-by-step.

    -------------------------------------------------
    STEP 1: CREATE TABLE
    -------------------------------------------------
    Create table IF NOT EXISTS:

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
    STEP 2: INSERT DATA (STRICT LOGIC)
    -------------------------------------------------
    INSERT INTO public.rescheduled_bookings using:

    FROM public.passenger_booking pb
    JOIN public.passenger p
        ON pb.passenger_id = p.passenger_id
    JOIN public.flight f
        ON pb.flight_id = f.flight_id
    CROSS JOIN public.master_decision_table mdt
    CROSS JOIN LATERAL
        jsonb_array_elements_text(mdt.event_json->'airport_code')
        AS ac(airport_code)

    WHERE conditions MUST BE:

    (
        f.origin_airport = ac.airport_code
        OR f.destination_airport = ac.airport_code
    )
    AND EXISTS (
        SELECT 1
        FROM jsonb_array_elements_text(mdt.event_json->'severity') s
        WHERE s = 'High'
    )
    AND mdt.created_at >= NOW() - INTERVAL '6 hours'

    SELECT columns MUST BE:
    - pb.booking_id
    - f.flight_id
    - pb.passenger_id
    - p.first_name
    - p.email
    - ac.airport_code
    - mdt.reason
    - NOW() AS rescheduled_at

    -------------------------------------------------
    STEP 3: UPDATE BOOKINGS
    -------------------------------------------------
    UPDATE public.passenger_booking
    SET booking_status = 'RESCHEDULED'
    WHERE booking_id IN (
        SELECT booking_id FROM public.rescheduled_bookings
    )

    -------------------------------------------------
    FINAL OUTPUT RULES
    -------------------------------------------------
    - Do NOT explain anything
    - Do NOT add comments
    - Do NOT change column names or types
    - Do NOT remove parentheses
    - Do NOT use JOIN instead of CROSS JOIN for master_decision_table
    - Output SQL ONLY

            """
        ),
    ]
    result = await llm.ainvoke(messages)

    # print("\n================ GENERATED SQL ================\n")
    # print(result.content)
    # print("\n==============================================\n")

    sql_statements = await extract_sql(result.content)
    await execute_sql(sql_statements)
