"""
Event Log API — main application entry point.
"""

from fastapi import FastAPI
from app.database import init_db
from app.routes.events import router as events_router

app = FastAPI(
    title="Event Log API",
    description="A simple event logging and analytics API.",
    version="0.1.0",
)

app.include_router(events_router)


@app.on_event("startup")
def startup():
    init_db()
