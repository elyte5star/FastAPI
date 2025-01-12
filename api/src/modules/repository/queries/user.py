from modules.repository.schema.users import User, Otp
from modules.database.base import AsyncDatabaseSession
from asyncpg.exceptions import PostgresError
from modules.repository.response_models.user import CreatedUserData
from datetime import datetime


class UserQueries(AsyncDatabaseSession):
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

    async def get_otp_by_email_query(self, email: str) -> Otp | None:
        stmt = self.select(Otp).where(Otp.email == email)
        users = await self.async_session.execute(stmt)
        return users.scalars().first()

    async def get_otp_by_token_query(self, token: str) -> Otp | None:
        stmt = self.select(Otp).where(Otp.token == token)
        users = await self.async_session.execute(stmt)
        return users.scalars().first()

    async def del_expired_otps_since(self, now: datetime) -> None:
        stmt = self.delete(Otp).where(Otp.expiry <= now)
        try:
            await self.async_session.execute(stmt)
            await self.async_session.commit()
        except PostgresError as e:
            await self.async_session.rollback()
            self.logger.error("Failed to delete user:", e)
            raise

    async def find_all_otps_expiry_less(self, now: datetime) -> list[Otp]:
        stmt = self.select(Otp).where(Otp.expiry <= now)
        result = await self.async_session.execute(stmt)
        otps = result.scalars().all()
        return otps

    async def update_otp_query(self, id: str, **kwargs):
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
