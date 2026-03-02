"""
Pydantic models for request and response validation.
"""

from pydantic import BaseModel, field_validator
from typing import Any, Optional

from app.utils import VALID_CATEGORIES


class EventCreate(BaseModel):
    """Request body for creating an event."""

    category: str
    payload: dict[str, Any]
    user_id: Optional[str] = None
    timestamp: Optional[str] = None  # ISO 8601; defaults to now if not provided

    @field_validator("category")
    @classmethod
    def category_must_be_valid(cls, v):
        if v not in VALID_CATEGORIES:
            raise ValueError(
                f"Invalid category '{v}'. "
                f"Must be one of: {', '.join(sorted(VALID_CATEGORIES))}"
            )
        return v


class EventResponse(BaseModel):
    """Response body for a single event."""

    id: int
    category: str
    payload: dict[str, Any]
    user_id: Optional[str]
    timestamp: str
