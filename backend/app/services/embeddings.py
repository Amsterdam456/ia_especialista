import os
import pickle
from typing import Dict, List

import numpy as np
from sentence_transformers import SentenceTransformer

from app.core.config import settings

MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"
model = SentenceTransformer(MODEL_NAME)

EMBEDDINGS_FILE = settings.EMBEDDINGS_FILE

# Estrutura em memória
emb_store: List[Dict] = []


# --------------------------
# HELPERS
# --------------------------

def reset_embeddings() -> None:
    """Limpa vetorizações em memória e arquivo."""
    global emb_store
    emb_store = []

    if os.path.exists(EMBEDDINGS_FILE):
        os.remove(EMBEDDINGS_FILE)


def store_embeddings(text_chunks: List[Dict]) -> None:
    """
    Recebe uma lista de chunks no formato:
    {
        "text": "...",
        "source": "...",
        "page": 3,
        "order": 10
    }
    """
    global emb_store

    for item in text_chunks:
        text = item["text"].strip()
        if not text:
            continue

        emb = model.encode(text, convert_to_numpy=True)

        emb_store.append(
            {
                "text": text,
                "embedding": emb,
                "source": item["source"],
                "page": item["page"],
                "order": item["order"],
            }
        )

    # Persistência
    os.makedirs(os.path.dirname(EMBEDDINGS_FILE) or "data", exist_ok=True)
    with open(EMBEDDINGS_FILE, "wb") as f:
        pickle.dump(emb_store, f)


def load_embeddings() -> None:
    """Carrega embeddings do disco."""
    global emb_store

    if os.path.exists(EMBEDDINGS_FILE):
        with open(EMBEDDINGS_FILE, "rb") as f:
            emb_store = pickle.load(f)
    else:
        emb_store = []


def _cosine_similarity(a: np.ndarray, b: np.ndarray) -> float:
    denom = (np.linalg.norm(a) * np.linalg.norm(b)) + 1e-8
    return float(np.dot(a, b) / denom)


def search_similar_documents(query: str, k: int = 5) -> List[Dict]:
    """Retorna os K chunks mais similares com metadados completos."""
    if not emb_store:
        load_embeddings()

    if not emb_store:
        return []

    query_emb = model.encode(query, convert_to_numpy=True)
    scored = []

    for item in emb_store:
        score = _cosine_similarity(query_emb, item["embedding"])

        scored.append(
            {
                "text": item["text"],
                "source": item["source"],
                "page": item["page"],
                "order": item["order"],
                "score": score,
            }
        )

    scored.sort(key=lambda x: x["score"], reverse=True)
    return scored[:k]


def get_relevant_chunks(query: str, k: int = 3, max_chars: int = 4000) -> str:
    """Retorna os melhores trechos formatados para o modelo, com limite de tamanho."""
    matches = search_similar_documents(query, k)

    if not matches:
        return ""

    formatted: list[str] = []
    total_chars = 0
    for m in matches:
        snippet = f"[Documento: {m['source']} | Pagina {m['page']}] Trecho:\n{m['text']}"
        total_chars += len(snippet)
        formatted.append(snippet)
        if total_chars >= max_chars:
            break

    return "\n\n".join(formatted)
