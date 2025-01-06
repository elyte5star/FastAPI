from modules.repository.schema.users import User
from modules.security.cache import Cache
from fastapi import Request


class LoginAttempthandler(Cache):

    def is_ip_blocked(self) -> bool:
        return True

    def increase_unknown_user_failed_attempt(self, key: str) -> None:
        pass

    def reset_failed_attempts_cache(self) -> None:
        pass

    def get_client_ip_address(self, request: Request) -> str:
        xf_header = request.headers.get("X-Forwarded-For")
        if xf_header is not None:
            return xf_header.split(",")[0]
        return request.client.host

    def get_cookies(self, name: str, request: Request) -> str | None:
        cookie = request.cookies.get(name)
        return cookie

    def reset_user_failed_attempts(self, user: User) -> None:
        pass

    def lock_user_account(self, user: User) -> None:
        pass

    def increase_user_failed_attempt(self, key: str) -> None:
        pass

    def unlock_when_time_expired(self, user: User) -> bool:
        pass
