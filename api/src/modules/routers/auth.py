from fastapi import APIRouter, Depends, Request, Response
from fastapi.security import OAuth2PasswordRequestForm
from modules.repository.response_models.auth import TokenResponse, BaseResponse
from modules.service.auth import AuthenticationHandler,get_indent
from modules.repository.request_models.auth import (
    LoginRequest,
    RefreshTokenRequest,
    EnableLocationRequest,
)
from modules.security.dependency import RefreshTokenChecker, JWTPrincipal
from typing import Annotated
from pydantic import SecretStr


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
            description="JWTBearerGrant",
        )
        self.router.add_api_route(
            path="/refresh",
            endpoint=self.refresh_access_token,
            response_model=TokenResponse,
            methods=["POST"],
            description="RefreshTokenGrant",
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
    ) -> BaseResponse:
        return await self.authenticate_user(
            LoginRequest(
                username=form_data.username,
                password=SecretStr(form_data.password),
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
    ) -> BaseResponse:
        return await self._refresh_access_token(
            RefreshTokenRequest(credentials=current_user),
        )

    async def enable_new_location(self, token: str) -> BaseResponse:
        return await self._enable_new_loc(EnableLocationRequest(token=token))
