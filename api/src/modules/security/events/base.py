from enum import Enum
from fastapi_events.typing import Event
from fastapi_events.handlers.base import BaseEventHandler


class UserEvents(Enum):
    SIGNED_UP = "USER_SIGNED_UP"
    ACTIVATED = "USER_ACTIVATED"
    RESET_PASSWORD = "USER_PASSWORD"
    OTP = "USER_OTP"
    STRANGE_LOCATION = "USER_LOCATION"
    BLOCKED = "USER_BLOCKED"
    BOOKING = "USER_BOOKING"
    AUTHENTICATION = "USER_AUTH"


class APIEventHandler(BaseEventHandler):
    async def handle(self, event: Event) -> None:
        """
        Handle events one by one
        """
        pass
