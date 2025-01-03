from modules.service.users import UserHandler
from fastapi import APIRouter, Depends
from typing import Annotated
from modules.repository.response_models.user import (
    GetUserResponse,
    CreateUserResponse,
    GetUsersResponse,
)
from modules.repository.request_models.user import (
    CreateUserRequest,
    GetUserRequest,
    GetUsersRequest,
)
from modules.security.base import JWTBearer, JwtPrincipal


class UserRouter(UserHandler):
    def __init__(self, config):
        super().__init__(config)
        self.security: JwtPrincipal = JWTBearer(config)
        self.router: APIRouter = APIRouter(prefix="/users", tags=["Users"])
        self.router.add_api_route(
            path="/signup",
            endpoint=self.create_user,
            response_model=CreateUserResponse,
            methods=["POST"],
        )
        self.router.add_api_route(
            path="/{userid}",
            endpoint=self.get_user,
            response_model=GetUserResponse,
            methods=["GET"],
            dependencies=[Depends(self.security)],
        )

        self.router.add_api_route(
            path="",
            endpoint=self.get_users,
            response_model=GetUserResponse,
            methods=["GET"],
            dependencies=[Depends(self.security)],
        )

    async def create_user(
        self, req: Annotated[CreateUserRequest, Depends()]
    ) -> CreateUserResponse:
        return await self._create_user(req)

    async def get_users(self):
        return ""

    async def get_user(self, userid: str) -> GetUserResponse:
        return await self._get_user(
            GetUserRequest(active_user=self.security, userid=userid)
        )
