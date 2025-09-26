"""
Base SQLModel classes and common functionality.
"""
from datetime import datetime, timezone
from typing import Optional
from sqlmodel import Field, SQLModel


class TimestampedBase(SQLModel):
    """Base class for models that need timestamp tracking."""
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="When the record was created"
    )
    updated_at: Optional[datetime] = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="When the record was last updated"
    )


class BaseResponse(SQLModel):
    """Base response model for API responses."""
    success: bool = True
    message: Optional[str] = None


class PaginationParams(SQLModel):
    """Standard pagination parameters."""
    page: int = Field(default=1, ge=1, description="Page number (1-based)")
    size: int = Field(default=50, ge=1, le=1000, description="Page size")


class PaginatedResponse(BaseResponse):
    """Paginated response wrapper."""
    page: int
    size: int
    total: int
    pages: int
    has_next: bool
    has_prev: bool