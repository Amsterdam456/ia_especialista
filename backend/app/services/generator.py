import uuid
import requests

from app.core.athena_prompt import ATHENA_SYSTEM_PROMPT
from app.core.config import settings
from app.services.embeddings import get_relevant_chunks


class ChatGenerationError(Exception):
    """Erro ao gerar resposta do modelo."""


def call_llm_api(messages: list[dict]) -> dict:
    """Chama o endpoint /v1/responses do LM Studio (Qwen2.5)."""
    payload = {
        "model": settings.LMSTUDIO_MODEL,
        "input": messages,
        "temperature": 0.25,
        "max_tokens": 600,
        "stream": False,
    }

    try:
        response = requests.post(
            settings.LMSTUDIO_API_URL,
            json=payload,
            headers={"Content-Type": "application/json"},
            timeout=300,  # modelos maiores podem levar mais tempo; aumentar tolerância
        )
        response.raise_for_status()
        data = response.json()
    except Exception as exc:  # noqa: BLE001
        raise ChatGenerationError(f"Falha ao chamar modelo: {exc}") from exc

    try:
        output_items = data.get("output") or []
        first_output = output_items[0] if output_items else {}
        content_parts = first_output.get("content") or []

        if isinstance(content_parts, str):
            content = content_parts
        else:
            text_chunks: list[str] = []
            for part in content_parts:
                if isinstance(part, dict) and "text" in part:
                    text_chunks.append(str(part.get("text", "")))
                elif isinstance(part, dict) and "content" in part:
                    text_chunks.append(str(part.get("content", "")))
                else:
                    text_chunks.append(str(part))
            content = "".join(text_chunks).strip()

        if not content:
            raise ValueError("Conteúdo vazio retornado pelo modelo")
    except Exception as exc:  # noqa: BLE001
        raise ChatGenerationError("Resposta inválida do modelo") from exc

    return {"id": str(uuid.uuid4()), "content": content, "raw": data}


def generate_answer_with_history(question: str, history: list[dict]) -> dict:
    """Gera resposta usando histórico do chat e contexto das políticas."""
    context = get_relevant_chunks(question)

    system_content = (
        ATHENA_SYSTEM_PROMPT
        + "\n\n--- CONTEXTO DAS POLÍTICAS ---\n"
        + (context or "Nenhum trecho relevante de política foi encontrado para esta pergunta.")
    )

    messages = [{"role": "system", "content": system_content}] + history

    return call_llm_api(messages)
