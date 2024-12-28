from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import inspect, event, select
from sqlalchemy.engine import Engine
from sqlalchemy.ext.asyncio import (
    async_sessionmaker,
    AsyncEngine,
    AsyncSession,
)
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
        self._engine: AsyncEngine | None = None
        self.async_session: AsyncSession | None = None
        self.select = select

    def __getattr__(self, name):
        return getattr(self.async_session, name)

    def init_db(self):
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

    async def db_queries(self):
        pass

    async def create_admin_account(self, async_session: AsyncSession) -> None:
        admin_username: str = self.cf.contacts["username"]
        admin_email: str = self.cf.contacts["email"]
        tel: str = self.cf.contacts["telephone"]
        password: bytes = self.cf.contacts["password"]
        if await self.get_user_by_username(admin_username) is None:
            admin_user: User = User(
                id=get_indent(),
                email=admin_email,
                username=admin_username,
                password=password,
                active=True,
                telephone=tel,
                admin=True,
                enabled=True,
                created_by=self.cf.contacts["username"],
            )
            try:
                async_session.add(admin_user)
                await async_session.commit()
                self.logger.info(f"account with id {admin_user.id} created")
                return
            except Exception:
                await async_session.rollback()
                raise
        self.logger.info(f"Admin account with name {admin_username} exist already")

    async def get_user_by_id(self, userid: str) -> User | None:
        stmt = self.select(User).where(User.userid == userid)
        users = await self.async_session.execute(stmt)
        return users.scalars().first()

    async def get_user_by_username(self, username: str) -> User | None:
        stmt = self.select(User).where(User.username == username)
        users = await self.async_session.execute(stmt)
        return users.scalars().first()

    async def get_user_by_email(self, email: str) -> User | None:
        stmt = self.select(User).where(User.username == email)
        users = await self.async_session.execute(stmt)
        return users.scalars().first()
