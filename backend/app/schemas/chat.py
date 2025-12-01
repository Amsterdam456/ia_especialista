from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict


class ChatCreate(BaseModel):
    title: Optional[str] = "Novo Chat"


class ChatOut(BaseModel):
    id: int
    title: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
