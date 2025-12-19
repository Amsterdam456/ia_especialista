from datetime import timedelta

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.core.auth import authenticate_user
from app.core.config import settings
from app.core.rate_limit import rate_limit
from app.core.security import (
    create_access_token,
    get_current_user,
    get_password_hash,
    normalize_email,
    validate_password,
    verify_password,
)
from app.db.session import get_session
from app.models import User
from app.schemas import AuthResponse, Envelope, Token, UserCreate, UserLogin, UserOut
from app.schemas.user import PasswordChange

router = APIRouter(prefix="/auth")


@router.post("/register", response_model=Envelope[UserOut])
def register(user_in: UserCreate, request: Request, db: Session = Depends(get_session)):
    rate_limit(request)
    email = normalize_email(user_in.email)
    validate_password(user_in.password, email=email)

    existing = db.query(User).filter(User.email == email).first()
    if existing:
        raise HTTPException(status_code=400, detail="E-mail ja registrado")

    user = User(
        email=email,
        full_name=user_in.full_name,
        hashed_password=get_password_hash(user_in.password),
        is_admin=False,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return Envelope(success=True, data=user)


@router.post("/login", response_model=Envelope[AuthResponse])
def login(payload: UserLogin, request: Request, db: Session = Depends(get_session)):
    rate_limit(request)
    user = authenticate_user(payload.email, payload.password, db)
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    token_str = create_access_token({"sub": str(user.id)}, expires_delta=access_token_expires)
    token = Token(access_token=token_str)
    return Envelope(success=True, data=AuthResponse(user=user, token=token))


@router.get("/me", response_model=Envelope[UserOut])
def me(current_user: User = Depends(get_current_user)):
    return Envelope(success=True, data=current_user)


@router.post("/change-password", response_model=Envelope[bool])
def change_password(payload: PasswordChange, db: Session = Depends(get_session), current_user: User = Depends(get_current_user)):
    user = db.query(User).filter(User.id == current_user.id).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Usuario nao encontrado")

    if payload.old_password:
        if not verify_password(payload.old_password, user.hashed_password):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Senha atual invalida")

    validate_password(payload.new_password, email=user.email)
    if payload.old_password and payload.old_password == payload.new_password:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Nova senha deve ser diferente.")

    user.hashed_password = get_password_hash(payload.new_password)
    db.add(user)
    db.commit()
    return Envelope(success=True, data=True)
