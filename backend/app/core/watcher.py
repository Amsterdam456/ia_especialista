# app/core/watcher.py

import hashlib
import os
import time
from datetime import datetime
from pathlib import Path

from app.core.config import settings
from app.services.ingest import ingest_all_policies, POLICY_DIR


HASH_FILE = POLICY_DIR / ".last_hash"
CHECK_INTERVAL_SECONDS = settings.CHECK_INTERVAL_SECONDS


def calculate_policies_hash() -> str | None:
    """
    Calcula um hash (sha256) de todos os arquivos de políticas.
    Ignora arquivos ocultos e o próprio .last_hash.
    """
    if not POLICY_DIR.exists():
        return None

    hasher = hashlib.sha256()

    for root, dirs, files in os.walk(POLICY_DIR):
        # Ignora diretórios ocultos
        dirs[:] = [d for d in dirs if not d.startswith(".")]

        for fname in sorted(files):
            if fname.startswith("."):
                continue

            path = Path(root) / fname
            rel = path.relative_to(POLICY_DIR)

            hasher.update(str(rel).encode("utf-8"))

            with open(path, "rb") as f:
                while True:
                    chunk = f.read(8192)
                    if not chunk:
                        break
                    hasher.update(chunk)

    return hasher.hexdigest()


def load_last_hash() -> str | None:
    try:
        return HASH_FILE.read_text(encoding="utf-8").strip()
    except FileNotFoundError:
        return None


def save_last_hash(value: str | None):
    if value is None:
        return
    HASH_FILE.write_text(value, encoding="utf-8")


def start_policy_watcher():
    print("🔍 ATHENA WATCHER iniciado (checagem 1x/dia)")

    while True:
        print(f"\n[{datetime.now()}] ⏳ Executando checagem diária...")

        current_hash = calculate_policies_hash()
        last_hash = load_last_hash()

        if current_hash and current_hash != last_hash:
            print("📄 Mudança detectada nos arquivos de políticas!")
            print("🔁 Reprocessando políticas e atualizando IA...")

            ingest_all_policies()
            save_last_hash(current_hash)

            print("✅ IA atualizada com sucesso!")

        time.sleep(CHECK_INTERVAL_SECONDS)
