from enum import Enum
from fastapi_events.typing import Event
from fastapi_events.handlers.base import BaseEventHandler
from fastapi_events.registry.payload_schema import registry as payload_schema
from pydantic import BaseModel, EmailStr
from datetime import datetime
from modules.settings.configuration import ApiConfig
from modules.security.events.email import EmailService
from modules.repository.request_models.user import EmailRequestSchema
from modules.utils.misc import time_now_utc


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
    UNKNOWN_DEVICE_LOGIN = "NEW_DEVICE_LOGIN"
    UPDATED_USER_INFO = "UPDATED_USER"


@payload_schema.register(event_name=UserEvents.SIGNED_UP)
class SignUpPayload(BaseModel):
    userid: str
    email: EmailStr
    expiry: datetime
    token: str
    app_url: str
    # locale:str future?


@payload_schema.register(event_name=UserEvents.STRANGE_LOCATION)
class StrangeLocation(BaseModel):
    username: str
    ip: str
    token: str
    app_url: str
    email: EmailStr
    country: str
    # locale:str future?


#@payload_schema.register(event_name=UserEvents.UNKNOWN_DEVICE_LOGIN)
class NewDeviceLogin(BaseModel):
    username: str
    email: EmailStr
    device_details: str
    ip: str
    location: str
    app_url: str
    # locale:str future?

@payload_schema.register(event_name=UserEvents.BLOCKED)
class BlockedUserAccount(BaseModel):
    userid: str
    username: str
    email: EmailStr
    blocked_date: datetime


class APIEventsHandler(EmailService):

    async def unknown_device_notification(self, event_payload: NewDeviceLogin):
        subject = "New Login Notification"
        body = {
            "device_details": event_payload.device_details,
            "location": event_payload.location,
            "ip": event_payload.ip,
            "home": event_payload.app_url,
        }
        email_req = EmailRequestSchema(
            subject=subject,
            recipients=["checkuti@gmail.com"],
            body=body,
            template_name="new_device.html"
        )   
        is_sent = await self.send_email_to_user(email_req)
        if is_sent:
            self.config.logger.info(f"Email sent to :{event_payload.email}")
            return True
        self.config.logger.warning(f"Email not sent to :{event_payload.email}")
        return False

    async def confirm_registration_notification(
        self,
        event_payload: SignUpPayload,
    ):
        subject = "Registration Confirmation"
        body = {
            "confirmationUrl": (
                event_payload.app_url
                + "/registrationConfirm?token="
                + event_payload.token
            ),
            "message": f"""You registered successfully.
            Your ID is :{event_payload.userid}.
            To confirm your registration, please click on the below link.""",
            "expiry": f" The link expires in {event_payload.expiry} seconds",
            "home": event_payload.app_url,
        }
        email_req = EmailRequestSchema(
            subject=subject,
            recipients=[event_payload.email],
            body=body,
            template_name="confirm_registration.html",
        )
        is_sent = await self.send_email_to_user(email_req)
        if is_sent:
            self.config.logger.info(f"Email sent to :{event_payload.email}")
            return True
        self.config.logger.warning(f"Email not sent to :{event_payload.email}")
        return False

    async def strange_location__login_notification(
        self,
        event_payload: StrangeLocation,
    ):  
        subject = "Login attempt from different location"
        print(event_payload)
        body = {
            "country": event_payload.country,
            "ip": event_payload.ip,
            "Date": time_now_utc(),
            "enableLocationLink": event_payload.app_url
            + "/user/enableNewLoc?token="
            + event_payload.token,
            "changePassUri": event_payload.app_url + "/user/updatePassword",
        }
        email_req = EmailRequestSchema(
            subject=subject,
            recipients=["checkuti@gmail.com"],
            body=body,
            template_name="unusual_location.html",
        )
        is_sent = await self.send_email_to_user(email_req)
        if is_sent:
            self.config.logger.info(f"Email sent to :{event_payload.email}")
            return True
        self.config.logger.warning(f"Email not sent to :{event_payload.email}")
        return False


class APIEvents(BaseEventHandler):
    def __init__(self, config: ApiConfig) -> None:
        self._handler = APIEventsHandler(config)

    async def handle(self, event: Event) -> None:
        match event[0]:
            case UserEvents.SIGNED_UP:
                payload = event[1]
                await self._handler.confirm_registration_notification(payload)
            case UserEvents.UNKNOWN_DEVICE_LOGIN:
                payload = event[1]
                await self._handler.unknown_device_notification(payload)
            case UserEvents.BLOCKED:
                payload = event[1]
            case UserEvents.STRANGE_LOCATION:
                payload = event[1]
                await self._handler.strange_location__login_notification(payload)
            case _:
                return "UNKNOWN EVENT ALERT ADMIN"
