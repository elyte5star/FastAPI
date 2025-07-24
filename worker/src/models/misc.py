import uuid
from datetime import datetime




def time_then() -> datetime:
    return datetime(1971, 1, 1)


def date_time_now_utc() -> datetime:
    return datetime.now()


def get_indent() -> str:
    return str(uuid.uuid4())
