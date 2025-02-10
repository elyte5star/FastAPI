from modules.repository.schema.users import (
    User,
    Otp,
    NewLocationToken,
    UserLocation,
    PasswordResetToken,
    Enquiry,
)
from modules.database.base import AsyncDatabaseSession
from asyncpg.exceptions import PostgresError
from datetime import datetime
from modules.utils.misc import time_now_utc


class UserQueries(AsyncDatabaseSession):
    async def create_user_query(self, user: User) -> User | None:
        self.async_session.add(user)
        result = None
        try:
            await self.async_session.commit()
            result = user
        except PostgresError as e:
            await self.async_session.rollback()
            self.logger.error("Failed to create user: ", e)
            raise
        finally:
            return result

    async def get_users_query(self) -> list[User]:
        stmt = self.select(User).order_by(User.created_at)
        result = await self.async_session.execute(stmt)
        users = result.scalars().all()
        return users

    async def activate_new_user_account(self, userid: str):
        stmt = self.select(User).where(User.id == userid)
        try:
            users = await self.async_session.execute(stmt)
            user = users.scalars().first()
            user.modified_at = time_now_utc()
            user.enabled = True
            user.modified_by = user.username
            await self.async_session.commit()
        except PostgresError as e:
            await self.async_session.rollback()
            self.logger.error(f"Failed to activate user:{e}")
            raise

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

    async def delete_otp_by_id_query(self, otp_id: str) -> bool:
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
        result = await self.async_session.execute(stmt)
        return result.scalars().first()

    async def get_otp_by_email_query(self, email: str) -> Otp | None:
        stmt = self.select(Otp).where(Otp.email == email)
        result = await self.async_session.execute(stmt)
        return result.scalars().first()

    async def get_otp_by_token_query(self, token: str) -> Otp | None:
        stmt = self.select(Otp).where(Otp.token == token)
        result = await self.async_session.execute(stmt)
        return result.scalars().first()

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

    async def update_otp_query(self, id: str, data: dict) -> dict | None:
        result = None
        stmt = (
            self.sqlalchemy_update(Otp)
            .where(Otp.id == id)
            .values(data)
            .execution_options(synchronize_session="fetch")
        )
        try:
            result = await self.async_session.execute(stmt)
            result = result.last_updated_params()
            return result
        except PostgresError as e:
            await self.async_session.rollback()
            self.logger.error("Failed to update otp:", e)
            raise

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

    async def update_new_loc_query(self, id: str, data: dict) -> None:
        stmt = (
            self.sqlalchemy_update(NewLocationToken)
            .where(NewLocationToken.id == id)
            .values(data)
            .execution_options(synchronize_session="fetch")
        )
        try:
            await self.async_session.execute(stmt)
            await self.async_session.commit()
        except PostgresError as e:
            await self.async_session.rollback()
            self.logger.error("Failed to update otp:", e)
            raise

    async def del_new_location_query(self, id: str) -> None:
        stmt = self.delete(NewLocationToken).where(NewLocationToken.id == id)
        try:
            await self.async_session.execute(stmt)
            await self.async_session.commit()
        except PostgresError as e:
            await self.async_session.rollback()
            self.logger.error("Failed to delete new location:", e)
            raise

    async def update_user_loc_query(self, id: str, data: dict) -> None:
        stmt = (
            self.sqlalchemy_update(UserLocation)
            .where(UserLocation.id == id)
            .values(data)
            .execution_options(synchronize_session="fetch")
        )
        try:
            await self.async_session.execute(stmt)
            await self.async_session.commit()
        except PostgresError as e:
            await self.async_session.rollback()
            self.logger.error("Failed to update otp:", e)
            raise

    # PASSWORD RESET
    async def create_pass_reset_query(self, token: PasswordResetToken) -> str:
        self.async_session.add(token)
        result = ""
        try:
            await self.async_session.commit()
            result = token.id
        except PostgresError as e:
            await self.async_session.rollback()
            self.logger.error(f"Failed to create usr reset password: {e}")
            raise
        finally:
            return result

    async def update_pass_token_query(self, id: str, data: dict) -> dict | None:
        result = None
        stmt = (
            self.sqlalchemy_update(PasswordResetToken)
            .where(PasswordResetToken.id == id)
            .values(data)
            .execution_options(synchronize_session="fetch")
        )
        try:
            result = await self.async_session.execute(stmt)
            result = result.last_updated_params()
            return result
        except PostgresError as e:
            await self.async_session.rollback()
            self.logger.error("Failed to update otp:", e)
            raise

    async def find_passw_token_by_token_query(
        self, token: str
    ) -> PasswordResetToken | None:
        stmt = self.select(PasswordResetToken).where(PasswordResetToken.token == token)
        result = await self.async_session.execute(stmt)
        return result.scalars().first()

    async def find_passw_token_by_user_query(self, user: User) -> PasswordResetToken:
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

    async def delete_passw_reset_token_by_id_query(self, id: str) -> bool:
        stmt = self.delete(PasswordResetToken).where(PasswordResetToken.id == id)
        result = False
        try:
            await self.async_session.execute(stmt)
            await self.async_session.commit()
            result = True
        except PostgresError as e:
            await self.async_session.rollback()
            self.logger.error("Failed to delete password-reset_token:", e)
            raise
        finally:
            return result

    async def create_enquiry_query(self, enquiry: Enquiry) -> str:
        self.async_session.add(enquiry)
        result = ""
        try:
            await self.async_session.commit()
            result = enquiry.id
        except PostgresError as e:
            await self.async_session.rollback()
            self.logger.error(f"Failed to create user enquiry: {e}")
            raise
        finally:
            return result
