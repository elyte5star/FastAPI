from modules.settings.configuration import ApiConfig
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.staticfiles import StaticFiles
from fastapi.logger import logger
from contextlib import asynccontextmanager

ALLOWED_HOSTS = ["*"]


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Do something now.")
    yield
    logger.info("Do something later.")


def get_application(cfg: ApiConfig) -> FastAPI:

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
    app.mount("/static", StaticFiles(directory="./modules/static"), name="static")
    return app


async def on_api_start(cfg: ApiConfig):
    logger.info(f"{cfg.name} v{cfg.version} is starting.")
