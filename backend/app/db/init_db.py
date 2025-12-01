from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.security import get_password_hash
from app.db.database import Base, engine
from app.db.session import SessionLocal
from app.models import User


def ensure_admin_user(db: Session):
    existing = db.query(User).filter(User.email == settings.ADMIN_EMAIL).first()
    if existing:
        return existing

    admin = User(
        email=settings.ADMIN_EMAIL,
        full_name="Administrador",
        hashed_password=get_password_hash(settings.ADMIN_PASSWORD),
        is_admin=True,
    )
    db.add(admin)
    db.commit()
    db.refresh(admin)
    return admin


def init_db():
    # garante criação das tabelas antes de bootstrap
    Base.metadata.create_all(bind=engine)

    db = SessionLocal()
    try:
        ensure_admin_user(db)
    finally:
        db.close()
