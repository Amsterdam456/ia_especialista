from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.security import get_password_hash
from app.db import models


def ensure_admin_user(db: Session):
    existing = db.query(models.User).filter(models.User.email == settings.ADMIN_EMAIL).first()
    if existing:
        return existing

    admin = models.User(
        email=settings.ADMIN_EMAIL,
        full_name="Administrador",
        hashed_password=get_password_hash(settings.ADMIN_PASSWORD),
        is_admin=True,
    )
    db.add(admin)
    db.commit()
    db.refresh(admin)
    return admin
