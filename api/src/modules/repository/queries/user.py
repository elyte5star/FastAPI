from modules.repository.schema.users import User
from modules.database.base import AsyncDatabaseSession, or_


class UserQueries(AsyncDatabaseSession):

    async def create_user_query(self, user: User) -> str | None:
        self.async_session.add(user)
        result = None
        try:
            await self.async_session.commit()
            result = user.id
        except Exception as error:
            await self.async_session.rollback()
            self.logger.error(error)
            raise
        finally:
            return result

    async def update_user():
        pass

    async def get_user_by_id(self, userid: str) -> User | None:
        stmt = self.select(User).where(User.userid == userid)
        users = await self.async_session.execute(stmt)
        (user,) = users.first()
        return user

    async def get_user_by_email(self, email: str):
        pass

    async def get_users(self):
        pass

    async def delete_user(self):
        pass

    async def get_user_by_username(self, username: str):
        pass

    async def get_user_address_by_user(self):
        pass

    async def get_user_location_by_user_and_country(self):
        pass

    async def check_if_user_exist(self, email: str, username: str) -> User | None:
        stmt = (
            self.select(User.email, User.username)
            .where(or_(User.email == email, User.username == username))
            .limit(1)
        )
        result = await self.async_session.execute(stmt).scalars().first()
        return result
