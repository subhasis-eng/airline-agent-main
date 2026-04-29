import asyncio
from task_queue import TASK_QUEUE
from database import (
    fetch_pending_decisions,
    mark_decision_processing,
    mark_decision_processed,
)
from agents.weather_agent import weather_agent
from agents.monitoring import monitoring_agent
from agents.bomb_threat_agent import bomb_threat_agent
from agents.crew_agent import crew_agent
import json

AGENT_MAP = {
    "weather_agent": weather_agent,
    "crew_agent": crew_agent,
    "monitoring": monitoring_agent,
    "bomb_threat_agent": bomb_threat_agent,
}

POLL_INTERVAL = 3.0


async def decision_poller():
    while True:
        decisions = await fetch_pending_decisions()

        for decision in decisions:
            decision_id = decision["id"]
            await mark_decision_processing(decision_id)

            selected_agents = decision["selected_agents"]
            if isinstance(selected_agents, str):
                selected_agents = json.loads(selected_agents)

            event_data = decision["event_json"]
            if isinstance(event_data, str):
                event_data = json.loads(event_data)

            for agent in selected_agents:
                if agent not in AGENT_MAP:
                    print(
                        f"[decision_poller] unknown agent {agent} for decision {decision_id}"
                    )
                    continue

                await TASK_QUEUE.put((AGENT_MAP[agent], event_data))

            await mark_decision_processed(decision_id)

        await asyncio.sleep(POLL_INTERVAL)
