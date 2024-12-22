from datetime import datetime, timedelta
from pytz import timezone
import uuid


class Utility:
    def __init__(self, config):
        self.cfg = config

    def time_now(self) -> datetime:
        now_utc = datetime.now()
        now_est = now_utc.astimezone(timezone("Europe/Stockholm"))
        return now_est

    def time_now_utc(self) -> datetime:
        return datetime.now()

    def time_then(self) -> datetime:
        return datetime(1980, 1, 1)

    def get_indent(self) -> str:
        return str(uuid.uuid4())

    def time_delta(self, min: int) -> timedelta:
        return timedelta(minutes=min)
