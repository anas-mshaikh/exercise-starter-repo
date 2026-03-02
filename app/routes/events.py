"""
Event routes.

Existing endpoints:
    POST /events       - Create a new event
    GET  /events/{id}  - Retrieve a single event

TODO: The following endpoints need to be implemented:
    GET    /events     - List events with optional filters
    DELETE /events/{id} - Delete an event
    GET    /stats      - Event statistics with optional filters
"""

import json
from fastapi import APIRouter

from app.database import get_db
from app.models import EventCreate, EventResponse
from app.errors import not_found, invalid_input
from app.utils import now_utc, parse_timestamp

router = APIRouter()


def _row_to_event(row) -> dict:
    """Convert a database row to an EventResponse-compatible dict."""
    return {
        "id": row["id"],
        "category": row["category"],
        "payload": json.loads(row["payload"]),
        "user_id": row["user_id"],
        "timestamp": row["timestamp"],
    }


@router.post("/events", status_code=201)
def create_event(event: EventCreate):
    """Create a new event."""
    # Use provided timestamp or default to now, always normalized to UTC
    if event.timestamp:
        try:
            parsed = parse_timestamp(event.timestamp)
            ts = parsed.isoformat()
        except ValueError as e:
            return invalid_input(str(e))
    else:
        ts = now_utc()

    db = get_db()
    try:
        cursor = db.execute(
            "INSERT INTO events (category, payload, user_id, timestamp) VALUES (?, ?, ?, ?)",
            (event.category, json.dumps(event.payload), event.user_id, ts),
        )
        db.commit()
        event_id = cursor.lastrowid

        row = db.execute("SELECT * FROM events WHERE id = ?", (event_id,)).fetchone()
        return _row_to_event(row)
    finally:
        db.close()


@router.get("/events/{event_id}")
def get_event(event_id: int):
    """Retrieve a single event by ID."""
    db = get_db()
    try:
        row = db.execute("SELECT * FROM events WHERE id = ?", (event_id,)).fetchone()
        if row is None:
            return not_found("Event", event_id)
        return _row_to_event(row)
    finally:
        db.close()
