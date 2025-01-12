from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import inspect, event, select, __version__, delete, update, or_
from sqlalchemy.engine import Engine
from modules.repository.response_models.base import GetInfoResponse
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
    Otp,  # noqa: F401
    DeviceMetaData,  # noqa: F401
)
from multiprocessing import cpu_count
from modules.settings.configuration import ApiConfig


class AsyncDatabaseSession:
    def __init__(self, config: ApiConfig):
        self.cf = config
        self.logger = config.logger
        self._engine: AsyncEngine = None
        self.async_session: AsyncSession = None
        self.select = select
        self.delete = delete
        self.upate = update
        self.or_ = or_
        self.init_db()

    def __getattr__(self, name):
        return getattr(self.async_session, name)

    def init_db(self) -> None:
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
            raise SystemExit("Couldn't connect to database %s" % error)

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

    async def drop_tables(self) -> None:
        async with self._engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)

    async def db_queries(self):
        pass

    async def system_info(self):
        info = {}
        async with self.get_session() as _:
            _, kwargs = self._engine.dialect.create_connect_args(self._engine.url)
        info["database_parameters"] = kwargs
        info["sqlalchemy_version"] = __version__
        info["tables_in_database"] = await self.async_inspect_schema()
        info["cpu_count"] = cpu_count()
        return GetInfoResponse(info=info, message="System information")

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
        stmt = self.select(User).where(User.id == userid)
        users = await self.async_session.execute(stmt)
        return users.scalars().first()

    async def get_user_by_username(self, username: str) -> User | None:
        stmt = self.select(User).where(User.username == username)
        users = await self.async_session.execute(stmt)
        return users.scalars().first()

    async def get_user_by_email(self, email: str) -> User | None:
        stmt = self.select(User).where(User.email == email)
        users = await self.async_session.execute(stmt)
        return users.scalars().first()
