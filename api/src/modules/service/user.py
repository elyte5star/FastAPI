from modules.repository.request_models.user import (
    CreateUserRequest,
    GetUserRequest,
    GetUsersRequest,
    OtpRequest,
    GetOtpResponse,
    NewOtpRequest,
)
from modules.repository.response_models.user import (
    CreateUserResponse,
    GetUserResponse,
    UserDetails,
    GetUsersResponse,
)
from modules.repository.schema.users import (
    User,
    Otp,
    PasswordResetToken,
    UserLocation,
    NewLocationToken,
)
import bcrypt
import geoip2.database

# from modules.repository.queries.user import UserQueries
from fastapi_events.dispatcher import dispatch
from modules.utils.misc import get_indent, time_delta, time_now_utc
from modules.service.email import EmailHandler
from starlette.staticfiles import StaticFiles

TOKEN_INVALID = "invalidToken"
TOKEN_EXPIRED = "expired"
TOKEN_VALID = "valid"
USER_ENABLED = "enabled"


class UserHandler(EmailHandler):
    async def _create_user(self, req: CreateUserRequest) -> CreateUserResponse:
        user_exist = await self.check_if_user_exist(
            req.email, req.username, req.telephone
        )
        if user_exist is None:
            new_user_password = req.password.get_secret_value()
            hashed_password = self.hash_password(new_user_password)
            new_user = User(
                id=self.get_new_id(req.email),
                email=req.email,
                username=req.username,
                password=hashed_password,
                telephone=req.telephone,
                discount=0.0,
                created_by=req.username,
                failed_attempts=0,
            )
            result = await self.create_user_query(new_user)
            if result is not None:
                req.result.data = result
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

    async def _get_users(self, req: GetUsersRequest) -> GetUsersResponse:
        # include RBAC
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

    async def _delete_user(self, user: User) -> None:
        otp: Otp = await self.get_otp_by_user_query(user)
        if otp is not None:
            await self.delete_otp_by_id_query(otp.id)
        password_rest_token: PasswordResetToken = (
            self.find_passw_reset_token_by_user_query(user)
        )
        if password_rest_token is not None:
            await self.delete_passw_reset_token_by_id_query(password_rest_token.id)
        await self.delete_user_query(user.id)

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

    def is_geo_ip_enabled(self) -> bool:
        return self.cf.is_geo_ip_enabled

    async def is_new_login_location(
        self, username: str, ip: str
    ) -> NewLocationToken | None:
        if not self.is_geo_ip_enabled():
            return None
        try:
            country, city = await self.get_location_from_ip(ip)
            self.cf.logger.info(country + "====****")
            user: User = await self.get_otp_by_user_query(username)
            user_loc: UserLocation = await self.find_user_location_by_country_and_user(
                country, user
            )
            if user_loc is None or not user_loc.enabled:
                return self.create_new_location_token(user, country)
        except Exception as e:
            self.cf.logger.error(e)
            return None

    async def is_valid_login_location(self, username: str, ip: str):
        pass

    async def create_new_location_token(
        self, user: User, country: str
    ) -> NewLocationToken | None:
        user_loc: UserLocation = UserLocation(
            id=get_indent(), country=country, owner=user
        )
        user_loc = await self.create_user_location_query(user_loc)
        new_loc_token: NewLocationToken = NewLocationToken(
            id=get_indent(), token=get_indent(), location=user_loc
        )
        new_loc_token = await self.create_new_location_token_query(new_loc_token)
        return new_loc_token

    async def add_user_location(self, user: User, ip: str):
        pass

    async def get_location_from_ip(self, ip: str) -> tuple[str, str]:
        async with geoip2.database.Reader(
            StaticFiles(directory="./modules/static/maxmind/GeoLite2-City.mmdb")
        ) as reader:
            response = reader.city(ip)
            return (response.country.name, response.city.name)
