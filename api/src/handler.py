from modules.settings.configuration import ApiConfig
from fastapi.logger import logger
from modules.database.base import AsyncDatabaseSession
from modules.routers import users, auth
from fastapi import APIRouter


cfg = ApiConfig().from_toml_file().from_env_file()
cfg.logger = logger

db = AsyncDatabaseSession(cfg)
db.init_db()

routes: tuple[APIRouter, ...] = (users.user_router, auth)


async def on_api_start():
    await db.create_tables()
    logger.info(f"{cfg.name}: v{cfg.version} is starting.")


async def on_api_shuttdown():
    await db._engine.dispose()
    logger.info(f"{cfg.name}: v{cfg.version} is shutting down.")
