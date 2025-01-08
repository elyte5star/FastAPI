from modules.settings.configuration import ApiConfig
from functools import lru_cache, wraps
from modules.utils.misc import time_now_utc, time_delta


class Cache:
    def __init__(self, config: ApiConfig):
        pass

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
