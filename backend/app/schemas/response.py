# app/schemas/response.py
# Consistent API response envelope schemas for CampusHire.

from __future__ import annotations

from typing import Any, Generic, Optional, TypeVar
from pydantic import BaseModel

T = TypeVar("T")


class APIResponse(BaseModel, Generic[T]):
    """Standard success response envelope."""
    success: bool = True
    data: Optional[T] = None
    message: str = "Operation completed successfully."


class ErrorResponse(BaseModel):
    """Standard error response envelope."""
    success: bool = False
    message: str
    error_code: str = "GENERIC_ERROR"
