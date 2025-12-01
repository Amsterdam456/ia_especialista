from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, EmailStr


class UserAdminBase(BaseModel):
    email: EmailStr
    full_name: Optional[str] = None
    is_admin: bool = False
    is_active: bool = True

    model_config = ConfigDict(from_attributes=True)


class UserAdminCreate(BaseModel):
    email: EmailStr
    full_name: Optional[str] = None
    password: str
    role: str = "Usuario"


class UserAdminUpdate(BaseModel):
    full_name: Optional[str] = None
    role: Optional[str] = None
    is_active: Optional[bool] = None


class UserAdminOut(UserAdminBase):
    id: int
    created_at: datetime


class PolicyFileOut(BaseModel):
    id: int
    filename: str
    stored_path: str
    uploaded_by: int
    uploaded_at: datetime
    active: bool
    embedding_status: str
    embedding_last_error: str | None = None

    model_config = ConfigDict(from_attributes=True)


class PolicyUploadResponse(BaseModel):
    id: int
    filename: str
    status: str


class SystemConfigIn(BaseModel):
    system_prompt: Optional[str] = None
    model_name: Optional[str] = None
    temperature: Optional[float] = None
    top_p: Optional[float] = None


class SystemConfigOut(BaseModel):
    id: int
    system_prompt: Optional[str] = None
    model_name: str
    temperature: float
    top_p: float
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ActionAuditOut(BaseModel):
    id: int
    user_id: int
    action: str
    metadata: dict | None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ChatFeedbackOut(BaseModel):
    id: int
    user_id: int
    message_id: int
    rating: int
    comment: str | None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
