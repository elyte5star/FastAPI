from datetime import datetime, timedelta
from pytz import timezone
import uuid


def time_now() -> datetime:
    now_utc = datetime.now()
    now_est = now_utc.astimezone(timezone("Europe/Stockholm"))
    return now_est


def time_now_utc() -> datetime:
    return datetime.now()


def time_then() -> datetime:
    return datetime(1980, 1, 1)


def get_indent() -> str:
    return str(uuid.uuid4())


def time_delta(min: int) -> timedelta:
    return timedelta(minutes=min)
