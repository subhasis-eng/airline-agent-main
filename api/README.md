# Airline Agent API

This is a FastAPI service that connects to the Azure PostgreSQL database to provide data for the Airline Disruption Agent.

## 📂 Project Structure

- **`main.py`**: The entry point of the API. Initializes the app and includes routers.
- **`routers/`**: Contains the API route definitions.
  - **`get_routes.py`**: All `GET` endpoints (e.g., fetching aircraft, passengers).
- **`models.py`**: SQLAlchemy definitions matching the Azure DB tables.
- **`schemas.py`**: Pydantic models for data validation.
- **`database.py`**: Postgres connection logic (handles SSL & credentials).

## 🚀 How to Run

1.  **Navigate to this folder:**
    ```bash
    cd api
    ```

2.  **Activate Virtual Environment (if not active):**
    ```bash
    venv\Scripts\Activate
    ```

3.  **Install Dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

4.  **Start the Server:**
    ```bash
    uvicorn main:app --reload --host 0.0.0.0 --port 8000
    ```

4.  **View Documentation:**
    - Open [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs) to see all available endpoints.

## 🔑 Environment Variables

Make sure your `.env` file contains:
```ini
POSTGRES_USER=...
POSTGRES_PASSWORD=...
POSTGRES_HOST=...
POSTGRES_PORT=5432
POSTGRES_DB=...
POSTGRES_SSLMODE=require
```

## 🛠️ Adding New Endpoints

- To add a **new data retrieval** endpoint: Open `routers/get_routes.py`.
