from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.security import get_current_user
from app.core.rate_limit import rate_limit
from app.db.session import get_session
from app.models import Chat, Message, User, ChatFeedback, FeedbackDirective
from app.schemas import AskRequest, ChatCreate, ChatOut, ChatUpdate, Envelope, MessageOut, MessageFeedbackIn
from app.services.generator import ChatGenerationError, generate_answer_with_history

router = APIRouter(prefix="/chats")


def _validate_question(question: str) -> None:
    if not question.strip():
        raise HTTPException(status_code=400, detail="Pergunta vazia.")
    if len(question) > settings.MAX_QUESTION_CHARS:
        raise HTTPException(
            status_code=400,
            detail=f"Pergunta muito longa (max {settings.MAX_QUESTION_CHARS} caracteres).",
        )


@router.get("", response_model=Envelope[list[ChatOut]])
def list_chats(db: Session = Depends(get_session), user: User = Depends(get_current_user)):
    chats = (
        db.query(Chat)
        .filter(Chat.user_id == user.id)
        .order_by(Chat.created_at.desc())
        .all()
    )
    return Envelope(success=True, data=chats)


@router.post("", response_model=Envelope[ChatOut])
def create_chat(payload: ChatCreate, db: Session = Depends(get_session), user: User = Depends(get_current_user)):
    chat = Chat(title=payload.title or "Novo Chat", user_id=user.id)
    db.add(chat)
    db.commit()
    db.refresh(chat)
    return Envelope(success=True, data=chat)


@router.put("/{chat_id}", response_model=Envelope[ChatOut])
def rename_chat(
    chat_id: int,
    payload: ChatUpdate,
    db: Session = Depends(get_session),
    user: User = Depends(get_current_user),
):
    chat = db.query(Chat).filter(Chat.id == chat_id, Chat.user_id == user.id).first()
    if not chat:
        raise HTTPException(status_code=404, detail="Chat nao encontrado")
    if payload.title:
        chat.title = payload.title
        db.add(chat)
        db.commit()
        db.refresh(chat)
    return Envelope(success=True, data=chat)


@router.delete("/{chat_id}", response_model=Envelope[bool])
def delete_chat(
    chat_id: int,
    db: Session = Depends(get_session),
    user: User = Depends(get_current_user),
):
    chat = db.query(Chat).filter(Chat.id == chat_id, Chat.user_id == user.id).first()
    if not chat:
        raise HTTPException(status_code=404, detail="Chat nao encontrado")
    # Collect related messages so we can clear feedbacks before deleting the chat.
    message_ids = [mid for (mid,) in db.query(Message.id).filter(Message.chat_id == chat.id).all()]
    if message_ids:
        feedback_ids = [
            fid
            for (fid,) in db.query(ChatFeedback.id).filter(ChatFeedback.message_id.in_(message_ids)).all()
        ]
        if feedback_ids:
            db.query(FeedbackDirective).filter(FeedbackDirective.feedback_id.in_(feedback_ids)).delete(
                synchronize_session=False
            )
            db.query(ChatFeedback).filter(ChatFeedback.id.in_(feedback_ids)).delete(synchronize_session=False)
        db.query(Message).filter(Message.id.in_(message_ids)).delete(synchronize_session=False)

    db.delete(chat)
    db.commit()
    return Envelope(success=True, data=True)


@router.get("/{chat_id}/messages", response_model=Envelope[list[MessageOut]])
def get_messages(chat_id: int, db: Session = Depends(get_session), user: User = Depends(get_current_user)):
    chat = db.query(Chat).filter(Chat.id == chat_id, Chat.user_id == user.id).first()
    if not chat:
        raise HTTPException(status_code=404, detail="Chat nao encontrado")

    messages = (
        db.query(Message)
        .filter(Message.chat_id == chat.id)
        .order_by(Message.created_at.asc())
        .all()
    )
    return Envelope(success=True, data=messages)


