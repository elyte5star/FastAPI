from modules.service.users import UserHandler
from fastapi import APIRouter, Depends
from typing import Annotated
from modules.repository.response_models.user import GetUserResponse, CreateUserResponse
from modules.repository.request_models.user import CreateUserRequest, GetUserRequest


class UserRouter(UserHandler):
    def __init__(self, config):
        super().__init__(config)
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
        )

    async def create_user(
        self, req: Annotated[CreateUserRequest, Depends()]
    ) -> CreateUserResponse:
        req.result = CreateUserResponse()
        return await self._create_user(req)

    async def get_user(self, userid: str) -> GetUserResponse:
        return await self._get_user(GetUserRequest(userid=userid))
