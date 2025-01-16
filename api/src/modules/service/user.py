from modules.repository.request_models.user import (
    CreateUserRequest,
    GetUserRequest,
    GetUsersRequest,
    OtpRequest,
    GetOtpResponse,
    NewOtpRequest,
    DeleteUserRequest,
)
from modules.repository.response_models.user import (
    CreateUserResponse,
    GetUserResponse,
    UserDetails,
    GetUsersResponse,
    BaseResponse,
    CreatedUserData,
)
from modules.repository.schema.users import (
    User,
    Otp,
    PasswordResetToken,
    UserLocation,
)
import bcrypt

from fastapi import Request
from fastapi_events.dispatcher import dispatch
from modules.utils.misc import get_indent, time_delta, time_now_utc
from modules.security.events.base import UserEvents
from modules.repository.queries.user import UserQueries
from itsdangerous import URLSafeTimedSerializer, BadTimeSignature, SignatureExpired

TOKEN_INVALID = "invalidToken"
TOKEN_EXPIRED = "expired"
TOKEN_VALID = "valid"
USER_ENABLED = "enabled"

LOCAL_HOST_ADDRESSES = ["0:0:0:0:0:0:0:1", "127.0.1.1", "127.0.0.1"]


class UserHandler(UserQueries):
    async def _create_user(
        self, req: CreateUserRequest, request: Request
    ) -> CreateUserResponse:
        user_exist = await self.check_if_user_exist(
            req.email, req.username, req.telephone
        )
        if user_exist is None:
            new_user_password = req.password.get_secret_value()
            hashed_password = self.hash_password(new_user_password)
            new_user = User(
                id=get_indent(),
                email=req.email,
                username=req.username,
                password=hashed_password,
                telephone=req.telephone,
                discount=0.0,
                created_by=req.username,
                failed_attempts=0,
            )
            user = await self.create_user_query(new_user)
            if user is not None:
                response_data = CreatedUserData(
                    userid=user.id, createdAt=user.created_at
                )
                req.result.data = response_data
                await self.add_user_location(user, self.get_client_ip_address(request))
                model_dict = response_data.model_dump(by_alias=True)
                event_payload = model_dict | {"app_url": self.get_app_url(request)}
                dispatch(UserEvents.SIGNED_UP, event_payload)
                return req.req_success("New user created!")
            return req.req_failure("Couldn't create account ,try later.")
        return req.req_failure("User exist")

    def hash_password(self, plain_password: str) -> bytes:
        hashed_password = bcrypt.hashpw(
            plain_password.encode(self.cf.encoding),
            bcrypt.gensalt(rounds=self.cf.rounds),
        ).decode(self.cf.encoding)
        return hashed_password

    def check_if_valid_old_password(self, user: User, password: str) -> bool:
        return bcrypt.checkpw(
            password.encode(self.cf.encoding),
            user.password.encode(self.cf.encoding),
        )

    def change_user_password(self, user: User, password: str) -> None:
        hashed_password = self.hash_password(password)
        user.password = hashed_password
        self.update_user_query(user.id, user)

    async def _get_user(self, req: GetUserRequest) -> GetUserResponse:
        # include RBAC
        user = await self.get_user_by_id(req.userid)
        if user is not None:
            user_info = UserDetails(
                userid=user.id,
                createdAt=user.created_at,
                lastModifiedAt=user.modified_at,
                lastModifiedBy=user.modified_by,
                createdBy=user.created_by,
                email=user.email,
                password="********",
                username=user.username,
                active=user.active,
                admin=user.admin,
                enabled=user.enabled,
                telephone=user.telephone,
                failedAttempt=user.failed_attempts,
                discount=user.discount,
                lockTime=user.lock_time,
                IsUsing2FA=user.is_using_mfa,
            )

            req.result.user = user_info
            return req.req_success(f"User with userid {req.userid} found")
        return req.req_failure(f"User with userid {req.userid} not found")

    # ADMIN RIGHTS ONLY
    async def _get_users(self, req: GetUsersRequest) -> GetUsersResponse:
        users = await self.get_users_query()
        result: list[UserDetails] = [
            UserDetails(
                userid=user.id,
                createdAt=user.created_at,
                lastModifiedAt=user.modified_at,
                lastModifiedBy=user.modified_by,
                createdBy=user.created_by,
                email=user.email,
                password="********",
                username=user.username,
                active=user.active,
                admin=user.admin,
                enabled=user.enabled,
                telephone=user.telephone,
                failedAttempt=user.failed_attempts,
                discount=user.discount,
                lockTime=user.lock_time,
                IsUsing2FA=user.is_using_mfa,
            )
            for user in users
        ]
        req.result.users = result
        return req.req_success(f"Total number of users: {len(users)}")

    async def _delete_user(self, req: DeleteUserRequest) -> BaseResponse:
        user = await self.get_user_by_id(req.userid)
        if user is None:
            return req.req_failure(f"No user with id :: {req.userid}")
        otp: Otp = await self.get_otp_by_user_query(user)
        if otp is not None:
            await self.delete_otp_by_id_query(otp.id)
        password_rest_token: PasswordResetToken = (
            await self.find_passw_reset_token_by_user_query(user)
        )
        if password_rest_token is not None:
            await self.delete_passw_reset_token_by_id_query(password_rest_token.id)
        await self.delete_user_query(user.id)
        return req.req_success(f"User with id::{req.userid} deleted")

    # OTP
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
        return req.req_success("Otp created for user with id ::{req.userid}")

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
            return req.req_success("New Otp created for user with email:: {req.email}")
        return req.req_failure("new Otp cant be created")

    def generate_confirmation_token(self, email: str):
        serializer = URLSafeTimedSerializer(
            self.cf.secret_key, salt=self.cf.security_salt
        )
        return serializer.dumps(email)

    def verify_email_token(self, token: str, expiration: int = 3600) -> bool:
        serializer = URLSafeTimedSerializer(self.config.secret_key)
        try:
            _ = serializer.loads(token, salt=self.config.rounds, max_age=expiration)
            return True
        except SignatureExpired:
            return False
        except BadTimeSignature:
            return False

    # LOCATION

    async def is_valid_new_location_token(self, token: str) -> str | None:
        loc_token = await self.find_new_location_by_token_query(token)
        if loc_token is None:
            return None
        user_loc = await self.find_new_location_by_token_query(loc_token)
        user_loc.enabled = True
        await self.update_user_loc_query(user_loc.id, user_loc)
        await self.del_new_location_query(loc_token.id)
        return user_loc.country

    async def add_user_location(self, user: User, ip: str):
        if not self.is_geo_ip_enabled():
            self.cf.logger.warning("GEO IP DISABALED BY ADMIN")
            return None
        country = (
            "NORWAY"
            if self.check_if_ip_is_local(ip)
            else await self.get_country_from_ip(ip)
        )
        user_loc = UserLocation(
            id=get_indent(), country=country, owner=user, enabled=True
        )
        await self.create_user_location_query(user_loc)

    def check_if_ip_is_local(self, ip: str) -> bool:
        if ip in LOCAL_HOST_ADDRESSES:
            return True
        return False

    def get_client_ip_address(self, request: Request) -> str:
        xf_header = request.headers.get("X-Forwarded-For")
        if xf_header is not None:
            return xf_header.split(",")[0]
        # return "41.238.0.198"  # for testing Egypt
        return request.client.host
