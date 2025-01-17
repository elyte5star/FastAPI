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
)
from modules.security.dependency import security, JWTPrincipal, RoleChecker


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
        self, userid: str, current_user: Annotated[JWTPrincipal, Depends(security)]
    ) -> BaseResponse:
        return await self._delete_user(
            DeleteUserRequest(credentials=current_user, userid=userid)
        )
