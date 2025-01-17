from modules.repository.schema.users import User
from fastapi import Request
from modules.settings.configuration import ApiConfig
from collections import OrderedDict
from modules.utils.misc import time_now_utc, time_delta
from modules.security.location import DifferentLocationChecker


class LoginAttemptChecker(DifferentLocationChecker):
    def __init__(self, config: ApiConfig):
        super().__init__(config)
        self.attempts_cache: OrderedDict = (
            OrderedDict()
        )  # { args : (timestamp, attempt_count)}
        self.active_user_store: list = []
        self.attempt_count: int = 0
        self.attempts_cache_size: int = 128

    def is_ip_blocked(self, request: Request) -> bool:
        client_ip: str = self.get_client_ip_address(request)
        if client_ip in self.attempts_cache:
            attempt_count, _ = self.attempts_cache.get(client_ip)
            if attempt_count >= self.cf.max_login_attempt:
                # update locktime
                self.attempts_cache[client_ip] = (
                    self.cf.max_login_attempt,
                    time_now_utc(),
                )
                return True
        return False

    def increase_failed_attempt_ip(self, key: str) -> None:
        if key in self.attempts_cache:
            self.attempt_count += 1
            self.attempts_cache.move_to_end(key)
            self.attempts_cache[key] = (self.attempt_count, time_now_utc())
            if len(self.attempts_cache) == self.attempts_cache_size:
                self.attempts_cache.popitem(last=False)  # LIFO
        else:
            self.attempt_count = 1
            self.attempts_cache[key] = (self.attempt_count, time_now_utc())

    def reset_failed_attempts_cache(self, key: str) -> bool:
        if key in self.attempts_cache:
            (
                attempt_count,
                timestamp,
            ) = self.attempts_cache.get(key)
            current_time = time_now_utc()
            expire = timestamp + time_delta(self.cf.lock_duration)
            if expire < current_time:
                del self.attempts_cache[key]
                self.attempt_count = 0
                self.cf.logger.warning(f"IP:{key} UNBLOCKED")
                return True
        return False

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
