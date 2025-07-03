import handler
import logging
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
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
from fastapi import FastAPI, Security, Request, status
from contextlib import asynccontextmanager
from modules.middleware.base import (
    CustomHeaderMiddleware,
    RateLimiterMiddleware,
    CustomHTTPExceptionMiddleware,
)
from modules.security.events.base import APIEvents
from fastapi_events.middleware import EventHandlerASGIMiddleware
import time
from typing import AsyncGenerator
from starlette.middleware.gzip import GZipMiddleware

# from starlette.middleware.sessions import SessionMiddleware

cfg = handler.cfg

log = handler.logger

# Set up logging
logging.basicConfig(
    handlers=[
        get_console_handler(),
        info_file_handler(),
        smtp_log_handler(cfg),
        error_file_handler(),
    ],
    encoding=cfg.encoding,
    level=cfg.log_level,
)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
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
    swagger_ui_oauth2_redirect_url="/oauth2-redirect",
    swagger_ui_init_oauth={
        "clientId": cfg.msal_client_id,
        "usePkceWithAuthorizationCodeGrant": True,
        "scopes": cfg.msal_scope_name,
    },
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
# app.add_middleware(SessionMiddleware, secret_key=cfg.secret_key, max_age=None)


ALLOWED_HOSTS = [str(origin) for origin in cfg.origins]


# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_HOSTS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# HEADER middleware
app.add_middleware(CustomHeaderMiddleware)

# for any request that includes "gzip" in the Accept-Encoding header
app.add_middleware(GZipMiddleware, minimum_size=1000, compresslevel=9)

# Request limiter
app.add_middleware(RateLimiterMiddleware, config=cfg)


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
    return JSONResponse(
        status_code=exc.status_code,
        content=jsonable_encoder(
            {
                "startTime": start_time,
                "stopTime": stop_time,
                "processTime": f"{(stop_time - start_time)* 1000:.4f} ms",
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
            {
                "message": " ".join(exc.errors()),
                "body": exc.body,
                "success": False,
            }
        ),
    )


@app.get("/favicon.ico", include_in_schema=False)
def favicon():
    return StaticFiles(directory="./modules/static")


@app.get(
    "/",
    description="API root",
    dependencies=[Security(handler.azure_scheme)],
    response_class=JSONResponse,
)
async def root(request: Request):
    start_time = time.perf_counter()
    _ = await request.body()
    stop_time = time.perf_counter()
    return JSONResponse(
        status_code=200,
        content=jsonable_encoder(
            {
                "startTime": start_time,
                "stopTime": stop_time,
                "processTime": f"{(stop_time - start_time)* 1000:.4f} ms",
                "message": "Hello Bigger Applications!",
                "success": True,
            }
        ),
    )


if __name__ == "__main__":
    uvicorn.run("main:app", port=8000, reload=True)
