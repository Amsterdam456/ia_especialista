import os
import hashlib
import json
from pathlib import Path
from typing import List, Dict

from sqlalchemy.orm import Session

from app.core.config import settings
from app.db.session import get_session
from app.models import PolicyFile
from app.services.embeddings import (
    build_semantic_metadata,
    load_embeddings,
    remove_embeddings_for_source,
    store_embeddings,
)
from app.services.parser import extract_text_from_file

# Diretório final onde os PDFs são salvos
BASE_DIR = Path(__file__).resolve().parent.parent.parent
POLICY_DIR = BASE_DIR / settings.POLICY_DIR
META_FILE = BASE_DIR / "data/embeddings_meta.json"
EMBEDDINGS_SCHEMA_VERSION = 2


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
    Divide cada página em blocos menores com metadados genéricos:
    { text, source, page, order, category, role, topic }
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
                category, role, topic, _doc_type = build_semantic_metadata(chunk, source_name, page_index)
                results.append({
                    "text": chunk,
                    "source": source_name,
                    "page": page_index,
                    "order": order,
                    "category": category,
                    "role": role,
                    "topic": topic,
                })
                order += 1

            start = end - overlap

    return results


# -----------------------------------------------------------------------------
# PROCESSAMENTO PRINCIPAL (incremental)
# -----------------------------------------------------------------------------
def ingest_all_policies():
    """Processa PDFs/DOCX/TXT com metadados e atualiza o banco de forma incremental."""
    print("[ingest] Iniciando processamento das políticas...")

    POLICY_DIR.mkdir(exist_ok=True, parents=True)
    load_embeddings()

    meta_version, meta = _load_meta()
    if meta_version != EMBEDDINGS_SCHEMA_VERSION:
        # Força reprocessamento quando o pipeline de embeddings muda.
        meta = {}
    updated_meta: dict[str, str] = {}

    db: Session = next(get_session())
    processed_files = 0

    current_files = [f for f in os.listdir(POLICY_DIR) if not f.startswith(".")]

    for filename in current_files:
        file_path = POLICY_DIR / filename
        file_hash = _file_hash(file_path)
        updated_meta[filename] = file_hash

        print(f"[ingest] Verificando: {filename}")

        policy = (
            db.query(PolicyFile)
            .filter(PolicyFile.filename == filename)
            .first()
        )

        if not policy:
            print(f"[ingest] AVISO: {filename} não está registrado no banco. Ignorando.")
            continue

        # Skip se hash não mudou e status está ok
        if meta.get(filename) == file_hash and policy.embedding_status == "completed":
            print(f"[ingest] {filename} sem mudanças. Pulando reprocessamento.")
            continue

        # Limpar embeddings antigos do arquivo
        remove_embeddings_for_source(filename)

        try:
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

            store_embeddings(chunks)

            policy.embedding_status = "completed"
            policy.embedding_last_error = None
            db.add(policy)
            processed_files += 1

        except Exception as e:  # noqa: BLE001
            print(f"[ingest] ERRO ao processar {filename}: {e}")
            policy.embedding_status = "error"
            policy.embedding_last_error = str(e)
            db.add(policy)
            continue

    # Remover embeddings de arquivos que foram apagados
    removed_files = set(meta.keys()) - set(current_files)
    for fname in removed_files:
        print(f"[ingest] Removendo embeddings de arquivo ausente: {fname}")
        remove_embeddings_for_source(fname)

    _save_meta(updated_meta)

    db.commit()
    db.close()

    print(f"[ingest] Processo de ingestão concluído! {processed_files} arquivos processados.")


def _file_hash(path: Path) -> str:
    hasher = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            hasher.update(chunk)
    return hasher.hexdigest()


def _load_meta() -> tuple[int, dict]:
    if META_FILE.exists():
        try:
            raw = json.loads(META_FILE.read_text(encoding="utf-8"))
            # Compatibilidade:
            # - formato antigo: { "arquivo.pdf": "sha256...", ... }
            # - formato novo: { "_schema_version": 2, "hashes": { ... } }
            if isinstance(raw, dict) and "hashes" in raw:
                return int(raw.get("_schema_version") or 1), dict(raw.get("hashes") or {})
            return 1, raw if isinstance(raw, dict) else {}
        except Exception:
            return 1, {}
    return 1, {}


def _save_meta(meta: dict) -> None:
    META_FILE.parent.mkdir(parents=True, exist_ok=True)
    payload = {"_schema_version": EMBEDDINGS_SCHEMA_VERSION, "hashes": meta}
    META_FILE.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def get_ingest_status(db: Session | None = None) -> dict:
    meta_version, meta = _load_meta()
    stats = {"schema_version": meta_version, "files_hashed": len(meta), "hashes": meta}
    if db:
        total = db.query(PolicyFile).count()
        pending = db.query(PolicyFile).filter(PolicyFile.embedding_status != "completed").count()
        stats["db_total"] = total
        stats["db_pending"] = pending
    return stats
