from fastapi import Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.security import verify_password
from app.db.session import get_session
from app.models import User


def authenticate_user(email: str, password: str, db: Session = Depends(get_session)) -> User:
    user = db.query(User).filter(User.email == email).first()
    if not user or not verify_password(password, user.hashed_password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Credenciais invalidas")
    return user
