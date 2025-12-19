from datetime import datetime
from pathlib import Path
from typing import List
import csv
import io
import os
import secrets
import string

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from pydantic import BaseModel

from app.core.config import settings
from app.core.security import get_current_admin, get_current_user, get_password_hash, normalize_email, validate_password
from app.db.session import get_session
from app.models import (
    ActionAudit,
    Chat,
    ChatFeedback,
    FeedbackDirective,
    Message,
    PolicyFile,
    SystemConfig,
    User,
)
from app.schemas import Envelope
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
from app.services.embeddings import remove_embeddings_for_source
from app.services.ingest import ingest_all_policies, get_ingest_status
from app.services.finance_ingest import ingest_finance_csv, load_pivot_cache, upload_finance_csv

router = APIRouter(prefix="/admin")


def log_action(db: Session, user_id: int, action: str, meta: dict | None = None) -> None:
    """Registra acoes administrativas para auditoria basica."""
    try:
        audit = ActionAudit(user_id=user_id, action=action, meta=meta or {})
        db.add(audit)
        db.commit()
    except Exception as exc:  # noqa: BLE001
        db.rollback()
        print(f"[audit] Falha ao registrar acao {action}: {exc}")


def secure_filename(filename: str) -> str:
    name = os.path.basename(filename).strip().replace(" ", "_")
    allowed = string.ascii_letters + string.digits + "._-"
    cleaned = "".join(ch for ch in name if ch in allowed)
    return cleaned or f"upload_{secrets.token_hex(8)}"


def generate_temp_password(length: int = 12) -> str:
    alphabet = string.ascii_letters + string.digits
    return "".join(secrets.choice(alphabet) for _ in range(length))


def max_upload_bytes() -> int:
    return settings.MAX_UPLOAD_MB * 1024 * 1024


# ---------------- Users ----------------
@router.get("/users", response_model=Envelope[List[UserAdminOut]])
def list_users(
    current_admin: User = Depends(get_current_admin),
    db: Session = Depends(get_session),
):
    users = db.query(User).order_by(User.created_at.desc()).all()
    return Envelope(success=True, data=users)


@router.post("/users", response_model=Envelope[UserAdminOut])
def create_user(payload: UserAdminCreate, current_admin: User = Depends(get_current_admin), db: Session = Depends(get_session)):
    email = normalize_email(payload.email)
    validate_password(payload.password, email=email)
    exists = db.query(User).filter(User.email == email).first()
    if exists:
        raise HTTPException(status_code=400, detail="Email ja existe")

    hashed = get_password_hash(payload.password)
    user = User(
        email=email,
        full_name=payload.full_name,
        hashed_password=hashed,
        is_admin=payload.role.lower() == "admin",
        is_active=True,
    )

    db.add(user)
    db.commit()
    db.refresh(user)
    log_action(db, current_admin.id, "create_user", {"user_id": user.id, "email": user.email})
    return Envelope(success=True, data=user)


@router.put("/users/{user_id}", response_model=Envelope[UserAdminOut])
def update_user(
    user_id: int,
    payload: UserAdminUpdate,
    current_admin: User = Depends(get_current_admin),
    db: Session = Depends(get_session),
):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        return Envelope(success=False, data=None, error="Usuario nao encontrado")

    if payload.full_name is not None:
        user.full_name = payload.full_name

    if payload.email is not None:
        email = normalize_email(payload.email)
        exists = db.query(User).filter(User.email == email, User.id != user.id).first()
        if exists:
            return Envelope(success=False, data=None, error="Email ja existe")
        user.email = email

    if payload.role is not None:
        user.is_admin = payload.role.lower() == "admin"

    if payload.is_active is not None:
        user.is_active = payload.is_active

    if payload.password is not None:
        validate_password(payload.password, email=user.email)
        user.hashed_password = get_password_hash(payload.password)

    db.add(user)
    db.commit()
    db.refresh(user)
    log_action(db, current_admin.id, "update_user", {"user_id": user.id})
    return Envelope(success=True, data=user)


