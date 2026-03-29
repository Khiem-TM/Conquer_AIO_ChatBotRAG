from __future__ import annotations

import time
from collections import deque, defaultdict
from fastapi import Header, HTTPException, status

from app.shared.configs import settings

_request_log: dict[str, deque[float]] = defaultdict(deque)


def require_local_api_key(x_api_key: str | None = Header(default=None)) -> None:
    expected = settings.local_api_key.strip()
    if not expected:
        return
    if x_api_key != expected:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Invalid API key')


def check_rate_limit(client_id: str) -> None:
    limit = max(1, settings.local_rate_limit_per_minute)
    now = time.time()
    q = _request_log[client_id]
    while q and now - q[0] > 60:
        q.popleft()
    if len(q) >= limit:
        raise HTTPException(status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail='Rate limit exceeded')
    q.append(now)
