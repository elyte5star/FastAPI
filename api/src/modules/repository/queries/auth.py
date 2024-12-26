from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker


class AuthQueries:
    def __init__(self, async_session: async_sessionmaker[AsyncSession]):
        self.db = async_session

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
