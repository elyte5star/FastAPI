from starlette.middleware.base import BaseHTTPMiddleware
import time
from typing import Callable
from starlette.requests import Request
from starlette.types import ASGIApp, Message, Scope, Receive, Send
from starlette.exceptions import HTTPException


class CustomHeaderMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: Callable):
        start_time = time.perf_counter()
        response = await call_next(request)
        process_time = time.perf_counter() - start_time
        response.headers["X-Process-Time"] = str(process_time)
        response.headers["path"] = request.url.path
        return response


class ASGIMiddleware:
    def __init__(self, app: ASGIApp) -> None:
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            return await self.app(scope, receive, send)

        async def send_wrapper(message: Message) -> None:
            # ... Do something
            print("Things are happening")
            await send(message)

        await self.app(scope, receive, send_wrapper)
