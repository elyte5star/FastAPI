from modules.repository.request_models.user import (
    CreateUserRequest,
    GetUserRequest,
    GetUsersRequest,
    OtpRequest,
    DeleteUserRequest,
    NewOtpRequest,
    EnableLocationRequest,
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
import geoip2.database

from fastapi import Request
from fastapi_events.dispatcher import dispatch
from modules.utils.misc import get_indent, time_delta, time_now
from modules.security.events.base import UserEvents, SignUpPayload
from modules.repository.queries.user import UserQueries


TOKEN_INVALID = "invalidToken"
TOKEN_EXPIRED = "expired"
TOKEN_VALID = "valid"
USER_ENABLED = "enabled"


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
                active=True,
            )
            user = await self.create_user_query(new_user)
            if user is not None:
                response_data = CreatedUserData(
                    userid=user.id, createdAt=user.created_at
                )
                req.result.data = response_data
                await self.on_successfull_registration(user, request)
                return req.req_success("New user created!")
            return req.req_failure("Couldn't create account ,try later.")
        return req.req_failure("User exist")

    async def on_successfull_registration(
        self,
        new_user: User,
        request: Request,
    ):
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
        user = await self.get_user_by_email(req.email)
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
        userid: str,
        email: str,
    ) -> Otp:
        token = self.create_timed_token(email)
        expiry = time_now() + time_delta(self.cf.otp_expiry)
        otp = await self.get_otp_by_email_query(email)
        if otp is None:
            new_otp = Otp(
                id=get_indent(),
                email=email,
                userid=userid,
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
            expiry = time_now() + time_delta(self.cf.otp_expiry)
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

    async def verify_otp(self, token: str) -> str:
        otp = await self.get_otp_by_token_query(token=token)
        if otp is None:
            return TOKEN_INVALID
        valid = await self.is_otp_valid(otp)
        if not valid:
            return TOKEN_EXPIRED
        user = await self.get_user_by_id(otp.userid)
        if user.enabled:
            return USER_ENABLED
        await self.update_user_query(user.id, dict(enabled=True))
        is_deleted = await self.delete_otp_by_id_query(otp.id)
        if not is_deleted:
            self.logger.warning("Old OTP not deleted")
        return TOKEN_VALID

    async def is_otp_valid(self, otp: Otp) -> bool:
        if (
            self.verify_email_token(otp.token, self.cf.otp_expiry * 60)
            or otp.expiry < time_now()
        ):
            return True
        return False

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
        self.update_user_query(user.id, dict(password=hashed_password))

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
            await self.delete_passw_reset_token_by_id_query(
                password_rest_token.id,
            )
        await self.delete_user_query(user.id)
        return req.req_success(f"User with id::{req.userid} deleted")

    # LOCATION
    async def _enable_new_loc(self, req: EnableLocationRequest) -> BaseResponse:
        country = self.is_valid_new_location_token(req.token)
        if country is not None:
            return req.req_success(f"{country} enabled.")
        return req.req_failure("Invalid Login Location!")

    async def is_valid_new_location_token(self, token: str) -> str | None:
        new_loc_token = await self.find_new_location_by_token_query(token)
        if new_loc_token is not None:
            user_loc = new_loc_token.location
            result = await self.update_user_loc_query(
                user_loc.id,
                dict(enabled=True),
            )
            self.logger.debug(result)
            await self.del_new_location_query(new_loc_token.id)
            return user_loc.country
        return None

    async def add_user_location(self, user: User, ip: str):
        if not self.is_geo_ip_enabled():
            self.logger.warning("GEO IP DISABALED BY ADMIN")
            return None
        country = await self.get_country_from_ip(ip)
        user_loc = UserLocation(
            id=get_indent(), country=country, owner=user, enabled=True
        )
        await self.create_user_location_query(user_loc)

    async def get_country_from_ip(self, ip: str) -> str:
        country = "UNKNOWN"
        try:
            with geoip2.database.Reader(
                "./modules/static/maxmind/GeoLite2-Country.mmdb"
            ) as reader:
                response = reader.country(ip)
                country = response.country.name
                return country
        except Exception as e:
            self.logger.error(e)
            return country
