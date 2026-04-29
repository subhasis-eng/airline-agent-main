from fastapi import FastAPI, UploadFile, File, HTTPException
import asyncio
from parser import extract_text_from_pdf, parse_event_data
from task_queue import TASK_QUEUE, task_worker
from agents.routing_ai import ai_decide_agent
from database import init_db, insert_master_decision, get_pool
from decision_worker import decision_poller
from agents.weather_agent import weather_agent
from agents.crew_agent import crew_agent
from agents.monitoring import monitoring_agent
from agents.bomb_threat_agent import bomb_threat_agent
from io import BytesIO
from dotenv import load_dotenv
import json
import os
import requests

url = "http://localhost:5000"

load_dotenv()

AGENT_MAP = {
    "weather_agent": weather_agent,
    "crew_agent": crew_agent,
    "monitoring": monitoring_agent,
    "bomb_threat_agent": bomb_threat_agent,
}

app = FastAPI()


@app.on_event("startup")
async def startup_event():
    # init DB (create table if not exists)
    await init_db()
    # start task worker
    asyncio.create_task(task_worker())
    # start decision poller
    asyncio.create_task(decision_poller())


async def enqueue_agents_for_decision(selected_agents, event_json):
    # Ensure monitoring always present
    if "monitoring" not in selected_agents:
        selected_agents.append("monitoring")
    for agent_name in selected_agents:
        agent_callable = AGENT_MAP.get(agent_name)
        if not agent_callable:
            print(f"[app] unknown agent {agent_name} - skipping")
            continue
        await TASK_QUEUE.put((agent_callable, event_json))


@app.post("/upload")
async def upload_pdf(file: UploadFile = File(...)):
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are accepted")

    pdf_bytes = await file.read()
    pdf_file = BytesIO(pdf_bytes)
    text = extract_text_from_pdf(pdf_file)

    events = await parse_event_data(text)

    if not events:
        return {"events": [], "message": "No events parsed"}

    routing_results = []
    for event in events:
        # Ask AI which agents should run for this event
        ai_result = await ai_decide_agent(
            event, db_rules=None
        )  # optionally pass db rules
        selected_agents = ai_result.get("selected_agents", ["monitoring"])
        reason = ai_result.get("reason", "")

        # Save decision to DB
        decision_row = await insert_master_decision(
            event_id=event.get("event_id")
            or str(event.get("impact_description", [""])[0])[:10],
            event_json=event,
            selected_agents=selected_agents,
            reason=reason,
        )
        if event["event_type"][0].lower() in ("weather", "bomb"):
            data = {
                "type": event["event_type"][0].lower(),
                "severity": event.get("severity"),
                "airport_code": event.get("airport_code"),
                "alternate_airport": None
            }

            DISRUPTION_API_URL = f"{url}/disruption/city"
            try:
                response = requests.post(
                    DISRUPTION_API_URL,
                    json=data,
                    timeout=5
                )
                print("Disruption API status:", response.status_code)
                try:
                    print("Disruption API response:", response.json())
                except ValueError:
                    print("Disruption API response (text):", response.text)

            except requests.exceptions.RequestException as e:
                print("Disruption API call failed:", str(e))


        # Immediately enqueue agents for low-latency response
        await enqueue_agents_for_decision(selected_agents, event)

        routing_results.append(
            {
                "event_id": event.get("event_id"),
                "decision_id": decision_row.get("id"),
                "selected_agents": selected_agents,
                "reason": reason,
            }
        )

    return {"events": events, "routing": routing_results}


def normalize_event(event: dict) -> dict:
    def first(val):
        return val[0] if isinstance(val, list) and val else val

    event["event_type"] = first(event.get("event_type"))
    event["severity"] = first(event.get("severity"))
    event["airport_code"] = first(event.get("airport_code"))
    return event
