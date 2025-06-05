from datetime import datetime, timedelta
from pytz import timezone
import uuid
from fastapi.encoders import jsonable_encoder
import string
import secrets
import bcrypt
from functools import lru_cache, wraps


def date_time_now_local_tz() -> datetime:
    return datetime.now().astimezone(timezone("Europe/Stockholm"))


def date_time_now_utc_tz() -> datetime:
    return datetime.now().astimezone(timezone("UTC"))


def time_then() -> datetime:
    return datetime(1971, 1, 1)


def date_time_now_utc() -> datetime:
    return datetime.now()


def get_indent() -> str:
    return str(uuid.uuid4())


def time_delta(min: int) -> timedelta:
    return timedelta(minutes=min)


def obj_as_json(obj):
    return jsonable_encoder(obj)


def hash_password(plain_password: str, salt: int, encoding: str) -> bytes:
    hashed_password = bcrypt.hashpw(
        plain_password.encode(encoding), bcrypt.gensalt(salt)
    ).decode(encoding)
    return hashed_password


def timed_lru_cache(minutes: int, maxsize: int = 128):
    def wrapper_cache(func):
        func = lru_cache(maxsize=maxsize)(func)
        func.lifetime = time_delta(minutes)
        func.expiration = time_now_utc() + func.lifetime

        @wraps(func)
        def wrapped_func(*args, **kwargs):
            if time_now_utc() >= func.expiration:
                func.cache_clear()
                func.expiration = time_now_utc() + func.lifetime

            return func(*args, **kwargs)

        return wrapped_func

    return wrapper_cache


def create_password(size: int, salt: int, encoding: str) -> tuple[str, bytes]:
    chars = (
        string.digits
        + string.ascii_letters
        + string.punctuation.replace("'", "").replace('"', "")
    )
    plain_password = "".join(secrets.choice(chars) for _ in range(size))
    hashed_password = hash_password(plain_password, salt, encoding)
    return (plain_password, hashed_password)


def serialize_datetime(obj):
    if isinstance(obj, datetime):
        return obj.isoformat()
    raise TypeError("Type not serializable")


class AsyncIteratorWrapper:
    """The following is a utility class that transforms a
    regular iterable to an asynchronous one.

    link: https://www.python.org/dev/peps/pep-0492/#example-2
    """

    def __init__(self, obj):
        self._it = iter(obj)

    def __aiter__(self):
        return self

    async def __anext__(self):
        try:
            value = next(self._it)
        except StopIteration:
            raise StopAsyncIteration
        return value


# def random_date(self, start_date, range_in_days):
#     days_to_add = np.arange(0, range_in_days)
#     rd = np.datetime64(start_date) + np.random.choice(days_to_add)
#     return str(rd)
