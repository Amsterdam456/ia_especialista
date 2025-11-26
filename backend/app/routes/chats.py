from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.deps import get_db
from app.core.security import get_current_user
from app.db import models
from app.schemas import AskPayload, ChatCreate, ChatOut, MessageOut
from app.services.embeddings import search_similar_documents
from app.services.generator import generate_answer

router = APIRouter(prefix="/chats", tags=["chats"])


@router.get("", response_model=list[ChatOut])
def list_chats(current_user: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    chats = (
        db.query(models.ChatSession)
        .filter(models.ChatSession.user_id == current_user.id)
        .order_by(models.ChatSession.created_at.desc())
        .all()
    )
    return chats


@router.post("", response_model=ChatOut)
def create_chat(
    chat_in: ChatCreate, current_user: models.User = Depends(get_current_user), db: Session = Depends(get_db)
):
    title = chat_in.title or f"Nova conversa ({datetime.utcnow().strftime('%d/%m %H:%M')})"
    chat = models.ChatSession(title=title, user_id=current_user.id)
    db.add(chat)
    db.commit()
    db.refresh(chat)
    return chat


@router.get("/{chat_id}/messages", response_model=list[MessageOut])
def get_messages(
    chat_id: int, current_user: models.User = Depends(get_current_user), db: Session = Depends(get_db)
):
    chat = db.query(models.ChatSession).filter(models.ChatSession.id == chat_id).first()
    if not chat or chat.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Chat não encontrado")

    return (
        db.query(models.Message)
        .filter(models.Message.chat_id == chat_id)
        .order_by(models.Message.created_at.asc())
        .all()
    )


@router.post("/{chat_id}/ask", response_model=list[MessageOut])
def ask_chat(
    chat_id: int,
    payload: AskPayload,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    chat = db.query(models.ChatSession).filter(models.ChatSession.id == chat_id).first()
    if not chat or chat.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Chat não encontrado")

    user_message = models.Message(role="user", content=payload.question, chat_id=chat_id)
    db.add(user_message)

    hits = search_similar_documents(payload.question, k=4)
    if not hits:
        answer = "Ainda não tenho conhecimento suficiente para responder com base nas políticas."
    else:
        context = "\n\n".join(h["text"] for h in hits)
        answer = generate_answer(context, payload.question)

    assistant_message = models.Message(role="assistant", content=answer, chat_id=chat_id)
    db.add(assistant_message)
    db.commit()

    return (
        db.query(models.Message)
        .filter(models.Message.chat_id == chat_id)
        .order_by(models.Message.created_at.asc())
        .all()
    )
