import logging
import sys
from logging.handlers import TimedRotatingFileHandler
from starlette.middleware.base import BaseHTTPMiddleware
from fastapi import status, FastAPI, Request
from fastapi.responses import JSONResponse, Response
from fastapi.encoders import jsonable_encoder
from typing import Callable
import json

FORMATTER = logging.Formatter(
    "%(levelname)s :: %(asctime)s :: %(name)s :: %(funcName)s :: %(message)s"
)


def get_console_handler():
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(FORMATTER)
    return console_handler


def get_file_handler(filename: str):
    file_handler = TimedRotatingFileHandler(filename, when="midnight")
    file_handler.setFormatter(FORMATTER)
    return file_handler


def get_logger(filename: str, logger_name: str = __name__) -> logging.Logger:
    logger = logging.getLogger(logger_name)

    logger.setLevel(logging.DEBUG)  # better to have too much log than not enough

    logger.addHandler(get_console_handler())
    logger.addHandler(get_file_handler(filename))
    # with this pattern, it's rarely necessary to propagate the error up to parent
    logger.propagate = False

    return logger


class AsyncIteratorWrapper:
    """The following is a utility class that transforms a
    regular iterable to an asynchronous one.

    link: https://www.python.org/dev/peps/pep-0492/#example-2
    """

    def __init__(self, obj):
        self._it = iter(obj)

    def __aiter__(self):
        return self

    async def __anext__(self):
        try:
            value = next(self._it)
        except StopIteration:
            raise StopAsyncIteration
        return value


class LoggerMiddleWare(BaseHTTPMiddleware):
    def __init__(
        self,
        app: FastAPI,
        log_level=logging.NOTSET,
        file_path=None,
    ):
        super().__init__(app)
        self.file_path = file_path
        self._log_level = log_level
        self.logger = logging.getLogger(self.__class__.__name__)
        self.logger.setLevel(self._log_level)
        self.logger.addHandler(get_console_handler())
        self.logger.addHandler(get_file_handler(self.file_path))

    async def dispatch(self, request, call_next):
        try:
            # response = await call_next(request)
            request_dict = await self._log_request(request)
            response, response_dict = await self._log_response(call_next, request)
            logging_dict = {"request": request_dict, "response": response_dict}
            self.logger.info(logging_dict)
            return response
        except RuntimeError as exc:
            if (
                str(exc) == "No response returned."
            ) and await request.is_disconnected():
                return JSONResponse(
                    status_code=status.HTTP_204_NO_CONTENT,
                    content=jsonable_encoder(
                        {
                            "message": str(exc.errors()),
                            "body": exc.body,
                            "success": False,
                        }
                    ),
                )
            raise

    async def _log_request(self, request: Request) -> dict:
        url_path = request.url.path
        if request.query_params:
            url_path += f"?{request.query_params}"
        ip = ""
        xf_header = request.headers.get("X-Forwarded-For")
        if xf_header is not None:
            ip = xf_header.split(",")[0]
        else:
            ip = request.client.host
        request_logging_dict = {
            "method": request.method,
            "path": url_path,
            "ip": ip,
        }
        return request_logging_dict

    async def _log_response(
        self, call_next: Callable, request: Request
    ) -> tuple[Response, dict]:
        response: Response = await call_next(request)
        overall_status = "successful" if response.status_code < 400 else "failed"
        response_logging = {
            "status": overall_status,
            "status_code": response.status_code,
        }
        resp_body = [section async for section in response.__dict__["body_iterator"]]
        response.__setattr__("body_iterator", AsyncIteratorWrapper(resp_body))
        try:
            resp_body = json.loads(resp_body[0].decode())
        except Exception:
            resp_body = str(resp_body)

        # response_logging["body"] = resp_body
        return response, response_logging
