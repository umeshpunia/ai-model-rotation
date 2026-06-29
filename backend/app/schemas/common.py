"""Shared schema primitives: base config, pagination, and generic responses."""
from typing import Generic, TypeVar

from pydantic import BaseModel, ConfigDict, Field

from app.core.constants import DEFAULT_PAGE_SIZE, MAX_PAGE_SIZE

T = TypeVar("T")


class SchemaBase(BaseModel):
    """Base for request DTOs (strict-ish, forbids unknown fields)."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)


class ORMSchema(BaseModel):
    """Base for response DTOs read from ORM entities."""

    model_config = ConfigDict(from_attributes=True)


class PaginationParams(BaseModel):
    """Query parameters controlling pagination."""

    page: int = Field(default=1, ge=1, description="1-based page number.")
    page_size: int = Field(
        default=DEFAULT_PAGE_SIZE,
        ge=1,
        le=MAX_PAGE_SIZE,
        description="Number of items per page.",
    )

    @property
    def offset(self) -> int:
        """Zero-based row offset for the current page."""
        return (self.page - 1) * self.page_size

    @property
    def limit(self) -> int:
        """Row limit for the current page."""
        return self.page_size


class Page(ORMSchema, Generic[T]):
    """A paginated envelope around a list of items."""

    items: list[T]
    total: int = Field(description="Total number of matching rows.")
    page: int = Field(description="Current 1-based page number.")
    page_size: int = Field(description="Items per page.")
    pages: int = Field(description="Total number of pages.")

    @classmethod
    def create(cls, items: list[T], total: int, params: PaginationParams) -> "Page[T]":
        """Build a page envelope from items, total count, and pagination params."""
        pages = (total + params.page_size - 1) // params.page_size if params.page_size else 0
        return cls(
            items=items,
            total=total,
            page=params.page,
            page_size=params.page_size,
            pages=pages,
        )


class MessageResponse(BaseModel):
    """Generic success/acknowledgement response."""

    message: str
    success: bool = True


class ErrorResponse(BaseModel):
    """Standard error response body (mirrors ``AppError.to_dict``)."""

    code: str
    message: str
    details: object | None = None
