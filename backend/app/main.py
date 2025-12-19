from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

import threading
import time

from app.core.config import settings
from app.db.database import Base, engine
from app.db.init_db import init_db
from app import models  # noqa: F401 ensures models are registered
from app.routes import admin, auth, chats, athena
from app.services.ingest import ingest_all_policies
from app.core.watcher import start_policy_watcher


def create_app() -> FastAPI:
    app = FastAPI(
        title=f"{settings.PROJECT_NAME} API",
        version="1.0.0",
    )

    # CORS
    allowed_origins = [o.strip() for o in settings.CORS_ORIGINS.split(",") if o.strip()] or ["*"]
    allow_credentials = "*" not in allowed_origins
    app.add_middleware(
        CORSMiddleware,
        allow_origins=allowed_origins,
        allow_credentials=allow_credentials,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.middleware("http")
    async def security_headers(request: Request, call_next):
        start = time.perf_counter()
        response = await call_next(request)
        elapsed_ms = (time.perf_counter() - start) * 1000
        response.headers.setdefault("X-Response-Time", f"{elapsed_ms:.0f}ms")
        if elapsed_ms > 1500:
            print(f"[slow] {request.method} {request.url.path} {elapsed_ms:.0f}ms")
        response.headers.setdefault("X-Content-Type-Options", "nosniff")
        response.headers.setdefault("X-Frame-Options", "DENY")
        response.headers.setdefault("Referrer-Policy", "no-referrer")
        return response

    # HTTP error handler
    @app.exception_handler(HTTPException)
    async def http_exception_handler(request: Request, exc: HTTPException):
        return JSONResponse(
            status_code=exc.status_code,
            content={"success": False, "data": None, "error": exc.detail},
        )

    # Generic error handler
    @app.exception_handler(Exception)
    async def unhandled_exception_handler(request: Request, exc: Exception):
        return JSONResponse(
            status_code=500,
            content={"success": False, "data": None, "error": "Erro interno do servidor"},
        )

    # Create DB tables
    Base.metadata.create_all(bind=engine)

    # Startup events
    @app.on_event("startup")
    def _startup():
        init_db()
        ingest_all_policies()
        # Start watcher in background thread to reprocess policies/finance periodically
        threading.Thread(target=start_policy_watcher, daemon=True).start()

    # Routers
    api_prefix = settings.API_V1_PREFIX
    app.include_router(auth.router, prefix=api_prefix, tags=["Auth"])
    app.include_router(chats.router, prefix=api_prefix, tags=["Chats"])
    app.include_router(admin.router, prefix=api_prefix, tags=["Admin"])
    app.include_router(athena.router, prefix=api_prefix, tags=["Athena"])

    return app


app = create_app()
