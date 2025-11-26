from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, EmailStr


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UserBase(BaseModel):
    email: EmailStr
    full_name: Optional[str] = None


class UserCreate(UserBase):
    password: str


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class UserOut(UserBase):
    id: int
    is_admin: bool
    created_at: datetime

    class Config:
        orm_mode = True


class MessageOut(BaseModel):
    id: int
    role: str
    content: str
    created_at: datetime

    class Config:
        orm_mode = True


class ChatCreate(BaseModel):
    title: Optional[str] = None


class ChatOut(BaseModel):
    id: int
    title: str
    created_at: datetime
    messages: List[MessageOut] = []

    class Config:
        orm_mode = True


class AskPayload(BaseModel):
    question: str
