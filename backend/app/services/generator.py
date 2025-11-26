# app/services/generator.py

import requests

from app.core.config import settings

LMSTUDIO_API_URL = settings.LMSTUDIO_API_URL
MODEL_NAME = settings.LMSTUDIO_MODEL


def generate_answer(context: str, question: str) -> str:
    """
    Gera resposta usando LM Studio como motor LLM local.
    """

    prompt = f"""
Você é a IA ATHENA, especialista em interpretar políticas internas da Estácio/YDUQS.

Base de conhecimento relevante (RAG):

{context}

Pergunta:
{question}

Responda com extrema precisão, apenas com base no texto acima.
Se a política não cobre o assunto, diga claramente: "Essa política não trata sobre isso."
"""

    body = {
        "model": MODEL_NAME,
        "messages": [
            {"role": "system", "content": "Você é a IA corporativa Athena, objetiva e precisa."},
            {"role": "user", "content": prompt},
        ],
        "temperature": 0.1,
        "max_tokens": 700,
    }

    try:
        resp = requests.post(LMSTUDIO_API_URL, json=body)
        resp.raise_for_status()

        data = resp.json()
        return data["choices"][0]["message"]["content"].strip()

    except Exception as e:
        return f"Erro ao gerar resposta: {e}"
