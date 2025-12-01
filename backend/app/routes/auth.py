from datetime import timedelta

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.auth import authenticate_user
from app.core.config import settings
from app.core.security import create_access_token, get_current_user, get_password_hash
from app.db.session import get_session
from app.models import User
from app.schemas import AuthResponse, Envelope, Token, UserCreate, UserLogin, UserOut

router = APIRouter(prefix="/auth")


@router.post("/register", response_model=Envelope[UserOut])
def register(user_in: UserCreate, db: Session = Depends(get_session)):
    existing = db.query(User).filter(User.email == user_in.email).first()
    if existing:
        raise HTTPException(status_code=400, detail="E-mail ja registrado")

    user = User(
        email=user_in.email,
        full_name=user_in.full_name,
        hashed_password=get_password_hash(user_in.password),
        is_admin=False,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return Envelope(success=True, data=user)


@router.post("/login", response_model=Envelope[AuthResponse])
def login(payload: UserLogin, db: Session = Depends(get_session)):
    user = authenticate_user(payload.email, payload.password, db)
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    token_str = create_access_token({"sub": str(user.id)}, expires_delta=access_token_expires)
    token = Token(access_token=token_str)
    return Envelope(success=True, data=AuthResponse(user=user, token=token))


@router.get("/me", response_model=Envelope[UserOut])
def me(current_user: User = Depends(get_current_user)):
    return Envelope(success=True, data=current_user)
