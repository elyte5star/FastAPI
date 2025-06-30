from modules.settings.configuration import ApiConfig
from fastapi.logger import logger
from modules.routers.auth import AuthRouter
from modules.routers.google_auth import GoogleAuthRouter
from modules.routers.msoft import MSOFTAuthRouter
from modules.routers.search import SearchRouter
from modules.routers.user import UserRouter
from modules.routers.product import ProductRouter
from modules.routers.booking import BookingRouter
from modules.routers.job import JobRouter
from modules.routers.system import SystemInfoRouter
from fastapi import APIRouter
from sqlalchemy.engine import Engine
from sqlalchemy import event

cfg = ApiConfig().from_toml_file().from_env_file()

cfg.logger = logger


system_router = SystemInfoRouter(cfg)

auth_router = AuthRouter(cfg)

google_router = GoogleAuthRouter(cfg)

msal_router = MSOFTAuthRouter(cfg)

user_router = UserRouter(cfg)

product_router = ProductRouter(cfg)

booking_router = BookingRouter(cfg)

search_router = SearchRouter(cfg)

job_router = JobRouter(cfg)


routes: tuple[APIRouter, ...] = (
    system_router.router,
    auth_router.router,
    google_router.router,
    msal_router.router,
    user_router.router,
    product_router.router,
    booking_router.router,
    search_router.router,
    job_router.router,
)


async def on_api_start():
    await system_router.create_tables()
    await system_router.create_admin_account()
    logger.info(f"{cfg.name}: v{cfg.version} is starting.")


async def on_api_shuttdown():
    await system_router._engine.dispose()
    logger.info(f"{cfg.name}: v{cfg.version} is shutting down.")


@event.listens_for(Engine, "first_connect")
def receive_connect(dbapi_con, connection_record):
    "listen for the 'first_connect' event"
    logger.info("New Database connection::")


@event.listens_for(Engine, "close")
def receive_close(dbapi_con, connection_record):
    "listen for the 'close' event"
    logger.warning(f"Connection closed::{dbapi_con.cursor()} closed")


@event.listens_for(Engine, "before_cursor_execute")
def before_cursor_execute(
    conn,
    cursor,
    statement,
    parameters,
    context,
    executemany,
):
    # logger.info("Received statement: %s", statement)
    pass


@event.listens_for(Engine, "rollback")
def receive_rollback(conn):
    "listen for the 'rollback' event"
    logger.warning("A rollback event")
