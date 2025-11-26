from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import threading
from dotenv import load_dotenv

load_dotenv()

from app.core.config import settings
from app.api.v1 import router as api_router
from app.routes.athena import router as athena_router
from app.routes.auth import router as auth_router
from app.routes.chats import router as chat_router
from app.routes.admin import router as admin_router
from app.services.ingest import ingest_all_policies
from app.core.watcher import (
    start_policy_watcher,
    calculate_policies_hash,
    save_last_hash,
)
from app.db.database import Base, engine, SessionLocal
from app.db.init_db import ensure_admin_user

app = FastAPI(
    title="Athena Specialist IA",
    version="0.1.0",
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Rotas da API v1 (stub antigo)
app.include_router(api_router, prefix=settings.API_V1_PREFIX)

# Rotas da IA de verdade (RAG)
app.include_router(athena_router, prefix="/athena")

# Autenticação e chat multi-conversas
app.include_router(auth_router)
app.include_router(chat_router)
app.include_router(admin_router)


@app.on_event("startup")
def startup_event():
    # Banco e usuário admin
    Base.metadata.create_all(bind=engine)
    with SessionLocal() as db:
        ensure_admin_user(db)

    # Inicializa embeddings atuais antes de iniciar o watcher em segundo plano
    ingest_all_policies()
    save_last_hash(calculate_policies_hash())

    watcher_thread = threading.Thread(target=start_policy_watcher, daemon=True)
    watcher_thread.start()
