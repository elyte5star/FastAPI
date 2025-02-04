from modules.settings.configuration import ApiConfig
from fastapi.logger import logger
from modules.routers.auth import AuthRouter
from modules.routers.user import UserRouter
from modules.routers.system import SystemInfoRouter
from fastapi import APIRouter
from modules.database.base import AsyncDatabaseSession

cfg = ApiConfig().from_toml_file().from_env_file()

cfg.logger = logger

db = AsyncDatabaseSession(cfg)

auth_router = AuthRouter(cfg)

user_router = UserRouter(cfg)

system_router = SystemInfoRouter(cfg)

routes: tuple[APIRouter, ...] = (
    auth_router.router,
    user_router.router,
    system_router.router,
)


async def on_api_start():
    await db.create_tables()
    logger.info(f"{cfg.name}: v{cfg.version} is starting.")


async def on_api_shuttdown():
    await db._engine.dispose()
    logger.info(f"{cfg.name}: v{cfg.version} is shutting down.")
