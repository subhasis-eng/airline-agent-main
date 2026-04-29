import time
import asyncio

# simple in-memory counters (replace with DB for persistence)
MONITOR_LOG = []


async def monitoring_agent(event):
    ts = time.time()
    MONITOR_LOG.append(
        {"event_id": event.get("event_id"), "ts": ts, "severity": event.get("severity")}
    )
    # example: print/log; in real use, write to DB or metrics system
    print(
        f"[monitoring_agent] logged event {event.get('event_id')} severity={event.get('severity')}"
    )
    # example metrics
    total = len(MONITOR_LOG)
    return {"status": "logged", "total_logged": total}
