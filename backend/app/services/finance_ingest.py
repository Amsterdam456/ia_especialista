import csv
import json
import shutil
from datetime import datetime
from pathlib import Path
from typing import Any, Dict

from app.core.config import settings

MONTH_KEYS = [f"M{idx:02d}" for idx in range(1, 13)]
MONTH_NAMES = ["Jan", "Fev", "Mar", "Abr", "Mai", "Jun", "Jul", "Ago", "Set", "Out", "Nov", "Dez"]
CACHE_FILE = Path("data/finance_cache.json")


def _norm(val: Any) -> str:
    return str(val or "").strip()


def parse_line(row: Dict[str, Any]):
    conta_desc = _norm(row.get("Conta_Descricao") or row.get("Nome_Conta"))
    meses = {}
    total = 0
    for idx, key in enumerate(MONTH_KEYS):
        raw = row.get(key)
        try:
            v = float(raw) if raw not in ("", None, "NULL") else 0.0
        except Exception:
            v = 0.0
        meses[MONTH_NAMES[idx]] = v
        total += v

    mes_atual = datetime.now().month
    ytd = sum(list(meses.values())[:mes_atual])

    return {
        "ano": _norm(row.get("Ano")),
        "cenario": _norm(row.get("Cenario")).lower(),
        "natureza": _norm(row.get("Natureza")),
        "agregador_conta": _norm(row.get("Agregador_Conta")),
        "bu_mercado": _norm(row.get("BU_Mercado")),
        "pacote": _norm(row.get("Pacote")),
        "nome_conta": conta_desc,
        "conta_descricao": conta_desc,
        "meses": meses,
        "ytd": ytd,
    }


def ingest_finance_csv():
    path = Path(settings.FINANCE_CSV_PATH)
    if not path.exists():
        print("ERRO: CSV nao encontrado.")
        return False

    raw = []
    with path.open("r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            parsed = parse_line(row)
            raw.append(parsed)

    CACHE_FILE.parent.mkdir(exist_ok=True, parents=True)
    with CACHE_FILE.open("w", encoding="utf-8") as f:
        json.dump({"raw": raw}, f)

    print("[finance_ingest] Pivot salva com", len(raw), "linhas.")
    return True


def upload_finance_csv(temp_path: Path):
    dest = Path(settings.FINANCE_CSV_PATH)
    dest.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy(temp_path, dest)
    return ingest_finance_csv()


def load_pivot_cache():
    if CACHE_FILE.exists():
        return json.load(CACHE_FILE.open("r", encoding="utf-8"))
    return {}
