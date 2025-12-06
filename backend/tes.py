from app.services.finance_ingest import ingest_finance_csv


if __name__ == "__main__":
    print("Iniciando ingestão da pivot (com progresso a cada 10k linhas)...")
    ok = ingest_finance_csv(verbose=True)
    print("Ingestão finalizada:", ok)
