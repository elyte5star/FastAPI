from starlette.middleware.base import BaseHTTPMiddleware
from fastapi import FastAPI, HTTPException, status
import time


class CustomHeaderMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        start_time = time.perf_counter()
        response = await call_next(request)
        process_time = time.perf_counter() - start_time
        response.headers["X-Process-Time"] = str(process_time)
        response.headers["path"] = request.url.path
        return response


class TokenBucket:

    def __init__(self, tokens, refill_rate, forward_callback, drop_callback):
        self.tokens = tokens
        self.refill_rate = refill_rate
        self.forward_callback = forward_callback
        self.drop_callback = drop_callback
        self.bucket = tokens
        self.last_refill = time.time()

    def handle(self, packet: int):
        current = time.time()
        time_passed = current - self.last_refill
        self.last_refill = current
        self.bucket = self.bucket + time_passed * (self.tokens / self.refill_rate)
        if self.bucket > self.tokens:
            self.bucket = self.tokens
        if self.bucket < 1:
            self.drop_callback(packet)
            return False
        self.bucket = self.bucket - 1
        self.forward_callback(packet)
        return True


def forward(packet):
    print("Packet Forwarded: " + str(packet))


def drop(packet):
    print("Packet Dropped: " + str(packet))


class RateLimiterMiddleware(BaseHTTPMiddleware):
    def __init__(self, app: FastAPI, bucket: TokenBucket):
        super().__init__(app)
        self.bucket = bucket
        self.packet = 0

    async def dispatch(self, request, call_next):
        if self.bucket.handle(self.packet):
            return await call_next(request)

        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too Many Requests",
        )