@router.delete("/users/{user_id}", response_model=Envelope[bool])
def delete_user(user_id: int, current_admin: User = Depends(get_current_admin), db: Session = Depends(get_session)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        return Envelope(success=False, data=None, error="Usuario nao encontrado")
    if user.id == current_admin.id:
        return Envelope(success=False, data=None, error="Nao e permitido excluir o proprio usuario")

    message_ids = [
        msg_id for (msg_id,) in
        db.query(Message.id)
        .join(Chat, Message.chat_id == Chat.id)
        .filter(Chat.user_id == user.id)
        .all()
    ]
    if message_ids:
        db.query(ChatFeedback).filter(ChatFeedback.message_id.in_(message_ids)).delete(synchronize_session=False)
    db.query(ChatFeedback).filter(ChatFeedback.user_id == user.id).delete(synchronize_session=False)
    db.query(FeedbackDirective).filter(FeedbackDirective.created_by == user.id).delete(synchronize_session=False)
    db.query(FeedbackDirective).filter(FeedbackDirective.approved_by == user.id).delete(synchronize_session=False)
    db.query(ActionAudit).filter(ActionAudit.user_id == user.id).delete(synchronize_session=False)

    policies = db.query(PolicyFile).filter(PolicyFile.uploaded_by == user.id).all()
    for policy in policies:
        remove_embeddings_for_source(policy.filename)
        try:
            Path(policy.stored_path).unlink(missing_ok=True)  # type: ignore[arg-type]
        except Exception:
            pass
        db.delete(policy)

    db.query(Chat).filter(Chat.user_id == user.id).delete(synchronize_session=False)
    db.delete(user)
    db.commit()
    log_action(db, current_admin.id, "delete_user", {"user_id": user_id})
    return Envelope(success=True, data=True)


# ---------------- Policies ----------------
UPLOAD_DIR = Path("storage/policies")
ALLOWED_EXTENSIONS = {".pdf", ".docx", ".txt"}


@router.post("/policies/upload", response_model=Envelope[PolicyUploadResponse])
def upload_policy(
    file: UploadFile = File(...),
    current_admin: User = Depends(get_current_admin),
    db: Session = Depends(get_session),
):
    original = file.filename or "upload"
    ext = Path(original).suffix.lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(status_code=400, detail="Apenas PDF, DOCX ou TXT sao permitidos")

    contents = file.file.read()
    if len(contents) > max_upload_bytes():
        raise HTTPException(status_code=413, detail="Arquivo acima do limite permitido")

    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    safe_name = secure_filename(original)
    stored_name = safe_name
    counter = 1
    while (UPLOAD_DIR / stored_name).exists():
        stem = Path(safe_name).stem
        suffix = Path(safe_name).suffix
        stored_name = f"{stem}_{counter}{suffix}"
        counter += 1
    stored_path = UPLOAD_DIR / stored_name
    with stored_path.open("wb") as f:
        f.write(contents)

    policy = PolicyFile(
        filename=stored_name,
        stored_path=str(stored_path),
        uploaded_by=current_admin.id,
        embedding_status="pending",
    )
    db.add(policy)
    db.commit()
    db.refresh(policy)
    log_action(db, current_admin.id, "upload_policy", {"policy_id": policy.id, "filename": policy.filename})

    return Envelope(success=True, data=PolicyUploadResponse(id=policy.id, filename=policy.filename, status="pending"))


@router.get("/policies", response_model=Envelope[List[PolicyFileOut]])
def list_policies(current_admin: User = Depends(get_current_admin), db: Session = Depends(get_session)):
    policies = db.query(PolicyFile).order_by(PolicyFile.uploaded_at.desc()).all()
    return Envelope(success=True, data=policies)


@router.post("/policies/process", response_model=Envelope[bool])
def process_policies(
    policy_id: int | None = Form(None),
    current_admin: User = Depends(get_current_admin),
    db: Session = Depends(get_session),
):
    ingest_all_policies()
    log_action(db, current_admin.id, "process_policies", {"policy_id": policy_id})
    return Envelope(success=True, data=True)


@router.put("/policies/{policy_id}/reprocess", response_model=Envelope[bool])
def reprocess_policy(policy_id: int, current_admin: User = Depends(get_current_admin), db: Session = Depends(get_session)):
    policy = db.query(PolicyFile).filter(PolicyFile.id == policy_id).first()
    if not policy:
        return Envelope(success=False, data=None, error="Politica nao encontrada")
    policy.embedding_status = "pending"
    policy.embedding_last_error = None
    db.add(policy)
    db.commit()
    log_action(db, current_admin.id, "reprocess_policy", {"policy_id": policy_id})
    return Envelope(success=True, data=True)


@router.delete("/policies/{policy_id}", response_model=Envelope[bool])
def delete_policy(policy_id: int, current_admin: User = Depends(get_current_admin), db: Session = Depends(get_session)):
    policy = db.query(PolicyFile).filter(PolicyFile.id == policy_id).first()
    if not policy:
        return Envelope(success=False, data=None, error="Politica nao encontrada")

    stored_path = Path(policy.stored_path)
    db.delete(policy)
    db.commit()
    remove_embeddings_for_source(policy.filename)
    if stored_path.exists():
        stored_path.unlink(missing_ok=True)  # type: ignore[arg-type]
    log_action(db, current_admin.id, "delete_policy", {"policy_id": policy_id})
    return Envelope(success=True, data=True)


# ---------------- System Config ----------------
@router.get("/config", response_model=Envelope[SystemConfigOut])
def get_config(current_admin: User = Depends(get_current_admin), db: Session = Depends(get_session)):
    cfg = db.query(SystemConfig).first()
    if not cfg:
        cfg = SystemConfig()
        db.add(cfg)
        db.commit()
        db.refresh(cfg)
    return Envelope(success=True, data=cfg)


@router.put("/config", response_model=Envelope[SystemConfigOut])
def update_config(payload: SystemConfigIn, current_admin: User = Depends(get_current_admin), db: Session = Depends(get_session)):
    cfg = db.query(SystemConfig).first()
    if not cfg:
        cfg = SystemConfig()

    if payload.system_prompt is not None:
        cfg.system_prompt = payload.system_prompt
    if payload.model_name is not None:
        cfg.model_name = payload.model_name
    if payload.temperature is not None:
        if not 0 <= payload.temperature <= 2:
            raise HTTPException(status_code=400, detail="Temperatura deve estar entre 0 e 2.")
        cfg.temperature = payload.temperature
    if payload.top_p is not None:
        if not 0 <= payload.top_p <= 1:
            raise HTTPException(status_code=400, detail="Top P deve estar entre 0 e 1.")
        cfg.top_p = payload.top_p

    db.add(cfg)
    db.commit()
    db.refresh(cfg)
    log_action(db, current_admin.id, "update_config", {"model": cfg.model_name})
    return Envelope(success=True, data=cfg)


# ---------------- Audit & Feedback ----------------
@router.get("/audit", response_model=Envelope[List[ActionAuditOut]])
def list_audit(current_admin: User = Depends(get_current_admin), db: Session = Depends(get_session)):
    audits = db.query(ActionAudit).order_by(ActionAudit.created_at.desc()).limit(200).all()
    return Envelope(success=True, data=audits)


@router.get("/audit/export", response_model=None)
def export_audit_csv(current_admin: User = Depends(get_current_admin), db: Session = Depends(get_session)):
    audits = db.query(ActionAudit).order_by(ActionAudit.created_at.desc()).limit(1000).all()
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["id", "user_id", "action", "meta", "created_at"])
    for row in audits:
        writer.writerow([row.id, row.user_id, row.action, row.meta, row.created_at.isoformat()])
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=audit.csv"},
    )


