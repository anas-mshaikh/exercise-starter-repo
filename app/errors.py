"""
Standardized error responses.

All error responses in this application use the format:

    {
        "error": {
            "code": "error_code_here",
            "message": "Human-readable description"
        }
    }

Use the helper functions in this module to return errors.
Do NOT use FastAPI's default HTTPException — it produces a different
response format ({"detail": "..."}) that is inconsistent with our API.
"""

from fastapi.responses import JSONResponse


def error_response(status_code: int, code: str, message: str) -> JSONResponse:
    """
    Return a standardized error response.
    
    Args:
        status_code: HTTP status code (e.g., 400, 404)
        code: Machine-readable error code (e.g., "not_found", "invalid_input")
        message: Human-readable error description
    """
    return JSONResponse(
        status_code=status_code,
        content={
            "error": {
                "code": code,
                "message": message,
            }
        },
    )


def not_found(resource: str, resource_id) -> JSONResponse:
    """Return a 404 error for a missing resource."""
    return error_response(404, "not_found", f"{resource} with id '{resource_id}' not found")


def invalid_input(message: str) -> JSONResponse:
    """Return a 400 error for invalid input."""
    return error_response(400, "invalid_input", message)
