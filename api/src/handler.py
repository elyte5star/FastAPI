from modules.routers import user
from modules.settings.configuration import ApiConfig
from fastapi.logger import logger
from modules.database.base import AsyncDatabaseSession
from modules.routers.auth import AuthRouter

# from modules.routers.user import user
from fastapi import APIRouter


cfg = ApiConfig().from_toml_file().from_env_file()
cfg.logger = logger

# db = AsyncDatabaseSession(cfg)
# db.init_db()

auth_router = AuthRouter(cfg)

auth_router.init_db()

routes: tuple[APIRouter, ...] = (auth_router.router,)


async def on_api_start():
    await auth_router.create_tables()
    logger.info(f"{cfg.name}: v{cfg.version} is starting.")


async def on_api_shuttdown():
    #await db._engine.dispose()
    logger.info(f"{cfg.name}: v{cfg.version} is shutting down.")
