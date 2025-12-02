from pathlib import Path
from typing import List
import csv
import io

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.core.security import get_current_admin, get_password_hash
from app.db.session import get_session
from app.models import (
    ActionAudit,
    ChatFeedback,
    PolicyFile,
    SystemConfig,
    User,
)
from app.schemas import Envelope, UserOut
from app.schemas.admin import (
    ActionAuditOut,
    ChatFeedbackOut,
    PolicyFileOut,
    PolicyUploadResponse,
    SystemConfigIn,
    SystemConfigOut,
    UserAdminCreate,
    UserAdminOut,
    UserAdminUpdate,
)
from app.services.ingest import POLICY_DIR, ingest_all_policies

router = APIRouter(prefix="/admin")


# ---------------- Users ----------------
@router.get("/users", response_model=Envelope[List[UserAdminOut]])
def list_users(
    _: User = Depends(get_current_admin),
    db: Session = Depends(get_session),
):
    users = db.query(User).order_by(User.created_at.desc()).all()
    return Envelope(success=True, data=users)


@router.post("/users", response_model=Envelope[UserAdminOut])
def create_user(payload: UserAdminCreate, _: User = Depends(get_current_admin), db: Session = Depends(get_session)):
    exists = db.query(User).filter(User.email == payload.email).first()
    if exists:
        raise HTTPException(status_code=400, detail="Email já existe")

    # 🔥 CORREÇÃO: aplicar hash real
    hashed = get_password_hash(payload.password)

    user = User(
        email=payload.email,
        full_name=payload.full_name,
        hashed_password=hashed,  # ✔ agora está correto
        is_admin=payload.role.lower() == "admin",
    )

    db.add(user)
    db.commit()
    db.refresh(user)
    return Envelope(success=True, data=user)


@router.put("/users/{user_id}", response_model=Envelope[UserAdminOut])
def update_user(
    user_id: int,
    payload: UserAdminUpdate,
    _: User = Depends(get_current_admin),
    db: Session = Depends(get_session),
):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        return Envelope(success=False, data=None, error="Usuário não encontrado")

    if payload.full_name is not None:
        user.full_name = payload.full_name

    if payload.role is not None:
        user.is_admin = payload.role.lower() == "admin"

    if payload.password is not None:
        # 🔥 permitir alteração de senha
        user.hashed_password = get_password_hash(payload.password)

    db.add(user)
    db.commit()
    db.refresh(user)
    return Envelope(success=True, data=user)


