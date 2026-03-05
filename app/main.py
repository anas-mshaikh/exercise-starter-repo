"""
Event Log API — main application entry point.
"""

from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from app.database import init_db
from app.errors import error_response
from app.routes.events import router as events_router


@asynccontextmanager
async def lifespan(app):
    init_db()
    yield


app = FastAPI(
    title="Event Log API",
    description="A simple event logging and analytics API.",
    version="0.1.0",
    lifespan=lifespan,
)


@app.exception_handler(RequestValidationError)
async def request_validation_exception_handler(request: Request, exc: RequestValidationError):
    details: list[str] = []
    for err in exc.errors():
        loc = err.get("loc") or ()
        loc_str = ".".join(str(p) for p in loc)
        msg = err.get("msg", "Invalid request")
        if loc_str:
            details.append(f"{loc_str}: {msg}")
        else:
            details.append(msg)

    message = "Validation error"
    if details:
        message = f"{message}: {'; '.join(details)}"

    return error_response(422, "invalid_input", message)


app.include_router(events_router)