@router.get("/feedback", response_model=Envelope[List[ChatFeedbackOut]])
def list_feedback(current_admin: User = Depends(get_current_admin), db: Session = Depends(get_session)):
    feedback = db.query(ChatFeedback).order_by(ChatFeedback.created_at.desc()).limit(200).all()
    return Envelope(success=True, data=feedback)


@router.get("/metrics", response_model=Envelope[dict])
def get_metrics(current_admin: User = Depends(get_current_admin), db: Session = Depends(get_session)):
    users = db.query(User).count()
    chats = db.query(Chat).count()
    messages = db.query(Message).count()
    policies = db.query(PolicyFile).count()
    feedback = db.query(ChatFeedback).count()
    directives_pending = db.query(FeedbackDirective).filter(FeedbackDirective.status == "pending").count()
    return Envelope(
        success=True,
        data={
            "users": users,
            "chats": chats,
            "messages": messages,
            "policies": policies,
            "feedback": feedback,
            "directives_pending": directives_pending,
        },
    )


@router.get("/ingest/status", response_model=Envelope[dict])
def ingest_status(_: User = Depends(get_current_admin), db: Session = Depends(get_session)):
    status = get_ingest_status(db)
    return Envelope(success=True, data=status)


class FeedbackResponse(BaseModel):
    feedback_id: int
    response: str


