from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy import inspect, event, select, or_
from sqlalchemy.engine import Engine
from sqlalchemy.ext.asyncio import async_sessionmaker, async_session
from modules.repository.schema.base import Base
from modules.utils.misc import get_indent
from modules.repository.schema.users import (
    User,  # noqa: F401
    UserLocations,  # noqa: F401
    UserAddress,  # noqa: F401
    Otps,  # noqa: F401
    DeviceMetaData,  # noqa: F401
)


class AsyncDatabaseSession:
    def __init__(self, config):
        self.cf = config
        self.logger = config.logger
        self._engine = None
        self.async_session = None
        self.select = select

    def __getattr__(self, name):
        return getattr(self.async_session, name)

    def init_db(self) -> async_sessionmaker[AsyncSession]:
        try:
            self._engine = create_async_engine(
                self.cf.db_url,
                future=True,
                echo=False,
                pool_recycle=3600,
            )
            self.async_session = async_sessionmaker(
                self._engine,
                expire_on_commit=False,
            )()
        except Exception as error:
            self.logger.error(error)
            raise

    def get_new_id(self) -> str:
        return get_indent()

    def use_inspector(self, conn):
        inspector = inspect(conn)
        return inspector.get_table_names()

    async def async_inspect_schema(self):
        async with self._engine.connect() as conn:
            tables = await conn.run_sync(self.use_inspector)
        self.logger.info(tables)
        return tables

    @event.listens_for(Engine, "connect")
    def my_on_connect(dbapi_con, connection_record):
        pass

    async def create_tables(self):
        async with self._engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)
            await conn.run_sync(Base.metadata.create_all)
        await self.create_admin_account(self.async_session)

    async def create_admin_account(self, async_session: async_session) -> None:
        admin_user = User(
            id=get_indent(),
            email="elyte5star@gmail.com",
            username="elyte5star",
            password="$2b$10$rQcvrrW2JcvjV2XM5TG3zeJd6oHPthld3VfRLsvyV2UJFO0.BxACO",
            active=True,
            telephone="889851919",
            admin=True,
            failed_attempts=0,
            created_by="elyte",
        )
        async_session.add(admin_user)
        try:
            await async_session.commit()
            self.logger.info(f"account with id {admin_user.id} created")
        except Exception:
            await async_session.rollback()
            raise
