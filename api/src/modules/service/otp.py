from modules.repository.request_models.user import (
    OtpRequest,
    GetOtpResponse,
    NewOtpRequest,
)
from modules.repository.schema.users import Otp, User
from modules.service.email import EmailHandler
from modules.utils.misc import get_indent, time_delta, time_now_utc
from fastapi_events.dispatcher import dispatch


TOKEN_INVALID = "invalidToken"
TOKEN_EXPIRED = "expired"
TOKEN_VALID = "valid"
USER_ENABLED = "enabled"


class OtpHandler(EmailHandler):
    async def generate_otp(self, req: OtpRequest) -> GetOtpResponse:
        token: str = self.generate_confirmation_token(email=req.email)
        expiry = time_now_utc() + time_delta(self.config.otp_expiry)
        otp: Otp = Otp(
            id=get_indent(),
            email=req.email,
            userid=req.userid,
            expiry=expiry,
            token=token,
        )
        new_otp = await self.create_otp_query(otp)
        req.result.token = new_otp.token
        return req.req_success("Otp created for user with id: {req.userid}")

    async def verify_otp(self, token: str) -> str:
        otp: Otp = await self.get_otp_by_token_query(token=token)
        if otp is None:
            return TOKEN_INVALID
        valid = await self.is_otp_valid()
        if not valid:
            return TOKEN_EXPIRED
        user: User = await self.get_user_by_id(otp.userid)
        if user.enabled:
            return USER_ENABLED
        user.enabled = True
        await self.update_user_query(user.id, user)
        await self.delete_otp_query(otp.id)
        return TOKEN_VALID

    async def is_otp_valid(self, otp: Otp) -> bool:
        if (
            self.verify_email_token(otp.token, self.cf.otp_expiry * 60)
            or otp.expiry < time_now_utc()
        ):
            return True
        return False

    async def generate_new_otp(self, req: NewOtpRequest) -> GetOtpResponse:
        otp: Otp = await self.get_otp_by_email_query(req.email)
        if otp is not None:
            otp.token = self.generate_confirmation_token(req.email)
            otp.expiry = time_now_utc() + time_delta(self.config.otp_expiry)
            await self.update_otp_query(otp.id, otp)
            return req.req_success("New Otp created for user with email: {req.email}")
        return req.req_failure("new Otp cant be created")


# Registration complete event
