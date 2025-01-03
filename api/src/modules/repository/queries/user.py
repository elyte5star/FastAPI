from modules.repository.schema.users import User
from modules.database.base import AsyncDatabaseSession
from sqlalchemy import or_


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

    async def update_user(self):
        pass

    async def get_users(self):
        pass

    async def delete_user(self):
        pass

    async def get_user_address_by_user(self):
        pass

    async def get_user_location_by_user_and_country(self):
        pass

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
