import time
from collections import defaultdict, deque
from fastapi import HTTPException
from app.config import RATE_LIMIT_REQUESTS, RATE_LIMIT_WINDOW_SECONDS

class InMemoryRateLimiter:
    """Simple per-process sliding-window request limiter."""

    def __init__(self):
        self.events = defaultdict(deque)

    def check(self, key: str):
        now = time.monotonic()
        events = self.events[key]
        cutoff = now - RATE_LIMIT_WINDOW_SECONDS
        while events and events[0] <= cutoff:
            events.popleft()
        if len(events) >= RATE_LIMIT_REQUESTS:
            raise HTTPException(
                status_code=429,
                detail="Rate limit reached. Please wait before trying again.",
                headers={"Retry-After": str(RATE_LIMIT_WINDOW_SECONDS)},
            )
        events.append(now)

limiter = InMemoryRateLimiter()
