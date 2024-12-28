from fastapi import APIRouter, Depends
from fastapi.security import OAuth2PasswordRequestForm
from typing import Annotated
from modules.repository.response_models.auth import TokenResponse
from modules.service.auth import AuthenticationHandler
from modules.repository.request_models.auth import LoginRequest


class AuthRouter(AuthenticationHandler):
    def __init__(self, config):
        super().__init__(config)
        self.router: APIRouter = APIRouter(prefix="/auth", tags=["Authentication"])
        self.router.add_api_route(
            path="/token",
            endpoint=self.form_login,
            response_model=TokenResponse,
            methods=["POST"],
        )

    async def form_login(
        self, form_data: Annotated[OAuth2PasswordRequestForm, Depends()]
    ) -> TokenResponse:
        return await self.authenticate_user(
            LoginRequest(username=form_data.username, password=form_data.password)
        )
