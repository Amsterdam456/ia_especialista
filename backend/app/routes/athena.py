from fastapi import APIRouter

from app.schemas import AskRequest, AskResponse, Envelope, StatusResponse
from app.services.athena_core import athena_answer

router = APIRouter()


@router.get("/health", response_model=Envelope[StatusResponse])
def health_check():
    return Envelope(success=True, data=StatusResponse())


@router.post("/ask", response_model=Envelope[AskResponse])
def ask_athena(payload: AskRequest):
    result = athena_answer(payload.question)
    response = AskResponse(answer=result.get("answer", ""), meta=result.get("meta"))
    return Envelope(success=True, data=response)
