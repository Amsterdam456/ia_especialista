from typing import Generic, TypeVar

from pydantic import BaseModel, ConfigDict

T = TypeVar("T")


class Envelope(BaseModel, Generic[T]):
    success: bool = True
    data: T | None = None
    error: str | None = None

    model_config = ConfigDict(arbitrary_types_allowed=True)


class StatusResponse(BaseModel):
    status: str = "ok"
