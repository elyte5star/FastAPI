from datetime import datetime, timedelta
from pytz import timezone
import uuid
from fastapi.encoders import jsonable_encoder
import string, secrets
import bcrypt


def time_now() -> datetime:
    now_utc = datetime.now()
    now_est = now_utc.astimezone(timezone("Europe/Stockholm"))
    return now_est


def time_now_utc() -> datetime:
    return datetime.now()


def time_then() -> datetime:
    return datetime(1971, 1, 1)


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


# def random_date(self, start_date, range_in_days):
#     days_to_add = np.arange(0, range_in_days)
#     rd = np.datetime64(start_date) + np.random.choice(days_to_add)
#     return str(rd)
