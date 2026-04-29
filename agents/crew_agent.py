"""
Crew Disruption Agent - LangChain ReAct Implementation
"""

import json
from dotenv import load_dotenv

from langchain_openai import ChatOpenAI
from langchain.agents import AgentExecutor, create_react_agent
from langchain_core.prompts import PromptTemplate

from tools.tools import (
    get_flights,
    get_crew,
    get_crew_assignment,
    get_crew_duty_time,
    get_disruption,
)

load_dotenv()

TOOLS = [get_flights, get_crew, get_crew_assignment, get_crew_duty_time, get_disruption]

AGENT_PROMPT = PromptTemplate.from_template(
    """
You are a Crew Disruption Resolution Agent for an airline operations center.

You handle crew-related disruptions such as:
- Crew duty time exceeded
- Crew unavailable
- Crew legality or rest issues

You MUST:
1. Use get_disruption to understand the crew issue
2. Use get_flights to identify the affected flight
3. Use get_crew_assignment to find currently assigned crew
4. Use get_crew_duty_time to verify legality
5. Use get_crew to find available replacement crew

Decision rules:
- If legal replacement crew exists → assign_crew
- If no crew and departure < 8 hours → reschedule
- If no crew and departure 8–24 hours → reschedule_and_hotel
- If no crew and departure > 24 hours → cancel_and_voucher

Return ONLY valid JSON.

You have access to the following tools:
{tools}

Tool names:
{tool_names}

Use the following format:
Thought: analyze crew disruption
Action: <tool name>
Action Input: <tool input>
Observation: <tool output>
...
Thought: I have enough information
Final Answer: <JSON>

Begin!

Event:
{input}
{agent_scratchpad}
"""
)


# -----------------------
# Agent factory
# -----------------------
def create_crew_agent():
    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)

    agent = create_react_agent(llm=llm, tools=TOOLS, prompt=AGENT_PROMPT)

    return AgentExecutor(
        agent=agent,
        tools=TOOLS,
        verbose=False,  # 🔴 important
        handle_parsing_errors=True,
        max_iterations=8,
        return_intermediate_steps=False,
    )


# -----------------------
# Main entrypoint
# -----------------------
async def crew_agent(event: dict) -> dict:
    print(f"[crew_agent] Handling event: {event.get('event_id')}")

    try:
        agent_executor = create_crew_agent()

        event_input = json.dumps(event or {}, indent=2)

        # 🔴 Guard: ainvoke MUST return something
        result = await agent_executor.ainvoke({"input": event_input})

        if not result or "output" not in result:
            return {
                "status": "error",
                "event_id": event.get("event_id"),
                "error": "agent returned empty result",
            }

        output = result.get("output") or "{}"

        try:
            response = json.loads(output)
        except Exception:
            response = {
                "status": "completed",
                "event_id": event.get("event_id"),
                "raw_response": output,
            }

        print(f"[crew_agent] Completed")
        return response

    except Exception as e:
        print(f"[crew_agent] Error:", repr(e))
        return {"status": "error", "event_id": event.get("event_id"), "error": str(e)}
