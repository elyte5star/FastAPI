from starlette.middleware.base import BaseHTTPMiddleware, DispatchFunction
import time
from typing import Callable, Mapping
from starlette.requests import Request
from fastapi import status
from modules.settings.configuration import ApiConfig
from starlette.types import ASGIApp, Message, Scope, Receive, Send
from starlette.responses import JSONResponse, RedirectResponse
from starlette.datastructures import URL
from starlette.exceptions import HTTPException as StarletteHTTPException


class TokenBucket:
    def __init__(self, tokens: int, refill_rate: int) -> None:
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


# redirections = {
#     "/v1/resource/": "/v2/resource/",
#     # ...
# }


class RedirectsMiddleware:
    def __init__(self, app, path_mapping: dict):
        self.app = app
        self.path_mapping = path_mapping

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        url = URL(scope=scope)

        if url.path in self.path_mapping:
            url = url.replace(path=self.path_mapping[url.path])
            response = RedirectResponse(url, status_code=301)
            await response(scope, receive, send)
            return

        await self.app(scope, receive, send)


class CustomHTTPExceptionMiddleware(StarletteHTTPException):
    def __init__(
        self,
        status_code: int,
        detail: str | None = None,
        headers: Mapping[str, str] | None = None,
    ) -> None:
        super().__init__(status_code, detail, headers)


class RateLimiterMiddleware:
    def __init__(self, app: ASGIApp, config: ApiConfig) -> None:
        self.app = app
        self.bucket = TokenBucket(3, 2)  # 3 request per 2 second
        self.config = config

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if not self.bucket.check() and scope["type"] == "http":
            response = JSONResponse(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                content={
                    "message": "Too many Requests",
                    "success": False,
                },
            )
            self.config.logger.warning("Request packet dropped")
            return await response(scope, receive, send)
        await self.app(scope, receive, send)


class CustomHeaderMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: Callable):
        start_time = time.perf_counter()
        response = await call_next(request)
        process_time = time.perf_counter() - start_time
        response.headers["X-Process-Time"] = str(process_time)
        response.headers["path"] = request.url.path
        return response
