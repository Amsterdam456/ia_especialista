import os
from pathlib import Path
from app.services.parser import extract_text_from_file
from app.services.embeddings import store_embeddings
from app.services.ingest import split_into_chunks

BASE_DIR = Path(__file__).resolve().parent.parent.parent
POLICY_DIR = BASE_DIR / "policies"


def ingest_all_policies():
    print("📘 Iniciando processamento das políticas...")

    POLICY_DIR.mkdir(exist_ok=True)

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
