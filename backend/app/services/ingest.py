import os
from pathlib import Path
from typing import List

from app.core.config import settings
from app.services.parser import extract_text_from_file
from app.services.embeddings import reset_embeddings, store_embeddings

BASE_DIR = Path(__file__).resolve().parent.parent.parent
POLICY_DIR = BASE_DIR / settings.POLICY_DIR


def split_into_chunks(text: str, chunk_size: int = 800, overlap: int = 120) -> List[str]:
    """Split raw text into overlapping chunks to feed the embedding model.

    Args:
        text: Full text extracted from the policy document.
        chunk_size: Target chunk length (in characters).
        overlap: Number of characters to repeat between consecutive chunks to
            preserve context around the split point.
    """

    cleaned = "\n".join(line.strip() for line in text.splitlines() if line.strip())
    if not cleaned:
        return []

    chunks: List[str] = []
    start = 0
    text_length = len(cleaned)

    while start < text_length:
        end = start + chunk_size
        chunk = cleaned[start:end]
        chunks.append(chunk)
        start = end - overlap

    return chunks


def ingest_all_policies():
    print("📘 Iniciando processamento das políticas...")

    POLICY_DIR.mkdir(exist_ok=True)

    # Evita duplicação de embeddings a cada reinício do serviço
    reset_embeddings()

    for filename in os.listdir(POLICY_DIR):
        if filename.startswith("."):
            continue

        file_path = POLICY_DIR / filename
        print(f"🔹 Processando: {filename}")

        text = extract_text_from_file(file_path)

        if not text.strip():
            print(f"⚠️ Arquivo {filename} não contém texto extraído!")
            continue

        chunks = split_into_chunks(text)
        print(f"🧩 {len(chunks)} chunks gerados para {filename}")

        store_embeddings(chunks, filename)

    print("✨ Processo de ingestão concluído!")
