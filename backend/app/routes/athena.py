from fastapi import APIRouter
from pydantic import BaseModel
from app.services.embeddings import search_similar_documents
from app.services.generator import generate_answer

router = APIRouter()

class Query(BaseModel):
    question: str

@router.post("/ask")
def ask_athena(query: Query):
    hits = search_similar_documents(query.question, k=4)

    if not hits:
        return {"answer": "Ainda não tenho conhecimento suficiente para responder."}

    context = "\n\n".join(h["text"] for h in hits)

    answer = generate_answer(context, query.question)

    return {"answer": answer}
