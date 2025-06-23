from modules.settings.configuration import ApiConfig
from fastapi.logger import logger
from modules.routers.auth import AuthRouter
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

auth_router = AuthRouter(cfg)

user_router = UserRouter(cfg)

product_router = ProductRouter(cfg)

booking_router = BookingRouter(cfg)

search_router = SearchRouter(cfg)

job_router = JobRouter(cfg)


system_router = SystemInfoRouter(cfg)

routes: tuple[APIRouter, ...] = (
    auth_router.router,
    user_router.router,
    product_router.router,
    booking_router.router,
    search_router.router,
    job_router.router,
    system_router.router,
)


async def on_api_start():
    await user_router.create_tables()
    await user_router.create_admin_account()
    logger.info(f"{cfg.name}: v{cfg.version} is starting.")


async def on_api_shuttdown():
    await user_router._engine.dispose()
    logger.info(f"{cfg.name}: v{cfg.version} is shutting down.")


@event.listens_for(Engine, "first_connect")
def receive_connect(dbapi_con, connection_record):
    "listen for the 'first_connect' event"
    logger.info(f"New DBAPI connection::{connection_record}")


@event.listens_for(Engine, "close")
def receive_close(dbapi_con, connection_record):
    "listen for the 'close' event"
    logger.warning(f"New DBAPI connection: {dbapi_con.cursor()} closed")


@event.listens_for(Engine, "before_cursor_execute")
def before_cursor_execute(conn, cursor, statement, parameters, context, executemany):
    # logger.info("Received statement: %s", statement)
    pass


@event.listens_for(Engine, "rollback")
def receive_rollback(conn):
    "listen for the 'rollback' event"
    logger.warning("A rollback event")
