import handler
import logging
from modules.settings.configuration import ApiConfig
from fastapi.logger import logger
from starlette.staticfiles import StaticFiles
from modules.middleware.log import get_file_handler, get_console_handler
from fastapi.encoders import jsonable_encoder
from starlette.exceptions import HTTPException as StarletteHTTPException
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from fastapi import Request, status

cfg = ApiConfig().from_toml_file().from_env_file()
cfg.logger = logger


# Set up logging
logging.basicConfig(
    handlers=[get_console_handler(), get_file_handler(cfg.log_file_path)],
    encoding=cfg.encoding,
    level=cfg.log_type,
)


app = handler.get_application(cfg)


@app.exception_handler(StarletteHTTPException)
async def custom_http_exception_handler(
    request: Request, exc: StarletteHTTPException
) -> JSONResponse:
    logger.warning(f"{repr(exc.detail)}!!")
    return JSONResponse(
        status_code=exc.status_code,
        content=jsonable_encoder({"message": str(exc.detail), "success": False}),
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(
    request: Request, exc: RequestValidationError
) -> JSONResponse:
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content=jsonable_encoder({"message": str(exc.detail), "body": exc.body}),
    )


@app.get("/favicon.ico", include_in_schema=False)
def favicon():
    return StaticFiles(directory="./modules/static")
