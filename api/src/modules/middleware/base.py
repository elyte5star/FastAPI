from starlette.middleware.base import BaseHTTPMiddleware
import time
from typing import Callable
from starlette.requests import Request
from starlette.exceptions import HTTPException
from starlette.responses import Response
from fastapi import status


class CustomHeaderMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: Callable):
        start_time = time.perf_counter()
        response = await call_next(request)
        process_time = time.perf_counter() - start_time
        response.headers["X-Process-Time"] = str(process_time)
        response.headers["path"] = request.url.path
        return response


class TokenBucket:
    def __init__(self, tokens, refill_rate) -> None:
        self.tokens = tokens
        self.refill_rate = refill_rate
        self.bucket = tokens
        self.last_refill = time.time()

    def check(self) -> bool:
        current = time.time()
        time_passed = current - self.last_refill
        self.last_refill = current
        self.bucket = self.bucket + time_passed * (self.tokens / self.refill_rate)
        if self.bucket > self.tokens:
            self.bucket = self.tokens
        if self.bucket < 1:
            print("Packet Dropped")
            return False
        self.bucket = self.bucket - 1
        print("Packet Forwarded")
        return True


# The request per second
bucket = TokenBucket(3, 1)


class RateLimiter(BaseHTTPMiddleware):
    def __init__(self, app):
        super().__init__(app)
        self.bucket = bucket

    async def default_callback(self, request: Request, response: Response):

        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too Many Requests",
        )