@router.post("/{chat_id}/ask", response_model=Envelope[dict])
def ask_chat(
    chat_id: int,
    payload: AskRequest,
    request: Request,
    db: Session = Depends(get_session),
    user: User = Depends(get_current_user),
):
    rate_limit(request)
    chat = db.query(Chat).filter(Chat.id == chat_id, Chat.user_id == user.id).first()
    if not chat:
        raise HTTPException(status_code=404, detail="Chat nao encontrado")

    try:
        _validate_question(payload.question)
        user_message = Message(role="user", content=payload.question, chat_id=chat.id)
        db.add(user_message)
        db.commit()
        db.refresh(user_message)

        history = (
            db.query(Message)
            .filter(Message.chat_id == chat.id)
            .order_by(Message.created_at.asc())
            .all()
        )
        history_payload = [{"role": m.role, "content": m.content} for m in history]

        llm_response = generate_answer_with_history(payload.question, history_payload)

        assistant_message = Message(role="assistant", content=llm_response["content"], chat_id=chat.id)
        db.add(assistant_message)
        db.commit()
        db.refresh(assistant_message)

        return Envelope(
            success=True,
            data={
                "id": llm_response["id"],
                "content": llm_response["content"],
                "raw": llm_response.get("raw"),
                "sources": llm_response.get("sources"),
                "message": MessageOut.model_validate(assistant_message),
            },
        )
    except ChatGenerationError as exc:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:  # noqa: BLE001
        db.rollback()
        raise HTTPException(status_code=500, detail="Erro ao processar a pergunta") from exc


@router.post("/{chat_id}/ask/stream")
def ask_chat_stream(
    chat_id: int,
    payload: AskRequest,
    request: Request,
    db: Session = Depends(get_session),
    user: User = Depends(get_current_user),
):
    rate_limit(request)
    chat = db.query(Chat).filter(Chat.id == chat_id, Chat.user_id == user.id).first()
    if not chat:
        raise HTTPException(status_code=404, detail="Chat nao encontrado")

    _validate_question(payload.question)
    user_msg = Message(role="user", content=payload.question, chat_id=chat.id)
    db.add(user_msg)
    db.commit()
    db.refresh(user_msg)

    history = (
        db.query(Message)
        .filter(Message.chat_id == chat.id)
        .order_by(Message.created_at.asc())
        .all()
    )
    history_payload = [{"role": m.role, "content": m.content} for m in history]

    def content_stream():
        try:
            llm_response = generate_answer_with_history(payload.question, history_payload)
            content = llm_response["content"]
            chunk_size = 160

            assistant_msg = Message(role="assistant", content=content, chat_id=chat.id)
            db.add(assistant_msg)
            db.commit()

            for idx in range(0, len(content), chunk_size):
                yield content[idx : idx + chunk_size]
        except Exception as exc:  # noqa: BLE001
            db.rollback()
            yield f"Erro: {exc}"

    return StreamingResponse(content_stream(), media_type="text/plain")


@router.post("/{chat_id}/feedback", response_model=Envelope[bool])
def send_feedback(
    chat_id: int,
    payload: MessageFeedbackIn,
    db: Session = Depends(get_session),
    user: User = Depends(get_current_user),
):
    chat = db.query(Chat).filter(Chat.id == chat_id, Chat.user_id == user.id).first()
    if not chat:
        raise HTTPException(status_code=404, detail="Chat nao encontrado")

    message = (
        db.query(Message)
        .filter(Message.id == payload.message_id, Message.chat_id == chat.id)
        .first()
    )
    if not message:
        raise HTTPException(status_code=404, detail="Mensagem nao encontrada")

    rating = max(min(payload.rating, 1), -1)
    feedback = ChatFeedback(
        message_id=message.id,
        user_id=user.id,
        rating=rating,
        comment=payload.comment,
    )
    db.add(feedback)
    db.commit()
    db.refresh(feedback)

    comment = (payload.comment or "").strip()
    if comment:
        now = datetime.utcnow()
        status = "applied" if user.is_admin else "pending"
        directive = FeedbackDirective(
            feedback_id=feedback.id,
            created_by=user.id,
            approved_by=user.id if user.is_admin else None,
            status=status,
            text=comment,
            approved_at=now if user.is_admin else None,
            applied_at=now if user.is_admin else None,
        )
        db.add(directive)
        db.commit()

    return Envelope(success=True, data=True)
