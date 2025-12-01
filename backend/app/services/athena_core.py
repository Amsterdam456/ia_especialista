"""Stub de resposta da ATHENA para integração inicial."""

from typing import Dict


def athena_answer(question: str) -> Dict:
    return {
        "answer": (
            "Ainda estou na versao inicial (stub), mas em breve estarei conectado "
            "aos dados internos da Estacio. "
            f"Voce perguntou: '{question}'.\n\n"
            "Na proxima fase, vou buscar nos data lakes e retornar analises, riscos e recomendacoes."
        ),
        "meta": {"source": "athena_stub", "confidence": 0.42},
    }
