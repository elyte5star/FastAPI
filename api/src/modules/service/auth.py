from modules.repository.request_models.auth import LoginRequest
import bcrypt
from modules.settings.configuration import ApiConfig


class Authentication:
    def __init__(self, config: ApiConfig) -> None:
        self.cf = config

    async def authenticate_user(self, req: LoginRequest):
        pass

    def verify_password(
        self, plain_password: str, hashed_password: str, selfcoding: str
    ) -> bool:
        if bcrypt.checkpw(
            plain_password.encode(self.cf.encoding),
            hashed_password.encode(self.cf.encoding),
        ):
            return True
        return False
