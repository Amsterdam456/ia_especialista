from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.core.security import get_current_user
from app.db.session import get_session
from app.models import Chat, Message, User
from app.schemas import AskRequest, ChatCreate, ChatOut, ChatUpdate, Envelope, MessageOut
from app.services.generator import ChatGenerationError, generate_answer_with_history

router = APIRouter(prefix="/chats")


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
        return Envelope(success=False, data=None, error="Chat nao encontrado")
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
        return Envelope(success=False, data=None, error="Chat nao encontrado")
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
    db: Session = Depends(get_session),
    user: User = Depends(get_current_user),
):
    chat = db.query(Chat).filter(Chat.id == chat_id, Chat.user_id == user.id).first()
    if not chat:
        return Envelope(success=False, data=None, error="Chat nao encontrado")

    try:
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
                "message": MessageOut.model_validate(assistant_message),
            },
        )
    except ChatGenerationError as exc:
        db.rollback()
        return Envelope(success=False, data=None, error=str(exc))
    except Exception:  # noqa: BLE001
        db.rollback()
        return Envelope(success=False, data=None, error="Erro ao processar a pergunta")


@router.post("/{chat_id}/ask/stream")
def ask_chat_stream(
    chat_id: int,
    payload: AskRequest,
    db: Session = Depends(get_session),
    user: User = Depends(get_current_user),
):
    chat = db.query(Chat).filter(Chat.id == chat_id, Chat.user_id == user.id).first()
    if not chat:
        raise HTTPException(status_code=404, detail="Chat nao encontrado")

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
            assistant_msg = Message(role="assistant", content=llm_response["content"], chat_id=chat.id)
            db.add(assistant_msg)
            db.commit()
            return llm_response["content"]
        except Exception as exc:  # noqa: BLE001
            return f"Erro: {exc}"

    return StreamingResponse(iter([content_stream()]), media_type="text/plain")
