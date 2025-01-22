import logging
import sys
from logging.handlers import TimedRotatingFileHandler
from starlette.middleware.base import BaseHTTPMiddleware
from fastapi import status, FastAPI
from fastapi.responses import JSONResponse
from fastapi.encoders import jsonable_encoder

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
            response = await call_next(request)
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
