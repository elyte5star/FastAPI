from fastapi import APIRouter, Depends
from fastapi.security import OAuth2PasswordRequestForm
from modules.repository.response_models.auth import TokenResponse
from modules.service.auth import AuthenticationHandler
from modules.repository.request_models.auth import (
    LoginRequest,
    RefreshTokenRequest,
    Grant,
)
from modules.security.base import JWTBearer
from typing import Annotated


class AuthRouter(AuthenticationHandler):

    def __init__(self, config):
        super().__init__(config)
        self.security: JWTBearer = JWTBearer(config, config.roles)
        self.router: APIRouter = APIRouter(prefix="/auth", tags=["Authentication"])
        self.router.add_api_route(
            path="/form-login",
            endpoint=self.login,
            response_model=TokenResponse,
            methods=["POST"],
        )
        self.router.add_api_route(
            path="/refresh",
            endpoint=self.refresh_access_token,
            response_model=TokenResponse,
            methods=["POST"],
            dependencies=[Depends(self.security)],
        )

    async def login(
        self, form_data: Annotated[OAuth2PasswordRequestForm, Depends()]
    ) -> TokenResponse:
        return await self.authenticate_user(
            LoginRequest(username=form_data.username, password=form_data.password)
        )

    async def refresh_access_token(self, data: Grant) -> TokenResponse:
        return await self.validate_create_token(
            RefreshTokenRequest(credentials=self.security.cred, data=data)
        )
