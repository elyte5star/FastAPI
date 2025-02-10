from modules.service.user import UserHandler
from fastapi import APIRouter, Depends, status, Request
from typing import Annotated
from modules.repository.response_models.user import (
    GetUserResponse,
    CreateUserResponse,
    GetUsersResponse,
    BaseResponse,
    ClientEnquiryResponse,
)
from modules.repository.request_models.user import (
    CreateUserRequest,
    GetUserRequest,
    GetUsersRequest,
    DeleteUserRequest,
    OtpRequest,
    NewOtpRequest,
    EnableLocationRequest,
    VerifyRegistrationOtpRequest,
    CreateUser,
    UserEnquiryRequest,
    UserEnquiry,
    ResetUserRequest,
    UpdateUserPassword,
    UpdateUserPasswordRequest,
    SaveUserPassswordRequest
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
            path="/create-registration-otp/{email}",
            status_code=status.HTTP_202_ACCEPTED,
            endpoint=self.create_verification_otp,
            response_model=BaseResponse,
            dependencies=[Depends(RoleChecker(["ADMIN"]))],
            methods=["GET"],
            description="Admin send user verification code",
        )

        self.router.add_api_route(
            path="/signup/resend-registration-otp/{token}",
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
            path="/enable-new-location/{token}",
            endpoint=self.enable_new_location,
            response_model=BaseResponse,
            methods=["GET"],
            description="Verify new location Login",
        )
        self.router.add_api_route(
            path="/signup/verify-otp/{token}",
            endpoint=self.verify_registration_otp,
            response_model=BaseResponse,
            methods=["GET"],
            description="Confirm user registration",
        )
        self.router.add_api_route(
            path="/customer/service",
            endpoint=self.create_enquiry,
            response_model=ClientEnquiryResponse,
            summary="Customer Service",
            methods=["POST"],
        )

        self.router.add_api_route(
            path="/reset-password",
            endpoint=self.reset_user_password,
            response_model=BaseResponse,
            summary="Reset user password",
            methods=["POST"],
        )

        self.router.add_api_route(
            path="/update-password",
            endpoint=self.update_user_password,
            response_model=BaseResponse,
            summary="Update user password",
            methods=["POST"],
        )
        
        self.router.add_api_route(
            path="/save-password",
            endpoint=self.save_user_password,
            response_model=BaseResponse,
            summary="Save user password",
            methods=["POST"],
        )

    async def create_user(
        self, new_user: Annotated[CreateUser, Depends()], request: Request
    ) -> CreateUserResponse:
        return await self._create_user(
            CreateUserRequest(new_user=new_user),
            request,
        )

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
    ) -> BaseResponse:
        return await self._generate_new_otp(
            NewOtpRequest(token=token),
            request,
        )

    async def enable_new_location(self, token: str) -> BaseResponse:
        return await self._enable_new_loc(EnableLocationRequest(token=token))

    async def verify_registration_otp(self, token: str) -> BaseResponse:
        return await self.confirm_user_registration(
            VerifyRegistrationOtpRequest(token=token)
        )

    async def create_enquiry(
        self,
        enquiry: Annotated[UserEnquiry, Depends()],
        request: Request,
    ) -> ClientEnquiryResponse:
        return await self._create_enquiry(
            UserEnquiryRequest(enquiry=enquiry),
            request,
        )

    async def reset_user_password(
        self, email: EmailStr, request: Request
    ) -> BaseResponse:
        return await self._reset_user_password(
            ResetUserRequest(email=email),
            request,
        )

    async def update_user_password(self, update: UpdateUserPassword) -> BaseResponse:
        return await self._update_user_password(
            UpdateUserPasswordRequest(update_password=update)
        )

    async def save_user_password(self, update: UpdateUserPassword) -> BaseResponse:
        return await self._save_user_password(
            SaveUserPassswordRequest(update_password=update)
        )
