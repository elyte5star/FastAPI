from modules.repository.schema.users import User
from fastapi import Request
from modules.settings.configuration import ApiConfig
from collections import OrderedDict
from modules.repository.queries.auth import AuthQueries
from modules.utils.misc import time_now_utc, time_delta


class LoginAttempthandler(AuthQueries):
    def __init__(self, config: ApiConfig):
        super().__init__(config)
        self.attempts_cache: OrderedDict = OrderedDict()
        self.active_user_store: list = []
        self.attempts: int = 0

    def is_ip_blocked(self, request: Request) -> bool:
        client_ip: str = self.get_client_ip_address(request)
        if self.attempts_cache.get(client_ip) is not None:
            return self.attempts_cache.get(client_ip) >= self.cf.max_login_attempt
        return False

    def increase_unknown_user_failed_attempt(self, key: str) -> None:
        if key in self.attempts_cache:
            self.attempts += 1
            self.attempts_cache[key] = self.attempts
        else:
            self.attempts_cache[key] = 1

    def reset_failed_attempts_cache(self) -> None:
        self.attempts_cache.clear()

    def get_client_ip_address(self, request: Request) -> str:
        xf_header = request.headers.get("X-Forwarded-For")
        if xf_header is not None:
            return xf_header.split(",")[0]
        return request.client.host

    def get_cookies(self, name: str, request: Request) -> str | None:
        cookie = request.cookies.get(name)
        if cookie is not None:
            return cookie
        self.cf.logger.warning(f"Cookie with name :{name} not found!")
        return None

    def reset_user_failed_attempts(self, user: User) -> None:
        userid = user.id
        user.failed_attempts = 0
        self.update_user_query(userid, user)

    def lock_user_account(self, user: User) -> None:
        userid = user.id
        user.is_locked = True
        user.lock_time = time_now_utc()
        self.update_user_query(userid, user)
        self.cf.logger.warning(f"User with id: {userid} is locked")

    def increase_user_failed_attempts(self, user: User) -> None:
        user_failed_attempts = user.failed_attempts
        if user_failed_attempts >= self.cf.max_login_attempt:
            self.lock_user_account(user)
        else:
            userid = user.id
            user.failed_attempts = user_failed_attempts + 1
            self.update_user_query(userid, user)

    def unlock_when_time_expired(self, user: User) -> bool:
        lock_time = user.lock_time
        current_time = time_now_utc()
        expire = lock_time + time_delta(self.cf.lock_duration)
        if expire < current_time:
            userid = user.id
            user.is_locked = False
            user.lock_time = None
            user.failed_attempts = 0
            self.update_user_query(userid, user)
            return True
        return False

    async def login_notification(self) -> None:
        pass
