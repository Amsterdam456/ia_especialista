"""
Aqui ficará o cérebro real do Athena (RAG, embeddings, Oracle, etc.).
Por enquanto, só um stub bonitinho para conectar o front.
"""

from typing import Dict


def athena_answer(question: str) -> Dict:
    # 🔹 Aqui depois vamos chamar FAISS + modelo local + dados Estácio.
    # Por enquanto, devolvemos uma resposta fake bem formatada.
    return {
        "answer": (
            "Ainda estou na versão inicial (stub), mas em breve estarei conectado "
            "aos dados financeiros e de captação da Estácio. "
            f"Você perguntou: '{question}'.\n\n"
            "Na próxima fase, vou buscar nos data lakes internos e retornar "
            "análises, riscos e recomendações detalhadas."
        ),
        "meta": {
            "source": "athena_stub",
            "confidence": 0.42,
        },
    }
