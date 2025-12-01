import uuid

import requests

from app.core.athena_prompt import ATHENA_SYSTEM_PROMPT
from app.core.config import settings
from app.services.embeddings import get_relevant_chunks


class ChatGenerationError(Exception):
    """Erro ao gerar resposta do modelo."""


def call_llm_api(messages: list[dict]) -> dict:
    """Chama endpoint de chat completion configurado e retorna payload completo."""
    payload = {
        "model": settings.LMSTUDIO_MODEL,
        "messages": messages,
        "temperature": 0.25,
        "max_tokens": 800,
    }
    try:
        response = requests.post(settings.LMSTUDIO_API_URL, json=payload, timeout=120)
        response.raise_for_status()
        data = response.json()
    except Exception as exc:  # noqa: BLE001
        raise ChatGenerationError(f"Falha ao chamar modelo: {exc}") from exc

    try:
        content = data["choices"][0]["message"]["content"]
    except Exception as exc:  # noqa: BLE001
        raise ChatGenerationError("Resposta invalida do modelo") from exc

    return {"id": str(uuid.uuid4()), "content": content, "raw": data}


def generate_answer_with_history(question: str, history: list[dict]) -> dict:
    """Gera resposta usando historico do chat e contexto das politicas."""
    context = get_relevant_chunks(question)
    system_content = (
        ATHENA_SYSTEM_PROMPT
        + "\n\n--- CONTEXTO DAS POLÍTICAS ---\n"
        + (context or "Nenhum trecho relevante de política foi encontrado para esta pergunta.")
    )

    messages = [{"role": "system", "content": system_content}] + history + [
        {"role": "user", "content": question}
    ]

    return call_llm_api(messages)
