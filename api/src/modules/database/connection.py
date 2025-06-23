from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.future import select
from sqlalchemy import inspect, __version__, delete, or_, and_
from sqlalchemy import update as sqlalchemy_update
from sqlalchemy.ext.asyncio import (
    async_sessionmaker,
    AsyncEngine,
    AsyncSession,
)
from modules.database.schema.base import Base
from modules.utils.misc import get_indent, date_time_now_utc
from modules.database.schema.user import (
    User,  # noqa: F401
    UserLocation,  # noqa: F401
    Otp,  # noqa: F401
    DeviceMetaData,  # noqa: F401,
    NewLocationToken,  # noqa: F401
    Enquiry,  # noqa: F401
    Address,  # noqa: F401
    Booking,
)
from modules.database.schema.product import (
    Product,  # noqa: F401
    Review,  # noqa: F401
    SpecialDeals,  # noqa: F401
)  # noqa: F401


# noqa: F401
from modules.queue.schema import Job, Task, Result  # noqa: F401
from modules.settings.configuration import ApiConfig


class AsyncDatabaseSession:
    def __init__(self, config: ApiConfig):
        self.cf = config
        self.logger = config.logger
        self._engine: AsyncEngine
        self.async_session: AsyncSession
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

    async def create_tables(self):
        async with self._engine.begin() as conn:
            # await conn.run_sync(Base.metadata.drop_all)
            await conn.run_sync(Base.metadata.create_all)
        # await self.create_admin_account(self.async_session)

    async def drop_tables(self) -> None:
        async with self._engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)
