from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.deps import get_db
from app.core.security import get_current_admin
from app.db import models
from app.schemas import UserOut
from app.services.ingest import POLICY_DIR

router = APIRouter(prefix="/admin", tags=["admin"])


@router.get("/users", response_model=list[UserOut])
def list_users(
    _: models.User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    return db.query(models.User).order_by(models.User.created_at.desc()).all()


@router.get("/policies", response_model=list[str])
def list_policies(_: models.User = Depends(get_current_admin)):
    if not POLICY_DIR.exists():
        return []
    return [p.name for p in POLICY_DIR.iterdir() if p.is_file() and not p.name.startswith(".")]
