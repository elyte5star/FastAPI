from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import inspect, event, select, __version__, delete, or_, and_
from sqlalchemy import update as sqlalchemy_update
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
    UserLocation,  # noqa: F401
    UserAddress,  # noqa: F401
    Otp,  # noqa: F401
    DeviceMetaData,  # noqa: F401,
    NewLocationToken,  # noqa: F401
)
from multiprocessing import cpu_count
from modules.settings.configuration import ApiConfig
from asyncpg.exceptions import PostgresError
from fastapi import Request
from itsdangerous import (
    URLSafeTimedSerializer,
    BadTimeSignature,
    SignatureExpired,
)


class AsyncDatabaseSession:
    def __init__(self, config: ApiConfig):
        self.cf = config
        self.logger = config.logger
        self._engine: AsyncEngine = None
        self.async_session: AsyncSession = None
        self.select = select
        self.delete = delete
        self.sqlalchemy_update = sqlalchemy_update
        self.or_ = or_
        self.and_ = and_
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
        user = await self.create_admin_account(self.async_session)
        user_loc = UserLocation(
            id=get_indent(),
            country="UNKNOWN",
            owner=user,
            enabled=True,
        )
        await self.create_user_location_query(user_loc)

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

    async def create_admin_account(self, async_session: AsyncSession) -> User:
        admin_username: str = self.cf.contacts["username"]
        if await self.get_user_by_username(admin_username) is None:
            admin_email: str = self.cf.contacts["email"]
            tel: str = self.cf.contacts["telephone"]
            password: bytes = self.cf.contacts["password"]
            admin_user = User(
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
                return admin_user
            except PostgresError:
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

    async def update_user_query(self, userid: str, data: dict):
        stmt = (
            self.sqlalchemy_update(User)
            .where(User.id == userid)
            .values(data)
            .execution_options(synchronize_session="fetch")
        )
        try:
            await self.async_session.execute(stmt)
            await self.async_session.commit()
        except PostgresError as e:
            await self.async_session.rollback()
            self.logger.error("Failed to update user:", e)
            raise

    def get_app_url(self, request: Request) -> str:
        client_url = self.get_client_url()
        if client_url is None:
            origin_url = dict(request.scope["headers"]).get(b"referer", b"").decode()
            return origin_url
        return client_url

    def get_client_url(self) -> str:
        client_urls: list = self.cf.origins
        return next(iter(client_urls)) if client_urls else None

    def is_geo_ip_enabled(self) -> bool:
        return self.cf.is_geo_ip_enabled

    async def create_user_location_query(
        self, user_loc: UserLocation
    ) -> UserLocation | None:
        self.async_session.add(user_loc)
        result = None
        try:
            await self.async_session.commit()
            result = user_loc
        except PostgresError as e:
            await self.async_session.rollback()
            self.logger.error("Failed to create user location: ", e)
            raise
        finally:
            return result

    def create_timed_token(self, email: str) -> str:
        serializer = URLSafeTimedSerializer(
            self.cf.secret_key, salt=str(self.cf.rounds)
        )
        return serializer.dumps(email)

    def get_client_ip_address(self, request: Request) -> str:
        xf_header = request.headers.get("X-Forwarded-For")
        if xf_header is not None:
            return xf_header.split(",")[0]
        return "128.101.101.101"  # for testing Richfield,United States
        # return "41.238.0.198" # for testing Giza, Egypt
        # return request.client.host

    def verify_email_token(self, token: str, expiration: int = 3600) -> bool:
        serializer = URLSafeTimedSerializer(self.config.secret_key)
        try:
            _ = serializer.loads(
                token,
                salt=self.config.rounds,
                max_age=expiration,
            )
            return True
        except SignatureExpired:
            return False
        except BadTimeSignature:
            return False
