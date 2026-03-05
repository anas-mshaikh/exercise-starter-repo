"""
Event routes.

Existing endpoints:
    POST /events       - Create a new event
    GET  /events/{id}  - Retrieve a single event
    GET  /events       - List events with optional filters
    DELETE /events/{id} - Delete an event
    GET  /stats        - Event statistics with optional filters
"""

import json
from typing import Any, Optional

from fastapi import APIRouter, Response

from app.database import get_db
from app.models import EventCreate, EventResponse
from app.errors import not_found, invalid_input
from app.utils import now_utc, parse_timestamp, validate_category

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


def _build_event_filters(
    *,
    category: Optional[str] = None,
    user_id: Optional[str] = None,
    start: Optional[str] = None,
    end: Optional[str] = None,
) -> tuple[str, list[Any]]:
    where_clauses: list[str] = []
    params: list[Any] = []

    start_dt = None
    end_dt = None

    if category is not None:
        validate_category(category)
        where_clauses.append("category = ?")
        params.append(category)

    if user_id is not None:
        where_clauses.append("user_id = ?")
        params.append(user_id)

    if start is not None:
        start_dt = parse_timestamp(start)
        where_clauses.append("timestamp >= ?")
        params.append(start_dt.isoformat())

    if end is not None:
        end_dt = parse_timestamp(end)
        where_clauses.append("timestamp <= ?")
        params.append(end_dt.isoformat())

    if start_dt is not None and end_dt is not None and start_dt > end_dt:
        raise ValueError("Start timestamp must be <= end timestamp")

    where_sql = f" WHERE {' AND '.join(where_clauses)}" if where_clauses else ""
    return where_sql, params


@router.get("/events")
def list_events(
    category: Optional[str] = None,
    user_id: Optional[str] = None,
    start: Optional[str] = None,
    end: Optional[str] = None,
):
    """List events with optional filters."""
    try:
        where_sql, params = _build_event_filters(
            category=category,
            user_id=user_id,
            start=start,
            end=end,
        )
    except ValueError as e:
        return invalid_input(str(e))

    db = get_db()
    try:
        rows = db.execute(
            f"SELECT * FROM events{where_sql} ORDER BY timestamp DESC, id DESC",
            params,
        ).fetchall()
        return [_row_to_event(row) for row in rows]
    finally:
        db.close()


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


@router.delete("/events/{event_id}", status_code=204)
def delete_event(event_id: int):
    """Delete an event by ID."""
    db = get_db()
    try:
        cursor = db.execute("DELETE FROM events WHERE id = ?", (event_id,))
        db.commit()
        if cursor.rowcount == 0:
            return not_found("Event", event_id)
        return Response(status_code=204)
    finally:
        db.close()


@router.get("/stats")
def get_stats(
    category: Optional[str] = None,
    user_id: Optional[str] = None,
    start: Optional[str] = None,
    end: Optional[str] = None,
):
    """Get event statistics with optional filters."""
    try:
        where_sql, params = _build_event_filters(
            category=category,
            user_id=user_id,
            start=start,
            end=end,
        )
    except ValueError as e:
        return invalid_input(str(e))

    db = get_db()
    try:
        total_events = db.execute(
            f"SELECT COUNT(*) AS count FROM events{where_sql}",
            params,
        ).fetchone()["count"]

        by_category_rows = db.execute(
            f"SELECT category, COUNT(*) AS count FROM events{where_sql} GROUP BY category",
            params,
        ).fetchall()
        events_by_category = {row["category"]: row["count"] for row in by_category_rows}

        unique_users = db.execute(
            f"SELECT COUNT(DISTINCT user_id) AS count FROM events{where_sql}",
            params,
        ).fetchone()["count"]

        first_row = db.execute(
            f"SELECT * FROM events{where_sql} ORDER BY timestamp ASC, id ASC LIMIT 1",
            params,
        ).fetchone()
        last_row = db.execute(
            f"SELECT * FROM events{where_sql} ORDER BY timestamp DESC, id DESC LIMIT 1",
            params,
        ).fetchone()

        return {
            "total_events": total_events,
            "events_by_category": events_by_category,
            "unique_users": unique_users,
            "first_event": first_row["timestamp"] if first_row is not None else None,
            "last_event": last_row["timestamp"] if last_row is not None else None,
        }
    finally:
        db.close()
