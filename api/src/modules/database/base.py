from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy import inspect
from modules.domain.schema.base import Base
from modules.domain.schema.users import Users
from fastapi.logger import logger


class AsyncDatabaseSession:
    def __init__(self, config):
        self.cf = config
        self.logger = config.logger
        self._engine = None
        self._session = None

    def __getattr__(self, name):
        return getattr(self._session, name)

    def init_db(self) -> AsyncSession:
        try:
            self._engine = create_async_engine(
                self.cf.db_url,
                future=True,
                echo=False,
                pool_recycle=3600,
            )
            self._session = sessionmaker(
                self._engine, expire_on_commit=False, class_=AsyncSession
            )()

        except Exception as ex:
            self.logger.warning("Couldn't connect to DB : \n", ex)

    def use_inspector(self, conn):
        inspector = inspect(conn)
        return inspector.get_table_names()

    async def async_inspect_schema(self):
        async with self._engine.connect() as conn:
            tables = await conn.run_sync(self.use_inspector)
        return tables

    async def create_db_and_tables(self):
        async with self._engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)
            await conn.run_sync(Base.metadata.create_all)
