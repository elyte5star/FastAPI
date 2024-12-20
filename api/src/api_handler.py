from modules.settings.configuration import ApiConfig
from fastapi import FastAPI
import logging
from starlette.staticfiles import StaticFiles

cfg = ApiConfig().from_toml_file().from_env_file()


app = FastAPI(
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
