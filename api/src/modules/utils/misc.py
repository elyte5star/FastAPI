from datetime import datetime, timedelta
from pytz import timezone
import uuid
from fastapi.encoders import jsonable_encoder


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


def obj_as_json(obj):
    return jsonable_encoder(obj)


def serialize_datetime(obj):
    if isinstance(obj, datetime):
        return obj.isoformat()
    raise TypeError("Type not serializable")
