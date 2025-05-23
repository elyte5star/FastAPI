from starlette.middleware.base import BaseHTTPMiddleware
import time
from typing import Callable
from starlette.requests import Request
from starlette.responses import JSONResponse
from fastapi import status, FastAPI
from modules.settings.configuration import ApiConfig


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
        self.last_refill = time.perf_counter()

    def check(self) -> bool:
        current = time.perf_counter()
        time_passed = current - self.last_refill
        self.last_refill = current
        self.bucket = self.bucket + time_passed * (self.tokens / self.refill_rate)
        if self.bucket > self.tokens:
            self.bucket = self.tokens
        if self.bucket < 1:
            return False
        self.bucket = self.bucket - 1
        return True


class RateLimiterMiddleware(BaseHTTPMiddleware):
    def __init__(self, app: FastAPI, config: ApiConfig):
        super().__init__(app)
        self.bucket = TokenBucket(2, 2) # 2 request per 2 second
        self.config = config

    async def dispatch(self, request, call_next):
        if self.bucket.check():
            response = await call_next(request)
            return response
        self.config.logger.warning("Request packet dropped")
        return JSONResponse(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            content={
                "message": "Too many Requests",
                "success": False,
            },
        )
