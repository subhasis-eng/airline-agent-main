from typing import List, Dict
import PyPDF2
import os
import json
import openai
import math
import time
from dotenv import load_dotenv
from concurrent.futures import ThreadPoolExecutor
import asyncio
from openai import OpenAI
from datetime import datetime
from langsmith import traceable

load_dotenv()
client = OpenAI()

openai.api_key = os.getenv("OPENAI_API_KEY")
today_str = datetime.now().strftime("%Y-%m-%d")


# --------------- PDF extraction ---------------
def extract_text_from_pdf(file_obj) -> str:
    """
    Accepts a file-like object (opened in binary) and returns extracted text.
    """
    reader = PyPDF2.PdfReader(file_obj)
    text = ""
    for page in reader.pages:
        try:
            page_text = page.extract_text()
        except Exception:
            page_text = ""
        if page_text:
            text += page_text + "\n"
    return text.strip()


# --------------- helper to call OpenAI safely ---------------
@traceable(name="get_agent_details")
def _call_openai(prompt: str, max_tokens: int = 1000) -> str:
    # synchronous call; we'll call via to_thread from async code if needed
    response = client.chat.completions.create(
        model="gpt-4",
        messages=[
            {
                "role": "system",
                "content": "You are an intelligent IRROPS Event Extractor. Return only valid JSON.",
            },
            {"role": "user", "content": prompt},
        ],
        temperature=0,
        max_tokens=max_tokens,
    )
    return response.choices[0].message.content.strip()


# --------------- parse chunk ---------------
def _repair_and_load_json(raw_output: str):
    """
    Try to safely fix common truncation issues and parse JSON.
    """
    try:
        return json.loads(raw_output)
    except json.JSONDecodeError:
        # attempt simple repairs: close unmatched brackets/quotes
        repaired = raw_output
        # close arrays/objects
        open_sq = repaired.count("[") - repaired.count("]")
        if open_sq > 0:
            repaired += "]" * open_sq
        open_br = repaired.count("{") - repaired.count("}")
        if open_br > 0:
            repaired += "}" * open_br
        # If still broken, try to trim to last complete array/object
        try:
            return json.loads(repaired)
        except Exception:
            # As a last resort, try to find the first '[' and last ']' and substring
            start = repaired.find("[")
            end = repaired.rfind("]")
            if start != -1 and end != -1 and end > start:
                try:
                    return json.loads(repaired[start : end + 1])
                except Exception:
                    pass
            raise


def parse_event_chunk(text_chunk: str) -> List[Dict]:
    """
    Build prompt and call OpenAI synchronously; return parsed list of events.
    """
    system_instructions = """
    Return ONLY a valid JSON array of event objects. No explanations, no extra text.

    Event fields:
    - event_id (string)
    - event_type (array of types: Weather, Threat, Crew, Traffic, MechanicalFailure, Other)
    - severity (array of: Low, Medium, High, Critical)
    - impact_description (array of short strings)
    - airport_code (array of IATA codes)
    - start_time (YYYY-MM-DD HH:MM)
    - end_time (YYYY-MM-DD HH:MM)
    - actions (array of suggested action strings)

    TIME EXTRACTION RULES:
    - If the text contains phrases like:
      • "between X – Y"
      • "from X to Y"
      • "expected between X and Y"
      • "from X onwards" → use X as start_time, leave end_time as empty string ""
      • "until Y" → set end_time as Y
    - If date is not mentioned, assume TODAY’s date: {today_str}.
    - Preserve the local time exactly as written.
    - Both start_time and end_time MUST be populated or empty string "".
    - NEVER use the word "Unknown".

    OTHER RULES:
    - airport_code must be valid IATA codes.
    - severity must reflect wording (e.g., "low-visibility" → Medium or High depending on context).
    - impact_description must be short factual phrases.
    - actions must be realistic airline operational actions.
    - Ensure perfectly valid JSON (double quotes, no trailing commas).
    """

    user_prompt = f"{system_instructions}\n\nPDF_CHUNK:\n{text_chunk}"
    raw_output = _call_openai(user_prompt, max_tokens=1200)
    events = _repair_and_load_json(raw_output)
    # Basic post-processing to ensure types
    for ev in events:
        ev.setdefault("event_id", str(ev.get("event_id", "")))
        # ensure lists
        for k in (
            "event_type",
            "severity",
            "impact_description",
            "airport_code",
            "actions",
        ):
            if k in ev and not isinstance(ev[k], list):
                ev[k] = [ev[k]]
    return events


async def parse_event_data(full_text: str, chunk_size: int = 3000) -> List[Dict]:
    """
    Split full_text into chunks of ~chunk_size characters and parse each chunk.
    This function is async but calls blocking OpenAI in a thread to avoid blocking event loop.
    """
    if not full_text:
        return []

    # split into approximate chunks by paragraphs
    paragraphs = [p for p in full_text.split("\n\n") if p.strip()]
    chunks = []
    cur = ""
    for p in paragraphs:
        if len(cur) + len(p) + 2 > chunk_size:
            chunks.append(cur)
            cur = p
        else:
            cur = (cur + "\n\n" + p).strip()
    if cur:
        chunks.append(cur)

    loop = asyncio.get_event_loop()
    results = []
    with ThreadPoolExecutor(max_workers=2) as exe:
        tasks = [
            loop.run_in_executor(exe, parse_event_chunk, chunk) for chunk in chunks
        ]
        completed = await asyncio.gather(*tasks)
        for evs in completed:
            results.extend(evs)
    return results