@router.post("/feedback/respond", response_model=Envelope[bool])
def respond_feedback(
    payload: FeedbackResponse,
    current_admin: User = Depends(get_current_admin),
    db: Session = Depends(get_session),
):
    fb = db.query(ChatFeedback).filter(ChatFeedback.id == payload.feedback_id).first()
    if not fb:
        return Envelope(success=False, data=False, error="Feedback nao encontrado")

    original = fb.comment or ""
    admin_note = f"[Resp admin] {payload.response}"
    fb.comment = f"{original}\n{admin_note}".strip()

    db.add(fb)
    db.commit()
    db.refresh(fb)
    log_action(db, current_admin.id, "respond_feedback", {"feedback_id": fb.id})
    return Envelope(success=True, data=True)


class FeedbackDirectiveApproveIn(BaseModel):
    text: str | None = None


@router.get("/feedback/directives", response_model=Envelope[List[dict]])
def list_feedback_directives(current_admin: User = Depends(get_current_admin), db: Session = Depends(get_session)):
    rows = (
        db.query(FeedbackDirective, ChatFeedback, User)
        .join(ChatFeedback, ChatFeedback.id == FeedbackDirective.feedback_id)
        .join(User, User.id == FeedbackDirective.created_by)
        .order_by(FeedbackDirective.created_at.desc())
        .all()
    )
    data = []
    for directive, feedback, user in rows:
        data.append(
            {
                "id": directive.id,
                "feedback_id": directive.feedback_id,
                "created_by": directive.created_by,
                "created_by_email": user.email,
                "status": directive.status,
                "text": directive.text,
                "created_at": directive.created_at,
                "approved_by": directive.approved_by,
                "approved_at": directive.approved_at,
                "applied_at": directive.applied_at,
                "rating": feedback.rating,
                "message_id": feedback.message_id,
            }
        )
    return Envelope(success=True, data=data)


@router.post("/feedback/directives/{directive_id}/approve", response_model=Envelope[bool])
def approve_feedback_directive(
    directive_id: int,
    payload: FeedbackDirectiveApproveIn,
    current_admin: User = Depends(get_current_admin),
    db: Session = Depends(get_session),
):
    directive = db.query(FeedbackDirective).filter(FeedbackDirective.id == directive_id).first()
    if not directive:
        return Envelope(success=False, data=False, error="Diretriz nao encontrada")

    if payload.text is not None:
        directive.text = payload.text

    now = datetime.utcnow()
    directive.status = "applied"
    directive.approved_by = current_admin.id
    directive.approved_at = now
    directive.applied_at = now
    db.add(directive)
    db.commit()
    log_action(db, current_admin.id, "approve_feedback_directive", {"directive_id": directive.id})
    return Envelope(success=True, data=True)


@router.post("/feedback/directives/{directive_id}/reject", response_model=Envelope[bool])
def reject_feedback_directive(
    directive_id: int,
    current_admin: User = Depends(get_current_admin),
    db: Session = Depends(get_session),
):
    directive = db.query(FeedbackDirective).filter(FeedbackDirective.id == directive_id).first()
    if not directive:
        return Envelope(success=False, data=False, error="Diretriz nao encontrada")

    now = datetime.utcnow()
    directive.status = "rejected"
    directive.approved_by = current_admin.id
    directive.approved_at = now
    directive.applied_at = None
    db.add(directive)
    db.commit()
    log_action(db, current_admin.id, "reject_feedback_directive", {"directive_id": directive.id})
    return Envelope(success=True, data=True)


