import re
import uuid

import requests
from sqlalchemy.exc import OperationalError
from sqlalchemy.orm import Session

from app.core.athena_prompt import ATHENA_SYSTEM_PROMPT
from app.core.config import settings
from app.db.session import SessionLocal
from app.models import FeedbackDirective, SystemConfig
from app.services.embeddings import get_relevant_chunks_with_meta


class ChatGenerationError(Exception):
    """Erro ao gerar resposta do modelo."""


def load_system_config() -> dict:
    db: Session = SessionLocal()
    try:
        cfg = db.query(SystemConfig).first()
        if not cfg:
            return {}
        return {
            "system_prompt": cfg.system_prompt,
            "model_name": cfg.model_name,
            "temperature": cfg.temperature,
            "top_p": cfg.top_p,
        }
    finally:
        db.close()


def load_feedback_directives(limit: int | None = None) -> list[str]:
    db: Session = SessionLocal()
    try:
        query = (
            db.query(FeedbackDirective)
            .filter(FeedbackDirective.status == "applied")
            .order_by(FeedbackDirective.applied_at.desc())
        )
        if limit:
            query = query.limit(limit)
        return [row.text for row in query.all()]
    except OperationalError:
        return []
    finally:
        db.close()


def call_llm_api(messages: list[dict], *, temperature: float | None = None, top_p: float | None = None) -> dict:
    """Compat: chama o endpoint /v1/responses do LM Studio."""
    return call_llm_api_with_limits(messages, temperature=temperature, top_p=top_p, max_tokens=600)


