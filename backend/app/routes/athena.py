from fastapi import APIRouter, HTTPException, Request

from app.core.config import settings
from app.core.rate_limit import rate_limit
from app.schemas import AskRequest, AskResponse, Envelope, StatusResponse
from app.services.generator import ChatGenerationError, generate_answer_with_history

router = APIRouter()


@router.get("/health", response_model=Envelope[StatusResponse])
def health_check():
    return Envelope(success=True, data=StatusResponse())


@router.post("/ask", response_model=Envelope[AskResponse])
def ask_athena(payload: AskRequest, request: Request):
    rate_limit(request)
    if not payload.question.strip():
        raise HTTPException(status_code=400, detail="Pergunta vazia.")
    if len(payload.question) > settings.MAX_QUESTION_CHARS:
        raise HTTPException(
            status_code=400,
            detail=f"Pergunta muito longa (max {settings.MAX_QUESTION_CHARS} caracteres).",
        )
    try:
        result = generate_answer_with_history(payload.question, [{"role": "user", "content": payload.question}])
        response = AskResponse(answer=result.get("content", ""), meta={"sources": result.get("sources", [])})
        return Envelope(success=True, data=response)
    except ChatGenerationError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
