from modules.database.base import AsyncDatabaseSession
from modules.repository.schema.users import (
    DeviceMetaData,
    UserLocation,
    User,
    NewLocationToken,
)
from asyncpg.exceptions import PostgresError


class AuthQueries(AsyncDatabaseSession):

    # DEVICE METADATA
    async def find_device_meta_data_by_userid_query(
        self, userid: str
    ) -> list[DeviceMetaData]:
        stmt = self.select(DeviceMetaData).where(DeviceMetaData.userid == userid)
        result = await self.async_session.execute(stmt)
        return result.scalars().all()

    async def create_device_meta_data_query(
        self, device_metadata: DeviceMetaData
    ) -> DeviceMetaData | None:
        self.async_session.add(device_metadata)
        result = None
        try:
            await self.async_session.commit()
            result = device_metadata
        except PostgresError as e:
            await self.async_session.rollback()
            self.logger.error("Failed to create device metadata: ", e)
            raise
        finally:
            return result

    async def update_device_meta_data_query(self, id: str, data: dict) -> dict | None:
        result = None
        stmt = (
            self.sqlalchemy_update(DeviceMetaData)
            .where(DeviceMetaData.id == id)
            .values(data)
            .execution_options(synchronize_session="fetch")
        )
        try:
            result = await self.async_session.execute(stmt)
            await self.async_session.commit()
            result = result.last_updated_params()
            return result
        except PostgresError as e:
            await self.async_session.rollback()
            self.logger.error("Failed to update device metadata:", e)
            raise
        finally:
            return result

    # USER LOCATION
    async def find_user_location_by_country_and_user_query(
        self, country: str, user: User
    ) -> UserLocation | None:
        stmt = (
            self.select(UserLocation)
            .where(
                self.and_(UserLocation.country == country, UserLocation.owner == user)
            )
            .limit(1)
        )
        result = await self.async_session.execute(stmt)
        return result.scalars().first()

    async def create_new_location_token_query(
        self, new_loc_token: NewLocationToken
    ) -> NewLocationToken | None:
        self.async_session.add(new_loc_token)
        result = None
        try:
            await self.async_session.commit()
            result = new_loc_token
        except PostgresError as e:
            await self.async_session.rollback()
            self.logger.error("Failed to create new location token: ", e)
            raise
        finally:
            return result
