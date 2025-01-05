import handler
import logging
from fastapi.middleware.cors import CORSMiddleware
from starlette.staticfiles import StaticFiles
from modules.middleware.log import get_file_handler, get_console_handler
from fastapi.encoders import jsonable_encoder
from starlette.exceptions import HTTPException as StarletteHTTPException
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from fastapi import Request, status
from fastapi import FastAPI
from contextlib import asynccontextmanager
from modules.middleware.base import CustomHeaderMiddleware

# from starlette.middleware.sessions import SessionMiddleware

cfg = handler.cfg

logger = handler.logger

# Set up logging
logging.basicConfig(
    handlers=[get_console_handler(), get_file_handler(cfg.log_file_path)],
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
    swagger_ui_parameters={
        "syntaxHighlight.theme": "tomorrow-night",
        "tryItOutEnabled": True,
        "displayRequestDuration": True,
    },
)

# Include routes
for route in handler.routes:
    app.include_router(route)

# Include Session
# app.add_middleware(SessionMiddleware, secret_key=cfg.secret_key, max_age=1500)

ALLOWED_HOSTS = ["*"]
if cfg.origins:
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

# Static files
app.mount("/static", StaticFiles(directory="./modules/static"), name="static")


@app.exception_handler(StarletteHTTPException)
async def custom_http_exception_handler(
    request: Request, exc: StarletteHTTPException
) -> JSONResponse:
    logger.warning(f"{repr(exc.detail)}!!")
    body = await request.body()
    return JSONResponse(
        status_code=exc.status_code,
        content=jsonable_encoder(
            {"message": str(exc.detail), "body": body.decode(), "success": False}
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
