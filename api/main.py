from fastapi import FastAPI
from api.airline_service import get_routes

app = FastAPI(
    title="Airline Agent API",
    description="API to access airline data from Azure Postgres",
)


@app.get("/")
def read_root():
    return {"message": "Welcome to the Airline Agent API"}


# Include the routers
app.include_router(get_routes.router)
