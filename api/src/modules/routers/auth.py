from fastapi import APIRouter, Depends, Request, Response
from fastapi.security import OAuth2PasswordRequestForm
from modules.repository.response_models.auth import TokenResponse, BaseResponse
from modules.service.auth import AuthenticationHandler
from modules.repository.request_models.auth import (
    LoginRequest,
    RefreshTokenRequest,
    EnableLocationRequest,
)
from modules.security.dependency import RefreshTokenChecker, JWTPrincipal
from typing import Annotated


class AuthRouter(AuthenticationHandler):

    def __init__(self, config):
        super().__init__(config)
        self.router: APIRouter = APIRouter(
            prefix="/auth",
            tags=["Authentication"],
        )
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
        )
        self.router.add_api_route(
            path="/enable-new-location/{token}",
            endpoint=self.enable_new_location,
            response_model=BaseResponse,
            methods=["GET"],
            description="Verify new location Login",
        )

    async def login(
        self,
        form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
        request: Request,
        response: Response,
    ) -> TokenResponse:
        return await self.authenticate_user(
            LoginRequest(
                username=form_data.username,
                password=form_data.password,
            ),
            request,
            response,
        )

    async def refresh_access_token(
        self,
        current_user: Annotated[
            JWTPrincipal,
            Depends(RefreshTokenChecker()),
        ],
    ) -> TokenResponse:
        return await self._refresh_access_token(
            RefreshTokenRequest(credentials=current_user),
        )

    async def enable_new_location(self, token: str) -> BaseResponse:
        return await self._enable_new_loc(EnableLocationRequest(token=token))
