from modules.repository.schema.users import User
from modules.database.base import AsyncDatabaseSession
from sqlalchemy import or_, delete, update
from asyncpg.exceptions import PostgresError


class UserQueries(AsyncDatabaseSession):
    async def create_user_query(self, user: User) -> str | None:
        self.async_session.add(user)
        result = None
        try:
            await self.async_session.commit()
            result = user.id
        except PostgresError as e:
            await self.async_session.rollback()
            self.logger.error("Failed to create user:", e)
            raise
        finally:
            return result

    async def update_user_query(self, userid: str, **kwargs):
        stmt = (
            update(User)
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
        stmt = delete(User).where(User.id == userid)
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
                or_(
                    User.email == email,
                    User.username == username,
                    User.telephone == telephone,
                )
            )
            .limit(1)
        )
        result = await self.async_session.execute(stmt)
        return result.scalars().first()
