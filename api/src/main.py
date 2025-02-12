import handler
import logging
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

# from starlette.middleware.trustedhost import TrustedHostMiddleware
from starlette.staticfiles import StaticFiles
from modules.middleware.log import (
    info_file_handler,
    get_console_handler,
    smtp_log_handler,
    error_file_handler,
)
from fastapi.encoders import jsonable_encoder
from starlette.exceptions import HTTPException as StarletteHTTPException
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from fastapi import Request, status
from fastapi import FastAPI
from contextlib import asynccontextmanager
from modules.middleware.base import CustomHeaderMiddleware
from modules.security.events.base import APIEvents
from fastapi_events.middleware import EventHandlerASGIMiddleware
import time

# from starlette.middleware.sessions import SessionMiddleware

cfg = handler.cfg

log = handler.logger

# # Set up logging
# logging.config.dictConfig(log_config(cfg.log_type))


# Set up logging
logging.basicConfig(
    handlers=[
        get_console_handler(),
        info_file_handler(),
        smtp_log_handler(cfg),
        error_file_handler(),
    ],
    encoding=cfg.encoding,
    level=cfg.log_type,
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    await handler.on_api_start()
    yield
    await handler.on_api_shuttdown()


app = FastAPI(
    lifespan=lifespan,
    debug=cfg.debug,
    title=cfg.name,
    description=cfg.description,
    version=cfg.version,
    terms_of_service=cfg.terms,
    contact=cfg.contacts,
    license_info=cfg.license,
    proxy_headers=True,
    forwarded_allow_ips="[::1]",
    swagger_ui_parameters={
        "syntaxHighlight.theme": "tomorrow-night",
        "tryItOutEnabled": True,
        "displayRequestDuration": True,
    },
)

# Include routes
for route in handler.routes:
    app.include_router(route)


# Add events middleware
app.add_middleware(EventHandlerASGIMiddleware, handlers=[APIEvents(cfg)])


# Include Session
# app.add_middleware(SessionMiddleware, secret_key=cfg.secret_key, max_age=1500)


ALLOWED_HOSTS = [str(origin) for origin in cfg.origins]


# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_HOSTS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# TRUSTED_HOSTS = ["*.elyte.com"]
# TrustedHostMiddleware
# app.add_middleware(TrustedHostMiddleware, allowebucket = TokenBucket(4, 1, log)d_hosts=TRUSTED_HOSTS)

# HEADER middleware
app.add_middleware(CustomHeaderMiddleware)

# Static files
app.mount("/static", StaticFiles(directory="./modules/static"), name="static")


@app.exception_handler(StarletteHTTPException)
async def custom_http_exception_handler(
    request: Request, exc: StarletteHTTPException
) -> JSONResponse:
    log.warning(f"{repr(exc.detail)}!!")
    start_time = time.perf_counter()
    _ = await request.body()
    stop_time = time.perf_counter()
    process_time = stop_time - start_time
    return JSONResponse(
        status_code=exc.status_code,
        content=jsonable_encoder(
            {
                "start_time": start_time,
                "stop_time": stop_time,
                "process_time": process_time,
                "message": str(exc.detail),
                "success": False,
            }
        ),
    )


# Override request validation exceptions
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(
    request: Request, exc: RequestValidationError
) -> JSONResponse:
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content=jsonable_encoder(
            {"message": str(exc.errors()), "body": exc.body, "success": False}
        ),
    )


@app.get("/favicon.ico", include_in_schema=False)
def favicon():
    return StaticFiles(directory="./modules/static")


@app.get("/")
async def root():
    return {"message": "Hello Bigger Applications!"}


if __name__ == "__main__":
    uvicorn.run("main:app", port=8080, debug=True, reload=True)
