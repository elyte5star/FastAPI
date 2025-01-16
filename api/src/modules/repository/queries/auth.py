from modules.database.base import AsyncDatabaseSession
from modules.repository.schema.users import DeviceMetaData
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

    async def update_device_meta_data_query(self, id: str, **kwargs) -> None:
        stmt = (
            self.update(DeviceMetaData)
            .where(DeviceMetaData.id == id)
            .values(**kwargs)
            .execution_options(synchronize_session="fetch")
        )
        try:
            await self.async_session.execute(stmt)
            await self.async_session.commit()
        except PostgresError as e:
            await self.async_session.rollback()
            self.logger.error("Failed to update device metadata:", e)
            raise

    async def find_otp_by_email(self, email: str):
        pass

    async def find_otp_by_user(self):
        pass

    async def find_all_otp_expiry_date_since(self):
        pass

    async def del_expired_otp_since(self):
        pass

    async def del_otp_by_expiry_date(self):
        pass

    async def find_otp_by_token(self, token: str):
        pass

    async def find_new_location_by_token(self, token: str):
        pass

    async def find_password_reset_token_by_token(self, token: str):
        pass

    async def find_password_reset_token_by_user(self):
        pass

    async def del_expired_password_reset_token_since(self):
        pass

    async def del_password_reset_token_by_expiry_date(self):
        pass
