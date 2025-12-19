import time
from typing import Dict, Tuple

from fastapi import HTTPException, Request, status

from app.core.config import settings

# Limite simples em memoria por IP+rota
_hits: Dict[Tuple[str, str], list[float]] = {}


def rate_limit(request: Request, *, limit: int | None = None, window_seconds: int | None = None) -> None:
    resolved_limit = limit or settings.RATE_LIMIT_MAX_REQUESTS
    resolved_window = window_seconds or settings.RATE_LIMIT_WINDOW_SECONDS

    ip = request.client.host if request.client else "unknown"
    key = (ip, request.url.path)
    now = time.time()

    window_start = now - resolved_window
    history = _hits.get(key, [])
    history = [ts for ts in history if ts >= window_start]

    if len(history) >= resolved_limit:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Muitas requisicoes, tente novamente em instantes.",
        )

    history.append(now)
    _hits[key] = history
