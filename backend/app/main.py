from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import threading
from dotenv import load_dotenv
load_dotenv()

from app.core.config import settings
from app.api.v1 import router as api_router
from app.routes.athena import router as athena_router
from app.core.watcher import start_policy_watcher

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


@app.on_event("startup")
def startup_event():
    watcher_thread = threading.Thread(target=start_policy_watcher, daemon=True)
    watcher_thread.start()
