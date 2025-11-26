# app/services/embeddings.py

import os
import numpy as np
import pickle
from sentence_transformers import SentenceTransformer

from app.core.config import settings

MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"

# Carrega o modelo global uma única vez
model = SentenceTransformer(MODEL_NAME)

EMBEDDINGS_FILE = settings.EMBEDDINGS_FILE

# Estrutura em memória
emb_store = []  # [{"text": "...", "embedding": np.array([...]), "source": "..."}]


def reset_embeddings():
    """Limpa o armazenamento em memória e remove o arquivo persistido."""
    global emb_store
    emb_store = []

    if os.path.exists(EMBEDDINGS_FILE):
        os.remove(EMBEDDINGS_FILE)


def store_embeddings(text_chunks, source_name: str):
    """
    Recebe blocos de texto e salva embeddings no arquivo e na memória.
    """
    global emb_store

    for chunk in text_chunks:
        if not chunk.strip():
            continue

        embedding = model.encode(chunk, convert_to_numpy=True)
        emb_store.append(
            {
                "text": chunk,
                "embedding": embedding,
                "source": source_name,
            }
        )

    # Garante que a pasta exista
    os.makedirs(os.path.dirname(EMBEDDINGS_FILE) or "data", exist_ok=True)

    with open(EMBEDDINGS_FILE, "wb") as f:
        pickle.dump(emb_store, f)


def load_embeddings():
    """
    Carrega o arquivo embeddings.pkl na memória.
    """
    global emb_store

    if os.path.exists(EMBEDDINGS_FILE):
        with open(EMBEDDINGS_FILE, "rb") as f:
            emb_store = pickle.load(f)
    else:
        emb_store = []


def _cosine_similarity(a: np.ndarray, b: np.ndarray) -> float:
    """
    Similaridade de cosseno entre dois vetores numpy.
    """
    denom = (np.linalg.norm(a) * np.linalg.norm(b)) + 1e-8
    return float(np.dot(a, b) / denom)


def search_similar_documents(query: str, k: int = 3):
    """
    Busca os textos mais similares ao prompt do usuário.
    Retorna uma lista de dicionários:
    [
      {"text": "...", "source": "Auditoria.pdf", "score": 0.87},
      ...
    ]
    """
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
                "score": score,
            }
        )

    scored.sort(key=lambda x: x["score"], reverse=True)

    return scored[:k]
