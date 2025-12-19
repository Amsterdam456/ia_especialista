from datetime import datetime, timedelta

from fastapi import Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.security import normalize_email, verify_password
from app.db.session import get_session
from app.models import User


def authenticate_user(email: str, password: str, db: Session = Depends(get_session)) -> User:
    normalized = normalize_email(email)
    user = db.query(User).filter(User.email == normalized).first()
    now = datetime.utcnow()
    if user and user.locked_until and user.locked_until > now:
        raise HTTPException(
            status_code=status.HTTP_423_LOCKED,
            detail="Conta temporariamente bloqueada. Tente novamente mais tarde.",
        )
    if not user or not verify_password(password, user.hashed_password):
        if user:
            user.failed_login_count = (user.failed_login_count or 0) + 1
            user.last_failed_at = now
            if user.failed_login_count >= settings.LOGIN_MAX_ATTEMPTS:
                user.locked_until = now + timedelta(minutes=settings.LOGIN_LOCKOUT_MINUTES)
            db.add(user)
            db.commit()
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Credenciais invalidas")
    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Usuario inativo")

    if user.failed_login_count or user.locked_until or user.last_failed_at:
        user.failed_login_count = 0
        user.last_failed_at = None
        user.locked_until = None
        db.add(user)
        db.commit()
    return user