def call_llm_api_with_limits(
    messages: list[dict],
    *,
    temperature: float | None = None,
    top_p: float | None = None,
    max_tokens: int = 600,
) -> dict:
    """Chama o endpoint /v1/responses do LM Studio, permitindo ajustar limites."""
    cfg = load_system_config()
    env_model = (settings.LMSTUDIO_MODEL or "").strip()
    db_model = (cfg.get("model_name") or "").strip()
    model_name = db_model or env_model
    # Se o banco estiver apontando para um modelo Phi antigo, mas o ambiente já está
    # configurado para Qwen, preferimos o modelo do ambiente para evitar regressão.
    if (
        env_model
        and db_model
        and env_model != db_model
        and db_model.lower().startswith("phi")
        and env_model.lower().startswith("qwen")
    ):
        model_name = env_model

    payload = {
        "model": model_name,
        "input": messages,
        "temperature": temperature if temperature is not None else cfg.get("temperature", 0.25),
        "top_p": top_p if top_p is not None else cfg.get("top_p", 1.0),
        "max_tokens": max_tokens,
        "stream": False,
    }

    try:
        response = requests.post(
            settings.LMSTUDIO_API_URL,
            json=payload,
            headers={"Content-Type": "application/json"},
            timeout=settings.LMSTUDIO_TIMEOUT_SECONDS,
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
            raise ValueError("Conteudo vazio retornado pelo modelo")
    except Exception as exc:  # noqa: BLE001
        raise ChatGenerationError("Resposta invalida do modelo") from exc

    return {"id": str(uuid.uuid4()), "content": content, "raw": data}


_XYZ_RE = re.compile(r"\b(paginacao\s+xyz|paginação\s+xyz|xyz)\b", re.IGNORECASE)


_SUMMARY_TEMPLATE = """
Quando o MODO DE RESPOSTA for RESUMO, responda exatamente nesta estrutura:

Resumo executivo (3-5 linhas)

Dados do evento
- Evento:
- Data:
- Horario:
- Duracao:
- Local:
- Contratante / Contratada (se existir):

Valores e pagamento
- Valor por pessoa / pacotes / taxas (se existir):
- O que esta incluso (se existir):
- Condicoes de pagamento (se existir):

Prazos e obrigacoes
- Prazos relevantes (ex.: envio de lista, comunicacoes):
- Obrigacoes do contratante:
- Obrigacoes da contratada:

Penalidades / reajustes (se existir)
- Multas, cobrancas por atraso, reajustes ou regras de cancelamento:

Regras importantes (bullets curtos)
- ...

REGRAS IMPORTANTES:
- Nao liste hash, numero de documento, IDs (ex.: Clicksign) e assinaturas, a menos que o usuario peça.
- Se algum campo nao estiver no contexto enviado, escreva: "Nao localizado no trecho enviado".
""".strip()


def _clean_response_text(text: str) -> str:
    """
    Remove ruídos comuns (placeholders como 'paginação XYZ') e reduz repetição de linhas.
    Mantém a ordem original.
    """
    lines = [ln.rstrip() for ln in (text or "").splitlines()]
    cleaned: list[str] = []
    seen = set()

    for ln in lines:
        stripped = ln.strip()
        if not stripped:
            if cleaned and cleaned[-1] != "":
                cleaned.append("")
            continue
        if _XYZ_RE.search(stripped):
            continue
        key = re.sub(r"\s+", " ", stripped.lower())
        if key in seen:
            continue
        seen.add(key)
        cleaned.append(stripped)

    while cleaned and cleaned[-1] == "":
        cleaned.pop()

    return "\n".join(cleaned).strip()


_DOC_META_RE = re.compile(
    r"\b(sha256|clicksign|hash do documento|documento numero|documento n[úu]mero|assinaturas?:)\b",
    re.IGNORECASE,
)


def _remove_document_metadata(answer: str) -> str:
    lines = [ln.rstrip() for ln in (answer or "").splitlines()]
    kept: list[str] = []
    for ln in lines:
        if _DOC_META_RE.search(ln):
            continue
        kept.append(ln)
    return "\n".join(kept).strip()


def _append_sources(answer: str, citations: list[dict]) -> str:
    if not citations:
        return answer

    unique: list[tuple[str, int]] = []
    seen = set()
    for c in citations:
        source = str(c.get("source") or "").strip()
        page = c.get("page")
        if not source or page is None:
            continue
        key = (source, int(page))
        if key in seen:
            continue
        seen.add(key)
        unique.append(key)

    if not unique:
        return answer

    sources_block = "\n".join(f"- {src} (p. {pg})" for (src, pg) in unique[:8])
    return (answer.rstrip() + "\n\nFontes consultadas:\n" + sources_block).strip()


def _dedupe_consecutive_messages(messages: list[dict]) -> list[dict]:
    """Remove mensagens consecutivas idênticas para reduzir tokens."""
    deduped: list[dict] = []
    last_key: tuple[str, str] | None = None
    for m in messages:
        role = str(m.get("role") or "")
        content = str(m.get("content") or "")
        key = (role, content.strip())
        if last_key == key:
            continue
        deduped.append(m)
        last_key = key
    return deduped


def generate_answer_with_history(question: str, history: list[dict]) -> dict:
    """Gera resposta usando historico do chat e contexto das politicas."""
    lowered = question.lower()

    def looks_like_small_talk(text: str) -> bool:
        t = text.strip().lower()
        if len(t) > 80:
            return False
        greetings = ("ola", "olá", "oi", "bom dia", "boa tarde", "boa noite", "tudo bem", "como voce esta", "como você está")
        if any(g in t for g in greetings):
            # se nao estiver pedindo politica/documento, tratamos como conversa geral
            keywords = ("politica", "pol", "ctt", "documento", "arquivo", "pdf", "procedimento", "cartao", "cartão")
            return not any(k in t for k in keywords)
        return False

    is_summary_request = any(key in lowered for key in ("resumo", "resuma", "sintese", "sintetize"))

    if looks_like_small_talk(question):
        context, citations = "", []
    elif is_summary_request:
        # Resumo de documento precisa de mais cobertura do mesmo PDF.
        context, citations = get_relevant_chunks_with_meta(
            question,
            k=10,
            max_chars=6500,
            max_per_source=12,
            mode="summary",
        )
    else:
        context, citations = get_relevant_chunks_with_meta(question)

    cfg = load_system_config()
    system_prompt = cfg.get("system_prompt") or ATHENA_SYSTEM_PROMPT
    directives = load_feedback_directives(settings.FEEDBACK_DIRECTIVES_LIMIT)
    if looks_like_small_talk(question):
        answer_mode = "PADRAO"
    elif any(key in lowered for key in ("detalhe", "detalhar", "expandir", "aprofund", "explique mais")):
        answer_mode = "DETALHADO"
    elif is_summary_request:
        answer_mode = "RESUMO"
    else:
        answer_mode = "PADRAO"

    system_parts = [
        f"MODO DE RESPOSTA: {answer_mode}\n",
        system_prompt,
        ("\n\n--- FORMATO DE SAIDA (RESUMO) ---\n" + _SUMMARY_TEMPLATE) if answer_mode == "RESUMO" else "",
        "\n\n--- CONTEXTO DAS POLITICAS ---\n"
        + (context or "Nenhum trecho relevante de politica foi encontrado para esta pergunta."),
    ]
    if directives:
        directives_block = "\n".join(f"- {text}" for text in directives if text.strip())
        system_parts.append("\n\n--- AJUSTES APROVADOS PELA ADMINISTRACAO ---\n" + directives_block)

    system_content = "".join(system_parts)

    history_for_llm = history
    if answer_mode == "RESUMO":
        # Resumo deve focar no documento, então reduzimos influência de respostas anteriores.
        history_for_llm = [m for m in history if m.get("role") == "user"][-4:]
    elif looks_like_small_talk(question):
        history_for_llm = [m for m in history if m.get("role") == "user"][-2:]
    else:
        history_for_llm = history[-20:]

    history_for_llm = _dedupe_consecutive_messages(history_for_llm)
    if answer_mode == "RESUMO":
        # Mantém só as 2 últimas perguntas únicas para evitar prompt gigante.
        history_for_llm = history_for_llm[-2:]

    messages = [{"role": "system", "content": system_content}] + history_for_llm

    if looks_like_small_talk(question):
        temp = 0.4
        top_p = 1.0
        max_tokens = 220
    elif is_summary_request:
        temp = min(cfg.get("temperature", 0.25), 0.15)
        top_p = min(cfg.get("top_p", 1.0), 0.9)
        max_tokens = 750
    else:
        temp = cfg.get("temperature", 0.25)
        top_p = cfg.get("top_p", 1.0)
        max_tokens = 900 if answer_mode == "DETALHADO" else 650

    result = call_llm_api_with_limits(messages, temperature=temp, top_p=top_p, max_tokens=max_tokens)
    cleaned = _clean_response_text(result["content"])
    if answer_mode == "RESUMO" and not any(k in lowered for k in ("hash", "sha256", "assinatura", "clicksign")):
        cleaned = _remove_document_metadata(cleaned)
    result["content"] = _append_sources(cleaned, citations)
    result["sources"] = citations
    return result
