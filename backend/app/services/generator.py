# app/services/generator.py

import os
import requests

LMSTUDIO_API_URL = os.getenv("LMSTUDIO_API_URL", "http://localhost:1234/v1/chat/completions")
MODEL_NAME = os.getenv("LMSTUDIO_MODEL", "phi-3.5-mini-3.8b-arliai-rpmax-v1.1")


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
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.1,
        "max_tokens": 700
    }

    try:
        resp = requests.post(LMSTUDIO_API_URL, json=body)
        resp.raise_for_status()

        data = resp.json()
        return data["choices"][0]["message"]["content"].strip()

    except Exception as e:
        return f"Erro ao gerar resposta: {e}"
