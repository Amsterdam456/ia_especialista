from datetime import datetime

from sqlalchemy import Boolean, DateTime, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base_class import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    email: Mapped[str] = mapped_column(String, unique=True, index=True, nullable=False)
    full_name: Mapped[str | None] = mapped_column(String, nullable=True)
    hashed_password: Mapped[str] = mapped_column(String, nullable=False)
    is_admin: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    chats: Mapped[list["Chat"]] = relationship("Chat", back_populates="owner", cascade="all, delete-orphan")
    feedbacks: Mapped[list["ChatFeedback"]] = relationship("ChatFeedback", back_populates="user")
    audits: Mapped[list["ActionAudit"]] = relationship("ActionAudit", back_populates="user")
    policies: Mapped[list["PolicyFile"]] = relationship("PolicyFile", back_populates="user")
