from modules.settings.configuration import ApiConfig
from fastapi.logger import logger
from modules.database.base import AsyncDatabaseSession

cfg = ApiConfig().from_toml_file().from_env_file()
cfg.logger = logger

db = AsyncDatabaseSession(cfg)
db.init_db()


async def on_api_start():
    await db.create_db_and_tables()
    logger.info(f"{cfg.name} v{cfg.version} is starting.")


async def on_api_shuttdown():
    await db._engine.dispose()
    logger.info(f"{cfg.name} v{cfg.version} is shutting down.")
