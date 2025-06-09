from modules.repository.request_models.user import (
    CreateUserRequest,
    GetUserRequest,
    GetUsersRequest,
    OtpRequest,
    DeleteUserRequest,
    NewOtpRequest,
    VerifyRegistrationOtpRequest,
    UserEnquiryRequest,
    ResetUserPasswordRequest,
    UpdateUserPasswordRequest,
    SaveUserPassswordRequest,
    LockUserAccountRequest,
)
from modules.repository.response_models.user import (
    CreateUserResponse,
    GetUserResponse,
    GetUsersResponse,
    BaseResponse,
    ClientEnquiryResponse,
    UserDisplay,
)
from modules.database.schema.user import (
    User,
    Otp,
    PasswordResetToken,
    UserLocation,
    Enquiry,
)
import bcrypt
from fastapi import Request
from fastapi_events.dispatcher import dispatch
from modules.utils.misc import (
    get_indent,
    time_delta,
    date_time_now_utc,
    datetime,
)
from modules.security.events.base import (
    UserEvents,
    SignUpPayload,
    ClientEnquiry,
    ResetUserPassword,
    UserPasswordChange,
)
from modules.repository.queries.user import UserQueries
from pydantic import SecretStr


TOKEN_INVALID = "invalid_token"
TOKEN_EXPIRED = "expired"
TOKEN_VALID = "valid"
USER_ENABLED = "enabled"


