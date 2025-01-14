from enum import Enum
from fastapi_events.typing import Event
from fastapi_events.handlers.base import BaseEventHandler
from fastapi_events.registry.payload_schema import registry as payload_schema
from pydantic import BaseModel, Field
from datetime import datetime


class UserEvents(Enum):
    SIGNED_UP = "USER_SIGNED_UP"
    ACTIVATED = "USER_ACTIVATED"
    RESET_PASSWORD = "USER_PASSWORD"
    OTP = "USER_OTP"
    STRANGE_LOCATION = "USER_LOCATION"
    BLOCKED = "USER_BLOCKED"
    BOOKING = "USER_BOOKING"
    USER_AUTH_SUCCESS = "USER_AUTH_SUCCESS"
    USER_AUTH_FAILURE = "USER_AUTH_FAILURE"
    UNKNOWN_USER_AUTH_FAILURE = "BRUTE_FORCE"
    UPDATED_USER_INFO = "UPDATED_USER"


@payload_schema.register(event_name=UserEvents.SIGNED_UP)
class SignUpPayload(BaseModel):
    userid: str
    created_at: datetime = Field(alias="createdAt", serialization_alias="createdAt")


class APIEventHandler(BaseEventHandler):

    async def handle(self, event: Event) -> None:
        event_name, payload = event
        print(event_name, payload)
        """
        Handle events one by one
        """
        # return None
