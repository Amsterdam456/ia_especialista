import os
from pathlib import Path
from typing import List, Dict

from sqlalchemy.orm import Session

from app.core.config import settings
from app.db.session import get_session
from app.models import PolicyFile
from app.services.embeddings import reset_embeddings, store_embeddings
from app.services.parser import extract_text_from_file

# Diretório final onde os PDFs são salvos
BASE_DIR = Path(__file__).resolve().parent.parent.parent
POLICY_DIR = BASE_DIR / settings.POLICY_DIR


# -----------------------------------------------------------------------------
# NOVO: Chunks muito mais eficientes + metadados
# -----------------------------------------------------------------------------
def split_into_chunks_with_metadata(
    pages: List[str],
    chunk_size: int = 450,
    overlap: int = 100,
    source_name: str = "",
) -> List[Dict]:
    """
    Divide cada página em blocos menores com metadados:
    { text, source, page, order }
    """

    results = []
    order = 0

    for page_index, page_text in enumerate(pages, start=1):

        cleaned = "\n".join(
            line.strip() for line in page_text.splitlines() if line.strip()
        )

        if not cleaned:
            continue

        start = 0
        length = len(cleaned)

        while start < length:
            end = start + chunk_size
            chunk = cleaned[start:end].strip()
            if chunk:
                results.append({
                    "text": chunk,
                    "source": source_name,
                    "page": page_index,
                    "order": order,
                })
                order += 1

            start = end - overlap

    return results


# -----------------------------------------------------------------------------
# PROCESSAMENTO PRINCIPAL
# -----------------------------------------------------------------------------
def ingest_all_policies():
    """Processa TODOS os PDFs com metadados e atualiza o banco."""
    print("[ingest] Iniciando processamento das políticas...")

    POLICY_DIR.mkdir(exist_ok=True, parents=True)

    # Zerar embeddings antes de reprocessar tudo
    reset_embeddings()

    db: Session = next(get_session())
    processed_files = 0

    for filename in os.listdir(POLICY_DIR):

        if filename.startswith("."):
            continue

        file_path = POLICY_DIR / filename
        print(f"[ingest] Processando: {filename}")

        # Buscar registro no banco
        policy = (
            db.query(PolicyFile)
            .filter(PolicyFile.filename == filename)
            .first()
        )

        if not policy:
            print(f"[ingest] AVISO: {filename} não está registrado no banco. Ignorando.")
            continue

        try:
            # Agora text = lista de páginas (parser será atualizado para isso)
            pages = extract_text_from_file(file_path)

            if not pages or not any(p.strip() for p in pages):
                print(f"[ingest] AVISO: {filename} não contém texto extraído!")
                policy.embedding_status = "error"
                policy.embedding_last_error = "Nenhum texto extraído"
                db.add(policy)
                continue

            chunks = split_into_chunks_with_metadata(
                pages=pages,
                source_name=filename,
            )

            print(f"[ingest] {len(chunks)} chunks gerados para {filename}")

            # Agora passamos chunks estruturados
            store_embeddings(chunks)

            # Atualizar status
            policy.embedding_status = "completed"
            policy.embedding_last_error = None
            db.add(policy)
            processed_files += 1

        except Exception as e:
            print(f"[ingest] ERRO ao processar {filename}: {e}")
            policy.embedding_status = "error"
            policy.embedding_last_error = str(e)
            db.add(policy)
            continue

    db.commit()
    db.close()

    print(f"[ingest] Processo de ingestão concluído! {processed_files} arquivos processados.")
