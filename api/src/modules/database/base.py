from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.future import select
from sqlalchemy import inspect, __version__, delete, or_, and_
from sqlalchemy import update as sqlalchemy_update
from sqlalchemy.ext.asyncio import (
    async_sessionmaker,
    AsyncEngine,
    AsyncSession,
)
from modules.repository.schema.base import Base
from modules.utils.misc import get_indent, time_now_utc
from modules.repository.schema.user import (
    User,  # noqa: F401
    UserLocation,  # noqa: F401
    UserAddress,  # noqa: F401
    Otp,  # noqa: F401
    DeviceMetaData,  # noqa: F401,
    NewLocationToken,  # noqa: F401
    Enquiry,  # noqa: F401
    Address,  # noqa: F401
)
from modules.repository.schema.product import (
    Product,  # noqa: F401
    Review,  # noqa: F401
    SpecialDeals,  # noqa: F401
    Order,  # noqa: F401
)  # noqa: F401
from multiprocessing import cpu_count
from modules.settings.configuration import ApiConfig
from asyncpg.exceptions import PostgresError
from fastapi import Request
from itsdangerous import (
    URLSafeTimedSerializer,
    BadTimeSignature,
    SignatureExpired,
)
import geoip2.errors
import geoip2.database


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

    async def system_info(self) -> dict:
        async with self.async_session as _:
            _, kwargs = self._engine.dialect.create_connect_args(
                self._engine.url,
            )
        info = dict(
            database_parameters=kwargs,
            sqlalchemy_version=__version__,
            tables_in_database=await self.async_inspect_schema(),
            queue_parameters=self.cf.rabbit_connect_string,
            cpu_count=cpu_count(),
        )
        return info

    async def create_admin_account(self, async_session: AsyncSession) -> None:
        admin_username = self.cf.contacts["username"]
        if await self.get_user_by_username(admin_username) is None:
            admin_email = self.cf.contacts["email"]
            tel = self.cf.contacts["telephone"]
            password = self.cf.contacts["password"]
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
                await self.admin_location(admin_user)
                return None
            except PostgresError:
                await async_session.rollback()
                raise
        self.logger.info(f"Account with name {admin_username} exist already")

    async def admin_location(self, user: User):
        user_loc = UserLocation(
            id=get_indent(),
            country="UNKNOWN",
            owner=user,
            enabled=True,
        )
        await self.create_user_location_query(user_loc)

    async def find_user_by_id(self, userid: str) -> User | None:
        return await self.async_session.get(User, userid)

    async def get_user_by_username(self, username: str) -> User | None:
        stmt = self.select(User).where(User.username == username)
        users = await self.async_session.execute(stmt)
        return users.scalars().first()

    async def find_user_by_email(self, email: str) -> User | None:
        stmt = self.select(User).where(User.email == email)
        users = await self.async_session.execute(stmt)
        return users.scalars().first()

    async def update_user_query(self, userid: str, user_data: dict):
        stmt = (
            self.sqlalchemy_update(User)
            .where(User.id == userid)
            .values(user_data)
            .execution_options(synchronize_session="fetch")
        )
        try:
            await self.async_session.execute(stmt)
            await self.async_session.commit()
        except PostgresError:
            await self.async_session.rollback()
            raise

    def get_app_url(self, request: Request) -> str:
        client_url = self.get_client_url()
        if client_url is None:
            origin_url = dict(request.scope["headers"]).get(b"referer", b"").decode()
            return origin_url
        return client_url

    def get_client_url(self) -> str:
        client_urls = self.cf.origins
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
        # return "128.101.101.101"  # for testing Richfield,United States
        # return "41.238.0.198"  # for testing Giza, Egypt
        return request.client.host

    def verify_email_token(self, token: str, expiration: int = 3600) -> bool:
        serializer = URLSafeTimedSerializer(self.cf.secret_key)
        try:
            _ = serializer.loads(
                token,
                salt=str(self.cf.rounds),
                max_age=expiration,
            )
            return True
        except SignatureExpired:
            return False
        except BadTimeSignature:
            return False

    async def get_location_from_ip(self, ip: str) -> str:
        location = ("UNKNOWN", "UNKNOWN")
        try:
            with geoip2.database.Reader(
                "./modules/static/maxmind/GeoLite2-City.mmdb"
            ) as reader:
                response = reader.city(ip)
                return (response.country.name, response.city.name)
        except geoip2.errors.AddressNotFoundError as e:
            self.logger.error(e)
            return location

    async def lock_user_account_query(self, user: User) -> None:
        changes = dict(lock_time=time_now_utc(), is_locked=True)
        await self.update_user_query(user.id, changes)
        self.logger.warning(f"User with id: {user.id} is locked")
