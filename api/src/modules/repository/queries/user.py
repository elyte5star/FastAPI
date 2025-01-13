from modules.repository.schema.users import (
    User,
    Otp,
    DeviceMetaData,
    NewLocationToken,
    UserLocation,
    PasswordResetToken,
)
from modules.database.base import AsyncDatabaseSession
from asyncpg.exceptions import PostgresError
from modules.repository.response_models.user import CreatedUserData
from datetime import datetime


class UserQueries(AsyncDatabaseSession):

    # USER
    async def create_user_query(self, user: User) -> CreatedUserData | None:
        self.async_session.add(user)
        result = None
        try:
            await self.async_session.commit()
            result = CreatedUserData(userid=user.id, createdAt=user.created_at)
        except PostgresError as e:
            await self.async_session.rollback()
            self.logger.error("Failed to create user: ", e)
            raise
        finally:
            return result

    async def update_user_query(self, userid: str, **kwargs):
        stmt = (
            self.update(User)
            .where(User.id == userid)
            .values(**kwargs)
            .execution_options(synchronize_session="fetch")
        )
        try:
            await self.async_session.execute(stmt)
            await self.async_session.commit()
        except PostgresError as e:
            await self.async_session.rollback()
            self.logger.error("Failed to update user:", e)
            raise

    async def get_users_query(self) -> list[User]:
        stmt = self.select(User).order_by(User.created_at)
        result = await self.async_session.execute(stmt)
        users = result.scalars().all()
        return users

    async def delete_user_query(self, userid: str) -> bool:
        stmt = self.delete(User).where(User.id == userid)
        result = False
        try:
            await self.async_session.execute(stmt)
            await self.async_session.commit()
            result = True
        except PostgresError as e:
            await self.async_session.rollback()
            self.logger.error("Failed to delete user:", e)
            raise
        finally:
            return result

    async def check_if_user_exist(
        self, email: str, username: str, telephone: str
    ) -> User | None:
        stmt = (
            self.select(User.email, User.username)
            .where(
                self.or_(
                    User.email == email,
                    User.username == username,
                    User.telephone == telephone,
                )
            )
            .limit(1)
        )
        result = await self.async_session.execute(stmt)
        return result.scalars().first()

    # OTP
    async def create_otp_query(self, otp: Otp) -> Otp | None:
        self.async_session.add(otp)
        result = None
        try:
            await self.async_session.commit()
            result = otp
        except PostgresError as e:
            await self.async_session.rollback()
            self.logger.error("Failed to create user otp: ", e)
            raise
        finally:
            return result

    async def delete_otp_query(self, otp_id: str) -> bool:
        stmt = self.delete(Otp).where(Otp.id == otp_id)
        result = False
        try:
            await self.async_session.execute(stmt)
            await self.async_session.commit()
            result = True
        except PostgresError as e:
            await self.async_session.rollback()
            self.logger.error("Failed to delete user:", e)
            raise
        finally:
            return result

    async def get_otp_by_user_query(self, user: User) -> Otp | None:
        stmt = self.select(Otp).where(Otp.owner == user)
        users = await self.async_session.execute(stmt)
        await self.async_session.refresh(users, ["owner"])
        return users.scalars().first()

    async def get_otp_by_token_query(self, token: str) -> Otp | None:
        stmt = self.select(Otp).where(Otp.token == token)
        users = await self.async_session.execute(stmt)
        await self.async_session.refresh(users, ["owner"])
        return users.scalars().first()

    async def del_otp_by_expiry_date_less_than(self, now: datetime) -> None:
        stmt = self.delete(Otp).where(Otp.expiry <= now)
        try:
            await self.async_session.execute(stmt)
            await self.async_session.commit()
        except PostgresError as e:
            await self.async_session.rollback()
            self.logger.error("Failed to delete otp:", e)
            raise

    async def del_all_expired_otps_since(self, now: datetime) -> None:
        stmt = self.delete(Otp).where(Otp.expiry <= now)
        try:
            await self.async_session.execute(stmt)
            await self.async_session.commit()
        except PostgresError as e:
            await self.async_session.rollback()
            self.logger.error("Failed to delete otp:", e)
            raise

    async def find_all_otps_expiry_less(self, now: datetime) -> list[Otp]:
        stmt = self.select(Otp).where(Otp.expiry <= now)
        result = await self.async_session.execute(stmt)
        otps = result.scalars().all()
        return otps

    async def update_otp_query(self, id: str, **kwargs) -> None:
        stmt = (
            self.update(Otp)
            .where(Otp.id == id)
            .values(**kwargs)
            .execution_options(synchronize_session="fetch")
        )
        try:
            await self.async_session.execute(stmt)
            await self.async_session.commit()
        except PostgresError as e:
            await self.async_session.rollback()
            self.logger.error("Failed to update otp:", e)
            raise

    # DEVICE METADATA
    async def find_device_mmeta_data_by_userid_query(
        self, userid: str
    ) -> list[DeviceMetaData]:
        stmt = self.select(DeviceMetaData).where(DeviceMetaData.userid == userid)
        result = await self.async_session.execute(stmt)
        return result.scalars().all()

    # NEW LOCATION
    async def find_new_location_by_token_query(
        self, token: str
    ) -> NewLocationToken | None:
        stmt = self.select(NewLocationToken).where(NewLocationToken.token == token)
        new_locs = await self.async_session.execute(stmt)
        return new_locs.scalars().first()

    async def find_new_location_by_user_location_query(
        self, user_loc: UserLocation
    ) -> NewLocationToken | None:
        stmt = self.select(NewLocationToken).where(
            NewLocationToken.location == user_loc
        )
        new_locs = await self.async_session.execute(stmt)
        return new_locs.scalars().first()

    # USER LOCATION
    async def find_user_location_by_country_and_user(
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

    # PASSWORD RESET
    async def find_passw_reset_token_by_token_query(
        self, token: str
    ) -> PasswordResetToken:
        stmt = self.select(PasswordResetToken).where(PasswordResetToken.token == token)
        result = await self.async_session.execute(stmt)
        return result.scalars().first()

    async def find_passw_reset_token_by_user_query(
        self, user: User
    ) -> PasswordResetToken:
        stmt = self.select(PasswordResetToken).where(PasswordResetToken.owner == user)
        result = await self.async_session.execute(stmt)
        return result.scalars().first()

    async def find_all_passw_reset_token_expiry_less(
        self, now: datetime
    ) -> list[PasswordResetToken]:
        stmt = self.select(PasswordResetToken).where(PasswordResetToken.expiry <= now)
        result = await self.async_session.execute(stmt)
        return result.scalars().all()

    async def del_all_expired_passw_reset_token_since(self, now: datetime) -> None:
        stmt = self.delete(PasswordResetToken).where(PasswordResetToken.expiry <= now)
        try:
            await self.async_session.execute(stmt)
            await self.async_session.commit()
        except PostgresError as e:
            await self.async_session.rollback()
            self.logger.error("Failed to delete password reset token:", e)
            raise
