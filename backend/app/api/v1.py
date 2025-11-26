from fastapi import APIRouter
from pydantic import BaseModel
from app.services.athena_core import athena_answer


router = APIRouter()


class AskRequest(BaseModel):
    question: str


class AskResponse(BaseModel):
    answer: str
    meta: dict


@router.get("/health")
def health_check():
    return {"status": "ok", "service": "athena-api"}


@router.post("/ask", response_model=AskResponse)
def ask_athena(payload: AskRequest):
    result = athena_answer(payload.question)
    return AskResponse(answer=result["answer"], meta=result["meta"])
