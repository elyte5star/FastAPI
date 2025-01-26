from modules.security.listeners.email import EmailService
from modules.security.events.base import (
    NewDeviceLogin,
    SignUpPayload,
    StrangeLocation,
)
from modules.repository.request_models.user import EmailRequestSchema
from modules.utils.misc import time_now_utc


class APIEventsListener(EmailService):

    async def unknown_device_notification(self, event_payload: NewDeviceLogin):
        subject = "New Login Notification"
        body = {
            "Device details": event_payload.device_details,
            "Location": event_payload.location,
            "IP Address": event_payload.ip,
        }
        email_req = EmailRequestSchema(
            subject=subject,
            recipients=[event_payload.email],
            body=body,
        )
        is_sent = await self.send_plain_text(email_req)
        if is_sent:
            self.config.logger.info(f"Email sent to :{event_payload.email}")
            return True
        self.config.logger.warning(f"Email not sent to :{event_payload.email}")
        return False

    async def confirm_registration_notifiction(
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

    async def strange_location__login_notifiction(
        self,
        event_payload: StrangeLocation,
    ):
        subject = "Login attempt from different location"
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
            recipients=[event_payload.email],
            body=body,
            template_name="unusual_location.html",
        )
        is_sent = await self.send_email_to_user(email_req)
        if is_sent:
            self.config.logger.info(f"Email sent to :{event_payload.email}")
            return True
        self.config.logger.warning(f"Email not sent to :{event_payload.email}")
        return False
