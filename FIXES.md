# FIXES.md — Event Log API Review Fixes

This file records fixes made during the time-boxed security + correctness review.
Entries are ordered by severity.

Agent config: `CODEX.md` (repo map, constraints, severity rules, test strategy).

**Note on starting state:** this repository started as a starter implementation: only
`POST /events` and `GET /events/{event_id}` existed. Accordingly, the Critical item
below covers implementing the missing spec endpoints.

## [Critical] Implement spec endpoints (`GET /events`, `DELETE /events/{event_id}`, `GET /stats`)
- Anchors:
  - `app/routes/events.py` :: `_build_event_filters()`
  - `app/routes/events.py` :: `list_events()`
  - `app/routes/events.py` :: `delete_event()`
  - `app/routes/events.py` :: `get_stats()`
- Before → After:
  - Before: `GET /events` returned **405** (the `/events` route existed only for POST).  
    After: returns **200** and supports combinable filters (`category`, `user_id`, `start`, `end`) and sorting by `timestamp DESC, id DESC`.
  - Before: `DELETE /events/{event_id}` returned **405** (only GET existed).  
    After: returns **204** with an empty body; missing id returns standardized **404** (`not_found`).
  - Before: `GET /stats` returned **404** (route did not exist).  
    After: returns **200** with filtered stats; `first_event`/`last_event` are **timestamp strings** (UTC) or `null` when empty.
- Implementation notes:
  - Centralized validation + WHERE/params building to keep `GET /events` and `GET /stats` consistent:
    - category validated via allowlist (`validate_category`)
    - timestamps parsed/normalized to UTC via `parse_timestamp`
    - inclusive bounds; `start > end` returns standardized `invalid_input` (400)
  - SQL safety: all user values are bound parameters; the only SQL concatenation is constant fragments (no user-supplied SQL).
  - Stats correctness: the identical `WHERE` clause + params are applied to **all** stats subqueries (`total_events`, `events_by_category`, `unique_users`, `first_event`, `last_event`).
- Tests added:
  - `tests/test_events.py` :: `TestListEvents`
  - `tests/test_events.py` :: `TestDeleteEvent`
  - `tests/test_events.py` :: `TestStats`

## [High] Accept ISO 8601 `Z` timestamps and normalize to UTC
- Anchor: `app/utils.py` :: `parse_timestamp()`
- Before → After:
  - Before: `2026-03-01T12:00:00Z` was rejected as an invalid ISO timestamp.
  - After: accepted and normalized to `2026-03-01T12:00:00+00:00`.
- Why this fix is needed:
  - The assignment spec expects ISO 8601 timestamps; `Z` is a common valid form and `datetime.fromisoformat()` does not accept it.
- Tests added:
  - `tests/test_events.py` :: `TestCreateEvent.test_create_event_timestamp_z_normalized_to_utc`

## [High] Standardize request validation errors (422) to the repo error format
- Anchor: `app/main.py` :: `request_validation_exception_handler()`
- Justification:
  - `app/errors.py` documents a single standardized error shape and warns against default FastAPI error payloads.
- Before → After:
  - Before: validation errors returned FastAPI default `{"detail": ...}`.
  - After: validation errors return `{ "error": { "code": "invalid_input", "message": ... } }` with **HTTP 422 preserved**.
- Error code choice:
  - Used `invalid_input` to avoid expanding the API’s error-code surface area for what is still “invalid input”.
- Tests added:
  - `tests/test_events.py` :: `TestCreateEvent.test_create_event_invalid_category`
  - `tests/test_events.py` :: `TestCreateEvent.test_create_event_missing_payload`
  - `tests/test_events.py` :: `TestGetEvent.test_get_event_invalid_id_returns_standard_error`

## [Medium] Read `DATABASE_PATH` from the environment on each connection
- Anchors:
  - `app/database.py` :: `_database_path()`
  - `app/database.py` :: `get_db()`
- Before → After:
  - Before: DB path resolved once at import time; env changes after import had no effect.
  - After: `get_db()` resolves the DB path at call time.
- Tests added:
  - `tests/test_database.py` :: `test_get_db_reads_database_path_env_var_each_call`

## Additional review notes (not required / not implemented)
- Pagination (`limit`/`offset`) for `GET /events` to avoid unbounded responses.
- Request payload size limits (app-level or server-level) for abuse resistance.
- Indexes on `timestamp`, `category`, `user_id` for larger datasets.
- SQLite concurrency considerations (WAL helps; still worth documenting if productionized).

## Identified but not fixed
- None.
