from starlette.middleware.base import BaseHTTPMiddleware
import time


class CustomHeaderMiddleware(BaseHTTPMiddleware):
    async def add_process_time_header(self, request, call_next):
        start_time = time.perf_counter()
        response = await call_next(request)
        process_time = time.perf_counter() - start_time
        response.headers["X-Process-Time"] = str(process_time)
        response.headers["root_path"] = request.scope.get('root_path')
        return response