@router.delete("/users/{user_id}", response_model=Envelope[bool])
def delete_user(user_id: int, _: User = Depends(get_current_admin), db: Session = Depends(get_session)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        return Envelope(success=False, data=None, error="Usuário não encontrado")
    db.delete(user)
    db.commit()
    return Envelope(success=True, data=True)


# ---------------- Policies ----------------
UPLOAD_DIR = Path("storage/policies")


@router.post("/policies/upload", response_model=Envelope[PolicyUploadResponse])
def upload_policy(
    file: UploadFile = File(...),
    current_admin: User = Depends(get_current_admin),
    db: Session = Depends(get_session),
):
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Apenas PDFs são permitidos")

    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    stored_path = UPLOAD_DIR / file.filename
    with stored_path.open("wb") as f:
        f.write(file.file.read())

    policy = PolicyFile(
        filename=file.filename,
        stored_path=str(stored_path),
        uploaded_by=current_admin.id,
        embedding_status="pending",
    )
    db.add(policy)
    db.commit()
    db.refresh(policy)

    return Envelope(success=True, data=PolicyUploadResponse(id=policy.id, filename=policy.filename, status="pending"))


@router.get("/policies", response_model=Envelope[List[PolicyFileOut]])
def list_policies(_: User = Depends(get_current_admin), db: Session = Depends(get_session)):
    policies = db.query(PolicyFile).order_by(PolicyFile.uploaded_at.desc()).all()
    return Envelope(success=True, data=policies)


@router.post("/policies/process", response_model=Envelope[bool])
def process_policies(
    policy_id: int | None = Form(None),
    _: User = Depends(get_current_admin),
    db: Session = Depends(get_session),
):
    ingest_all_policies()
    return Envelope(success=True, data=True)


@router.put("/policies/{policy_id}/reprocess", response_model=Envelope[bool])
def reprocess_policy(policy_id: int, _: User = Depends(get_current_admin), db: Session = Depends(get_session)):
    policy = db.query(PolicyFile).filter(PolicyFile.id == policy_id).first()
    if not policy:
        return Envelope(success=False, data=None, error="Política não encontrada")
    policy.embedding_status = "pending"
    policy.embedding_last_error = None
    db.add(policy)
    db.commit()
    return Envelope(success=True, data=True)


@router.delete("/policies/{policy_id}", response_model=Envelope[bool])
def delete_policy(policy_id: int, _: User = Depends(get_current_admin), db: Session = Depends(get_session)):
    policy = db.query(PolicyFile).filter(PolicyFile.id == policy_id).first()
    if not policy:
        return Envelope(success=False, data=None, error="Política não encontrada")
    db.delete(policy)
    db.commit()
    return Envelope(success=True, data=True)


# ---------------- System Config ----------------
@router.get("/config", response_model=Envelope[SystemConfigOut])
def get_config(_: User = Depends(get_current_admin), db: Session = Depends(get_session)):
    cfg = db.query(SystemConfig).first()
    if not cfg:
        cfg = SystemConfig()
        db.add(cfg)
        db.commit()
        db.refresh(cfg)
    return Envelope(success=True, data=cfg)


@router.put("/config", response_model=Envelope[SystemConfigOut])
def update_config(payload: SystemConfigIn, _: User = Depends(get_current_admin), db: Session = Depends(get_session)):
    cfg = db.query(SystemConfig).first()
    if not cfg:
        cfg = SystemConfig()

    if payload.system_prompt is not None:
        cfg.system_prompt = payload.system_prompt
    if payload.model_name is not None:
        cfg.model_name = payload.model_name
    if payload.temperature is not None:
        cfg.temperature = payload.temperature
    if payload.top_p is not None:
        cfg.top_p = payload.top_p

    db.add(cfg)
    db.commit()
    db.refresh(cfg)
    return Envelope(success=True, data=cfg)


# ---------------- Audit & Feedback ----------------
@router.get("/audit", response_model=Envelope[List[ActionAuditOut]])
def list_audit(_: User = Depends(get_current_admin), db: Session = Depends(get_session)):
    audits = db.query(ActionAudit).order_by(ActionAudit.created_at.desc()).limit(200).all()
    return Envelope(success=True, data=audits)


@router.get("/feedback", response_model=Envelope[List[ChatFeedbackOut]])
def list_feedback(_: User = Depends(get_current_admin), db: Session = Depends(get_session)):
    feedback = db.query(ChatFeedback).order_by(ChatFeedback.created_at.desc()).limit(200).all()
    return Envelope(success=True, data=feedback)


# ---------------- Bulk users ----------------
@router.post("/users/bulk", response_model=Envelope[dict])
def create_users_bulk(
    file: UploadFile = File(...),
    _: User = Depends(get_current_admin),
    db: Session = Depends(get_session),
):
    content = file.file.read()
    text = content.decode("utf-8", errors="ignore")
    reader = csv.DictReader(io.StringIO(text))
    created = 0
    errors = []
    for idx, row in enumerate(reader, start=1):
        email = (row.get("email") or "").strip()
        full_name = (row.get("full_name") or "").strip()
        role = (row.get("role") or "usuario").strip().lower()
        if not email:
            errors.append(f"Linha {idx}: email vazio")
            continue
        exists = db.query(User).filter(User.email == email).first()
        if exists:
            errors.append(f"Linha {idx}: email já existe")
            continue
        hashed = get_password_hash("123")
        is_admin = role == "admin"
        user = User(email=email, full_name=full_name, hashed_password=hashed, is_admin=is_admin)
        db.add(user)
        created += 1
    db.commit()
    return Envelope(success=True, data={"created": created, "errors": errors})


@router.get("/users/template", response_model=None)
def download_users_template(_: User = Depends(get_current_admin)):
    csv_content = "email,full_name,role\nuser1@example.com,Nome 1,usuario\nuser2@example.com,Nome 2,moderador\n"
    return StreamingResponse(
        iter([csv_content]),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=template_usuarios.csv"},
    )
