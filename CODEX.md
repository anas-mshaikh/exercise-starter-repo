# CODEX.md — Agent Configuration for Event Log API Code Review

## Mission
Perform a focused, time-boxed review of this Event Log API. Identify and fix issues in priority order: **security → correctness/spec compliance → consistency → quality**. Keep changes minimal and consistent with existing project patterns.

## Non-negotiable Constraints
- **Do not rewrite** the project or change architecture.
- **Do not add infra** (no Docker/CI/new frameworks).
- Keep diffs small; prefer local helpers over new modules.
- All existing tests must keep passing; add new tests for every bug you fix.
- Follow the repo’s standardized error response format everywhere.

## Required Review Order
1. Read codebase + tests end-to-end before editing.
2. Confirm baseline: run test suite (`pytest -q`).
3. Identify & prioritize issues by severity.
4. Fix highest severity first.
5. Add tests that demonstrate each bug (red→green).
6. Document every fix in `FIXES.md` (severity ordered).

## Project Map
- FastAPI entrypoint: `app/main.py` (lifespan/init, router mounting, validation error handler)
- Routes: `app/routes/events.py`
- DB: `app/database.py` (SQLite)
- Errors: `app/errors.py` (standard error format)
- Models: `app/models.py` (Pydantic)
- Utils: `app/utils.py` (timestamps, categories)
- Tests: `tests/`

## Spec Requirements (Must Match Assignment)
### Endpoints
- `POST /events`
  - category required: one of `page_view`, `click`, `form_submit`, `purchase`, `error`
  - payload required (JSON)
  - user_id optional
  - timestamp optional; normalized to UTC
- `GET /events/{event_id}`
  - 404 uses standardized error format
- `GET /events`
  - filters optional + combinable: `category`, `user_id`, `start`, `end`
  - results sorted by timestamp **descending**
  - invalid timestamps return standardized error response
- `DELETE /events/{event_id}`
  - success: **204 No Content**
  - not found: 404 standardized error format
- `GET /stats`
  - same filters as `GET /events`
  - statistics reflect filters:
    - total_events
    - events_by_category
    - unique_users
    - first_event (timestamp string in UTC, or null)
    - last_event (timestamp string in UTC, or null)

## Security Rules
- **Never** build SQL queries using string interpolation with user input.
- Use parameterized queries (`?` placeholders / named params) for ALL filters.
- Validate category filters with allowlist.
- Validate and normalize timestamps consistently (prefer shared utils).

## Error Handling Rules
- Use the project’s `app/errors.py` helpers everywhere.
- Avoid mixing FastAPI default error payloads with custom error format:
  - Validation errors should be converted to the standardized `{error:{code,message}}` shape.
- Keep error payload shape consistent across endpoints.

## Timestamp Rules
- Treat incoming timestamps as ISO 8601 (accept `Z`).
- Normalize to UTC (timezone-aware).
- Use the shared parsing utility (do not duplicate parsing).
- Ensure filters use normalized timestamps for comparisons.

## Implementation Strategy
- Prefer a local helper function (inside `app/routes/events.py`) to build:
  - `WHERE` clauses
  - parameter lists
  - consistent validation for filters
- For each fix:
  1) Add a failing test first.
  2) Implement minimal code change.
  3) Run full test suite.
  4) Add an entry to `FIXES.md`.

## Test Additions to Prioritize
- SQL injection regression tests for list endpoints.
- Sorting by timestamp desc.
- Combined filters behavior.
- Timestamp edge cases (including `Z`).
- Stats reflect filters (especially `events_by_category`).
- Delete returns 204 + empty body.
- Stats empty result set does not crash.

## Commands
- Run tests: `pytest -q`
- Run a single test: `pytest -q tests/test_events.py::test_name`

## Output Expectations
When asked for “analysis”, produce:
- Architecture map
- Spec compliance matrix
- Prioritized issue list (Critical→Low)
- Test gap plan
- Proposed fix plan (red→green steps)

When asked to “implement”, keep changes small and ensure:
- All tests pass
- New tests cover the bug
- `FIXES.md` updated for each fix

## FIXES.md Format
For each fixed issue:
- What was wrong (file/function/line)
- Why it matters (security/correctness/consistency)
- What changed (brief)
- Severity: Critical/High/Medium/Low
- Tests added

Include “Identified but not fixed” at bottom if time runs out.