# ---------------- Bulk users ----------------
@router.post("/users/bulk", response_model=Envelope[dict])
def create_users_bulk(
    file: UploadFile = File(...),
    current_admin: User = Depends(get_current_admin),
    db: Session = Depends(get_session),
):
    content = file.file.read()
    if len(content) > max_upload_bytes():
        raise HTTPException(status_code=413, detail="Arquivo acima do limite permitido")

    text = content.decode("utf-8", errors="ignore")
    reader = csv.DictReader(io.StringIO(text))
    created = 0
    errors = []
    temp_passwords: list[dict] = []
    for idx, row in enumerate(reader, start=1):
        email_raw = (row.get("email") or "").strip()
        full_name = (row.get("full_name") or "").strip()
        role = (row.get("role") or "usuario").strip().lower()
        if not email_raw:
            errors.append(f"Linha {idx}: email vazio")
            continue

        email = normalize_email(email_raw)
        exists = db.query(User).filter(User.email == email).first()
        if exists:
            errors.append(f"Linha {idx}: email ja existe")
            continue

        password = (row.get("password") or "").strip()
        if password:
            try:
                validate_password(password, email=email)
            except HTTPException:
                password = ""

        if not password:
            password = generate_temp_password()
            temp_passwords.append({"email": email, "password": password})

        is_admin = role == "admin"
        user = User(
            email=email,
            full_name=full_name,
            hashed_password=get_password_hash(password),
            is_admin=is_admin,
            is_active=True,
        )
        db.add(user)
        created += 1

    db.commit()
    log_action(db, current_admin.id, "bulk_create_users", {"created": created, "errors": len(errors)})
    return Envelope(success=True, data={"created": created, "errors": errors, "temp_passwords": temp_passwords})


@router.get("/users/template", response_model=None)
def download_users_template(current_admin: User = Depends(get_current_admin)):
    csv_content = "email,full_name,role,password\nuser1@example.com,Nome 1,usuario,\nuser2@example.com,Nome 2,moderador,\n"
    return StreamingResponse(
        iter([csv_content]),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=template_usuarios.csv"},
    )


@router.post("/finance/import", response_model=Envelope[bool])
def import_finance(current_admin: User = Depends(get_current_admin), db: Session = Depends(get_session)):
    ok = ingest_finance_csv()
    if not ok:
        return Envelope(success=False, data=False, error="CSV financeiro nao encontrado ou vazio")
    log_action(db, current_admin.id, "import_finance_csv")
    return Envelope(success=True, data=True)


@router.post("/finance/upload", response_model=Envelope[bool])
def upload_finance(
    file: UploadFile = File(...),
    current_admin: User = Depends(get_current_admin),
    db: Session = Depends(get_session),
):
    if not (file.filename or "").lower().endswith(".csv"):
        raise HTTPException(status_code=400, detail="Apenas CSV e permitido")

    content = file.file.read()
    if len(content) > max_upload_bytes():
        raise HTTPException(status_code=413, detail="Arquivo acima do limite permitido")

    temp_path = Path("data") / f"_upload_{secure_filename(file.filename or 'finance.csv')}"
    temp_path.parent.mkdir(parents=True, exist_ok=True)
    with temp_path.open("wb") as f:
        f.write(content)

    ok = upload_finance_csv(temp_path)
    try:
        temp_path.unlink(missing_ok=True)  # type: ignore[arg-type]
    except Exception:
        pass

    if not ok:
        return Envelope(success=False, data=False, error="Falha ao processar CSV financeiro")

    log_action(db, current_admin.id, "upload_finance_csv", {"filename": file.filename})
    return Envelope(success=True, data=True)


@router.get("/finance/pivot", response_model=Envelope[dict])
def get_pivot_data(
    cenario: str | None = None,
    ano: str | None = None,
    current_user: User = Depends(get_current_user),
):
    payload = load_pivot_cache() or {}
    raw = payload.get("raw", [])
    aggregates = payload.get("aggregates", [])
    dre = payload.get("dre", [])

    if cenario:
        aggregates = [d for d in aggregates if str(d.get("base", "")).lower() == cenario.lower()]
        dre = [d for d in dre if str(d.get("base", "")).lower() == cenario.lower()]
    if ano:
        aggregates = [d for d in aggregates if str(d.get("ano", "")).lower() == ano.lower()]
        dre = [d for d in dre if str(d.get("ano", "")).lower() == ano.lower()]

    return Envelope(success=True, data={"raw": raw, "aggregates": aggregates, "dre": dre})
