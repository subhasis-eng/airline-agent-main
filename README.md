# Airlines IRROPS - demo

## Prereqsites
- Python 3.10+
- OpenAI API key
- DB credentials

## Setup

1. Copy .env.example -> .env and set OPENAI_API_KEY and DB credentials

2. create venv and activate:
    python3 -m venv myenv
    source myenv/bin/activate

3. Install deps:
   pip3 install -r requirements.txt

4. Run FastAPI fo Agents:
   uvicorn app:app --reload --host 0.0.0.0 --port 8000

5. Run FastAPI fo API(POSTGRES TABLE):
    uvicorn api.main:app --reload --host 0.0.0.0 --port 8001

6. To Run ui
   cd ui/
   streamlit run main.py