from modules.repository.request_models.user import (
    CreateUserRequest,
    GetUserRequest,
)
from modules.repository.response_models.user import (
    CreateUserResponse,
    GetUserResponse,
    UserDetails,
)
from modules.repository.queries.user import UserQueries, User
import bcrypt


class UserHandler(UserQueries):
    async def _create_user(self, req: CreateUserRequest) -> CreateUserResponse:
        user_exist = await self.check_if_user_exist(req.email, req.username)
        if user_exist is None:
            new_user = User(
                id=self.get_new_id(),
                email=req.email,
                username=req.username,
                password=self.hash_password(req.password.get_secret_value()),
                telephone=req.telephone,
                discount=0.0,
                created_by=req.username,
                failed_attempts=0,
            )
            result = await self.create_user_query(new_user)
            req.result.userid = result
            return req.success("New user created!")
        return req.failure("User exist")

    def hash_password(self, plain_password: str) -> bytes:
        hashed_password = bcrypt.hashpw(
            plain_password.encode(self.cf.coding), bcrypt.gensalt(rounds=self.cf.rounds)
        ).decode(self.cf.coding)
        return hashed_password

    async def _get_user(self, req: GetUserRequest) -> GetUserResponse:
        user = await self.get_user_by_id(req.userid)
        if user is not None:
            user_info = UserDetails(
                userid=user.id,
                createdAt=user.created_at,
                lastModifiedAt=user.modified_at,
                lastModifiedBy=user.modified_by,
                createdBy=user.created_by,
                email=user.email,
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