class UserHandler(UserQueries):
    async def _create_user(
        self, req: CreateUserRequest, request: Request
    ) -> BaseResponse:
        user_exist = await self.check_if_user_exist(
            req.new_user.email, req.new_user.username, req.new_user.telephone
        )
        if user_exist is None:
            new_user_password = req.new_user.password.get_secret_value()
            hashed_password = self.hash_password(new_user_password)
            new_user = User(
                id=get_indent(),
                email=req.new_user.email,
                username=req.new_user.username,
                password=hashed_password,
                telephone=req.new_user.telephone,
                discount=0.0,
                created_by=req.new_user.username,
                active=True,
            )
            user_in_db = await self.create_user_query(new_user)
            pydantic_model = UserDisplay.model_validate(user_in_db)
            req.result.new_user = pydantic_model
            await self.on_successfull_registration(user_in_db, request)
            return req.req_success("New user created!")
        return req.req_failure("User exist")

    async def on_successfull_registration(
        self,
        new_user: User,
        request: Request,
    ) -> None:
        ip = self.get_client_ip_address(request)
        app_url = self.get_app_url(request)
        await self.add_user_location(new_user, ip)
        otp_token = await self.generate_confirmation_token(
            new_user.id,
            new_user.email,
        )
        event_payload = SignUpPayload(
            userid=new_user.id,
            username=new_user.username,
            email=new_user.email,
            token=otp_token.token,
            expiry=otp_token.expiry,
            app_url=app_url,
        )
        dispatch(UserEvents.SIGNED_UP, event_payload)

    # OTP ADMIN REQUEST
    async def _create_verification_otp(
        self, req: OtpRequest, request: Request
    ) -> BaseResponse:
        user = await self.find_user_by_email(req.email)
        if user is None:
            return req.req_failure(f"User with email {req.email} not found")
        app_url = self.get_app_url(request)
        new_otp = await self.generate_confirmation_token(
            user.id,
            user.email,
        )
        event_payload = SignUpPayload(
            userid=user.id,
            email=user.email,
            username=user.username,
            token=new_otp.token,
            expiry=new_otp.expiry,
            app_url=app_url,
        )
        dispatch(UserEvents.SIGNED_UP, event_payload)
        return req.req_success(f"Otp created and sent to email::{user.email}")

    async def generate_confirmation_token(
        self,
        user_id: str,
        email: str,
    ) -> Otp:
        token = self.create_timed_token(email)
        expiry = date_time_now_utc() + time_delta(self.cf.otp_expiry)
        otp = await self.get_otp_by_email_query(email)
        if otp is None:
            new_otp = Otp(
                id=get_indent(),
                email=email,
                user_id=user_id,
                expiry=expiry,
                token=token,
            )
            new_otp = await self.create_otp_query(new_otp)
            return new_otp
        changes = {"token": token, "expiry": expiry}
        await self.update_otp_query(otp.id, changes)
        return otp

    # USER NEW OTP REQUEST
    async def _generate_new_otp(
        self,
        req: NewOtpRequest,
        request: Request,
    ) -> BaseResponse:
        otp = await self.get_otp_by_token_query(req.token)
        if otp is not None:
            token = self.create_timed_token(otp.owner.email)
            app_url = self.get_app_url(request)
            expiry = date_time_now_utc() + time_delta(self.cf.otp_expiry)
            changes = {"token": token, "expiry": expiry}
            await self.update_otp_query(otp.id, changes)
            event_payload = SignUpPayload(
                userid=otp.owner.id,
                username=otp.owner.username,
                email=otp.owner.email,
                token=token,
                expiry=expiry,
                app_url=app_url,
            )
            dispatch(UserEvents.SIGNED_UP, event_payload)
            return req.req_success(
                f"New Otp created for user with email::{otp.owner.email}",
            )
        return req.req_failure("new Otp cant be created")

    async def confirm_user_registration(
        self,
        req: VerifyRegistrationOtpRequest,
    ) -> BaseResponse:
        result = await self.verify_otp(req.token)
        if result == "valid":
            return req.req_success("Your account verified successfully")
        elif result == "expired" or result == "invalid_token":
            return req.req_failure("invalid_token or expired token")
        return req.req_success("Your account is already activated")

    async def verify_otp(self, token: str) -> str:
        otp = await self.get_otp_by_token_query(token)
        if otp is None:
            return TOKEN_INVALID
        valid = await self.is_otp_valid(otp.token, otp.expiry)
        if not valid:
            return TOKEN_EXPIRED
        user = otp.owner
        if user.enabled:
            return USER_ENABLED
        await self.activate_new_user_account(user.id)
        await self.delete_otp_by_id_query(otp.id)
        return TOKEN_VALID

    async def is_otp_valid(self, token: str, expiry: datetime) -> bool:
        if (
            self.verify_email_token(token, self.cf.otp_expiry * 60)
            and expiry > date_time_now_utc()
        ):
            return True
        return False

    def hash_password(self, plain_password: str) -> str:
        hashed_password = bcrypt.hashpw(
            plain_password.encode(self.cf.encoding),
            bcrypt.gensalt(rounds=self.cf.rounds),
        ).decode(self.cf.encoding)
        return hashed_password

    async def _get_user(self, req: GetUserRequest) -> GetUserResponse:
        if req.credentials is not None and req.credentials.user_id != req.userid:
            self.logger.warning(
                f"illegal operation by {req.credentials.userid}",
            )
            return req.req_failure("Forbidden: Access is denied")
        user_in_db = await self.find_user_by_id(req.userid)
        if user_in_db is None:
            return req.req_failure(f"User with id {req.userid} not found")
        pydantic_model = UserDisplay.model_validate(user_in_db)
        req.result.user = pydantic_model
        return req.req_success(f"User with id {req.userid} found")

    # ADMIN RIGHTS ONLY
    async def _get_users(self, req: GetUsersRequest) -> GetUsersResponse:
        users = await self.get_users_query()
        users = [
            UserDisplay.model_validate(user_in_db)
            for user_in_db in await self.get_users_query()
        ]
        req.result.users = users
        return req.req_success(f"Total number of users: {len(users)}")

    async def _delete_user(self, req: DeleteUserRequest) -> BaseResponse:
        if req.credentials is not None and req.credentials.user_id != req.userid:
            self.logger.warning(
                f"illegal operation by {req.credentials.username}",
            )
            return req.req_failure("Forbidden: Access is denied")
        user = await self.find_user_by_id(req.userid)
        if user is None:
            return req.req_failure(f"No user with id: {req.userid}")
        otp = await self.get_otp_by_user_query(user)
        if otp is not None:
            await self.delete_otp_by_id_query(otp.id)
        password_reset_token = await self.find_passw_reset_token_by_user_query(
            user,
        )
        if password_reset_token is not None:
            await self.delete_passw_reset_token_by_id_query(
                password_reset_token.id,
            )
        await self.delete_user_query(user.id)
        return req.req_success(f"User with id: {req.userid} deleted")

    # ADMIN RIGHTS ONLY
    async def _lock_user(
        self,
        req: LockUserAccountRequest,
    ) -> BaseResponse:
        if req.credentials is not None and req.credentials.userid == req.userid:
            return req.req_failure("You cant lock your own account")
        user = await self.find_user_by_id(req.userid)
        if user is None:
            return req.req_failure(f"No user with id: {req.userid}")
        await self.lock_user_account_query(user)
        self.logger.warning(
            f"""account with id: {req.userid} was locked by
            admin with userId: {req.credentials.user_id}"""
        )
        return req.req_success(f"User with id:{req.userid} locked")

    # LOCATION

    async def add_user_location(self, user: User, ip: str):
        if not self.is_geo_ip_enabled():
            self.logger.warning("GEO IP DISABALED BY ADMIN")
            return None
        country, _ = await self.get_location_from_ip(ip)
        user_loc = UserLocation(
            id=get_indent(), country=country, owner=user, enabled=True
        )
        await self.create_user_location_query(user_loc)

    # RESET USER PASSWORD (user forgot password)
    async def _reset_user_password(
        self, req: ResetUserPasswordRequest, request: Request
    ) -> BaseResponse:
        user = await self.find_user_by_email(req.data.email)
        if user is not None:
            token = self.create_timed_token(user.email)
            expiry = date_time_now_utc() + time_delta(self.cf.otp_expiry)
            password_reset_token = await self.find_passw_token_by_user_query(
                user,
            )
            if password_reset_token is None:
                new_reset_token = PasswordResetToken(
                    id=get_indent(), token=token, expiry=expiry, userid=user.id
                )
                await self.create_pass_reset_query(new_reset_token)
            else:
                changes = {"token": token, "expiry": expiry}
                _ = await self.update_pass_token_query(
                    password_reset_token.id,
                    changes,
                )

            event_payload = ResetUserPassword(
                username=user.username,
                email=user.email,
                token=token,
                expiry=expiry,
                app_url=self.get_app_url(request),
            )
            dispatch(UserEvents.RESET_PASSWORD, event_payload)
            return req.req_success(
                f"New password reset token sent to: {user.email}",
            )
        return req.req_failure("User doesn't exist")

    # Change user password
    async def _save_user_password(self, req: SaveUserPassswordRequest):
        result = await self.validate_password_reset_token(
            req.data.token, req.data.new_password
        )
        if result == "valid":
            return req.req_success("Password reset successfully")
        return req.req_failure("invalid_token or expired token")

    async def validate_password_reset_token(
        self,
        token: str,
        new_password: str,
    ):
        pass_reset_token = await self.find_passw_token_by_token_query(token)
        if pass_reset_token is None:
            return TOKEN_INVALID
        valid = await self.is_otp_valid(
            pass_reset_token.token,
            pass_reset_token.expiry,
        )
        if not valid:
            return TOKEN_EXPIRED
        user = pass_reset_token.owner
        await self.change_user_password(user, user.username, new_password)
        return TOKEN_VALID

    # Update user password
    async def _update_user_password(self, req: UpdateUserPasswordRequest):
        if req.credentials.userid != req.userid:
            self.logger.warning(
                f"illegal operation by {req.credentials.username}",
            )
            return req.req_failure("Forbidden: Access is denied")
        user = await self.find_user_by_email(req.credentials.email)
        if user is not None:
            if self.check_if_valid_old_password(
                user.password,
                req.data.old_password,
            ):
                await self.change_user_password(
                    user, req.credentials.username, req.data.new_password
                )
                return req.req_success("Password updated successfully")
        return req.req_failure("Invalid old password or user does not exist")

    def check_if_valid_old_password(
        self,
        password_in_db: str,
        old_password: str,
    ) -> bool:
        return (
            True
            if bcrypt.checkpw(
                old_password.encode(self.cf.encoding),
                password_in_db.encode(self.cf.encoding),
            )
            else False
        )

    async def change_user_password(
        self, user: User, modified_by: str, password: SecretStr
    ) -> None:
        hashed_password = self.hash_password(password.get_secret_value())
        is_updated = await self.update_user_password_query(
            user.id,
            modified_by,
            hashed_password,
        )
        if is_updated:
            event_payload = UserPasswordChange(
                username=user.username, email=user.email, modified_by=modified_by
            )
            dispatch(UserEvents.UPDATED_USER_PASSWORD, event_payload)

    # USER ENQUIRY
    async def _create_enquiry(
        self,
        req: UserEnquiryRequest,
        request: Request,
    ) -> ClientEnquiryResponse:
        client_enquiry = Enquiry(
            **dict(
                id=get_indent(),
                client_name=req.enquiry.client_name,
                client_email=req.enquiry.client_email,
                country=req.enquiry.country,
                subject=req.enquiry.subject,
                message=req.enquiry.message,
                created_by=req.enquiry.client_name,
            )
        )
        result = await self.create_enquiry_query(client_enquiry)
        if result:
            req.result.eid = result
            event_payload = ClientEnquiry(
                message=req.enquiry.message,
                client_name=req.enquiry.client_name,
                eid=result,
                email=req.enquiry.client_email,
                app_url=self.get_app_url(request),
                expiry=date_time_now_utc() + time_delta(1600),
            )
            dispatch(UserEvents.CLIENT_ENQUIRY, event_payload)
            return req.req_success(f"Enquiry with id: {result} created")
        return req.req_failure("Couldn't create enquiry")
