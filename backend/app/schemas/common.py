from typing import Generic, TypeVar
from uuid import UUID

from pydantic import BaseModel

T = TypeVar("T")


class PaginationParams(BaseModel):
    page: int = 1
    page_size: int = 20


class PaginatedResponse(BaseModel, Generic[T]):
    items: list[T]
    total: int
    page: int
    page_size: int
    pages: int


class ErrorResponse(BaseModel):
    detail: str
    code: str | None = None
    correlation_id: str | None = None


class MessageResponse(BaseModel):
    message: str


class IDResponse(BaseModel):
    id: UUID
    message: str | None = None
