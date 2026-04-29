from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Dict, List, Optional
import uuid

from langchain_core.messages import SystemMessage, HumanMessage

from irops_agent_v5 import build_agent, process_user_input, SYSTEM_PROMPT


app = FastAPI(title="IROPS Agent API", version="1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # tighten later if needed
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


print("🚀 Initializing IROPS Agent...")
agent = build_agent()
if not agent:
    raise RuntimeError("Failed to initialize IROPS agent")


SESSIONS: Dict[str, List] = {}


class ChatRequest(BaseModel):
    message: str
    session_id: str | None = None
    mode: str = "analysis"


class ChatResponse(BaseModel):
    session_id: Optional[str] = None
    reply: str



@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/chat", response_model=ChatResponse)
def chat(req: ChatRequest):

    if req.session_id and req.session_id in SESSIONS:
        history = SESSIONS[req.session_id]
        session_id = req.session_id
    else:
        history = []
        session_id = str(uuid.uuid4())
        SESSIONS[session_id] = history

    print("SESSION ID:", req.session_id)
    print("HISTORY LENGTH:", len(history))

    new_messages = process_user_input(
        agent=agent,
        history=history,
        user_text=req.message
    )

    history.clear()
    history.extend(new_messages)

    return ChatResponse(
        session_id=session_id,
        reply=history[-1].content
    )


@app.post("/analysis")
def analysis():
    return {
        "title": "IROPS Analysis",
        "sections": [
            {
                "type": "plan",
                "title": "Plan Breakdown",
                "items": [
                    "Identify disrupted flights",
                    "Check runway availability",
                    "Evaluate crew legality",
                    "Assess passenger impact",
                    "Recommend action"
                ]
            },
            {
                "type": "summary",
                "title": "Operational Summary",
                "text": "Crew shortage and runway constraints detected at BOM."
            }
        ]
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "api:app",
        host="localhost",
        port=8000,
        reload=True
    )
