import hashlib
import os
import time
from datetime import datetime
from pathlib import Path

from app.core.config import settings
from app.services.ingest import ingest_all_policies, POLICY_DIR
from app.services.finance_ingest import ingest_finance_csv

HASH_FILE = POLICY_DIR / ".last_hash"
CHECK_INTERVAL_SECONDS = settings.CHECK_INTERVAL_SECONDS
_running = False


def calculate_policies_hash() -> str | None:
    """Calculate a sha256 hash of all policy files."""
    if not POLICY_DIR.exists():
        return None

    hasher = hashlib.sha256()

    for root, dirs, files in os.walk(POLICY_DIR):
        dirs[:] = [d for d in dirs if not d.startswith('.')]

        for fname in sorted(files):
            if fname.startswith('.'):
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
    HASH_FILE.parent.mkdir(parents=True, exist_ok=True)
    HASH_FILE.write_text(value, encoding="utf-8")


def start_policy_watcher():
    """Run an infinite loop that reprocesses policies and ingere CSV financeiro diariamente."""
    global _running
    if _running:
        return
    _running = True
    print("[watcher] ATHENA watcher iniciado (checagem a cada ciclo configurado)")

    # Registrar hash inicial para evitar reprocessar imediatamente após o bootstrap
    initial_hash = calculate_policies_hash()
    if initial_hash:
        save_last_hash(initial_hash)

    last_finance_run = 0.0

    while True:
        print(f"\n[{datetime.now()}] Rodando checagem diaria...")

        current_hash = calculate_policies_hash()
        last_hash = load_last_hash()

        if current_hash and current_hash != last_hash:
            print("[watcher] Mudanca detectada nos arquivos de politicas")
            print("[watcher] Reprocessando politicas e atualizando IA...")

            ingest_all_policies()
            save_last_hash(current_hash)

            print("[watcher] IA atualizada com sucesso!")

        # Ingestão financeira periódica
        now_ts = time.time()
        if now_ts - last_finance_run >= settings.FINANCE_REFRESH_SECONDS:
            print("[watcher] Iniciando ingestão financeira via CSV...")
            ingest_finance_csv()
            last_finance_run = now_ts

        time.sleep(CHECK_INTERVAL_SECONDS)
