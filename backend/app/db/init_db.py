from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.security import get_password_hash
from app.db.database import Base, engine
from app.db.session import SessionLocal
from app.models import SystemConfig, User


def ensure_admin_user(db: Session):
    existing = db.query(User).filter(User.email == settings.ADMIN_EMAIL).first()
    if existing:
        return existing

    admin = User(
        email=settings.ADMIN_EMAIL,
        full_name="Administrador",
        hashed_password=get_password_hash(settings.ADMIN_PASSWORD),
        is_admin=True,
        is_active=True,
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

        cfg = db.query(SystemConfig).first()
        if not cfg:
            cfg = SystemConfig(model_name=settings.LMSTUDIO_MODEL, temperature=0.25, top_p=1.0)
            db.add(cfg)
            db.commit()
        else:
            changed = False
            if not (cfg.model_name or "").strip():
                cfg.model_name = settings.LMSTUDIO_MODEL
                changed = True

            # Se o .env aponta para um modelo melhor (ex.: Qwen), migramos automaticamente
            # de modelos "phi" para o modelo do ambiente.
            env_model = (settings.LMSTUDIO_MODEL or "").strip()
            db_model = (cfg.model_name or "").strip()
            if (
                env_model
                and db_model
                and env_model != db_model
                and db_model.lower().startswith("phi")
                and env_model.lower().startswith("qwen")
            ):
                cfg.model_name = env_model
                changed = True
            if cfg.temperature is None:
                cfg.temperature = 0.25
                changed = True
            if cfg.top_p is None:
                cfg.top_p = 1.0
                changed = True
            if changed:
                db.add(cfg)
                db.commit()
    finally:
        db.close()
