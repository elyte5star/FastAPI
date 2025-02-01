from modules.service.user import UserHandler
from fastapi import APIRouter, Depends, status, Request
from typing import Annotated
from modules.repository.response_models.user import (
    GetUserResponse,
    CreateUserResponse,
    GetUsersResponse,
    BaseResponse,
)
from modules.repository.request_models.user import (
    CreateUserRequest,
    GetUserRequest,
    GetUsersRequest,
    DeleteUserRequest,
    OtpRequest,
    NewOtpRequest,
    EnableLocationRequest,
)
from modules.security.dependency import security, JWTPrincipal, RoleChecker
from pydantic import EmailStr


class UserRouter(UserHandler):
    def __init__(self, config):
        super().__init__(config)
        self.router: APIRouter = APIRouter(prefix="/users", tags=["Users"])
        self.router.add_api_route(
            path="/signup",
            status_code=status.HTTP_201_CREATED,
            endpoint=self.create_user,
            response_model=CreateUserResponse,
            methods=["POST"],
            description="Create user account",
        )
        self.router.add_api_route(
            path="/create-confirmation-token/{email}",
            status_code=status.HTTP_202_ACCEPTED,
            endpoint=self.create_verification_otp,
            response_model=BaseResponse,
            dependencies=[Depends(RoleChecker(["ADMIN"]))],
            methods=["GET"],
            description="Send user verification code",
        )

        self.router.add_api_route(
            path="/resend-registration-token/{token}",
            status_code=status.HTTP_202_ACCEPTED,
            endpoint=self.resend_verification_otp,
            response_model=BaseResponse,
            dependencies=[Depends(RoleChecker(config.roles))],
            methods=["GET"],
            description="Send a new user verification code",
        )
        self.router.add_api_route(
            path="/{userid}",
            endpoint=self.get_user,
            response_model=GetUserResponse,
            methods=["GET"],
            dependencies=[Depends(RoleChecker(config.roles))],
            description="Get User",
        )

        self.router.add_api_route(
            path="/{userid}",
            endpoint=self.delete_user,
            response_model=BaseResponse,
            methods=["DELETE"],
            dependencies=[Depends(RoleChecker(config.roles))],
            description="Delete User",
        )
        self.router.add_api_route(
            path="",
            endpoint=self.get_users,
            response_model=GetUsersResponse,
            methods=["GET"],
            dependencies=[Depends(RoleChecker(["ADMIN"]))],
            description="Get Users, Admin right required",
        )
        self.router.add_api_route(
            path="/enableNewLoc/{token}",
            endpoint=self.enable_new_loc,
            response_model=BaseResponse,
            methods=["GET"],
            dependencies=[Depends(RoleChecker(config.roles))],
            description="Enable New Location Login",
        )

    async def create_user(
        self, req: Annotated[CreateUserRequest, Depends()], request: Request
    ) -> CreateUserResponse:
        return await self._create_user(req, request)

    async def get_users(
        self, current_user: Annotated[JWTPrincipal, Depends(security)]
    ) -> GetUsersResponse:
        return await self._get_users(GetUsersRequest(credentials=current_user))

    async def get_user(
        self, userid: str, current_user: Annotated[JWTPrincipal, Depends(security)]
    ) -> GetUserResponse:
        return await self._get_user(
            GetUserRequest(credentials=current_user, userid=userid)
        )

    async def delete_user(
        self,
        userid: str,
        current_user: Annotated[
            JWTPrincipal,
            Depends(security),
        ],
    ) -> BaseResponse:
        return await self._delete_user(
            DeleteUserRequest(credentials=current_user, userid=userid)
        )

    async def create_verification_otp(
        self,
        email: EmailStr,
        request: Request,
        current_user: Annotated[JWTPrincipal, Depends(security)],
    ) -> BaseResponse:
        return await self._create_verification_otp(
            OtpRequest(credentials=current_user, email=email), request
        )

    async def resend_verification_otp(
        self,
        token: str,
        request: Request,
        current_user: Annotated[JWTPrincipal, Depends(security)],
    ) -> BaseResponse:
        return await self._generate_new_otp(
            NewOtpRequest(credentials=current_user, token=token), request
        )

    async def enable_new_loc(self, token: str) -> BaseResponse:
        return await self._enable_new_loc(EnableLocationRequest(token=token))
