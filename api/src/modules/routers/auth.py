from fastapi import APIRouter, Request, Response, Security, Depends
from fastapi.security import OAuth2PasswordRequestForm
from modules.repository.response_models.auth import TokenResponse, BaseResponse
from modules.service.mfa_auth import MFAHandler
from modules.repository.request_models.auth import (
    LoginRequest,
    RefreshTokenRequest,
    EnableLocationRequest,
    MFALoginRequest,
)
from modules.security.dependency import security
from modules.security.current_user import JWTPrincipal
from typing import Annotated
from pydantic import SecretStr

from modules.security.ext_auth import OAuth2CodeBearer


security = OAuth2CodeBearer()


class AuthRouter(MFAHandler):

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
        self.router.add_api_route(
            path="/msal/login",
            endpoint=self.get_token,
            response_model=TokenResponse,
            methods=["GET"],
            description="Verify msal access token",
        )
        self.router.add_api_route(
            path="/google/login",
            endpoint=self.get_token,
            response_model=TokenResponse,
            methods=["GET"],
            description="Verify google access token",
        )

    async def get_token(
        self,
        token: Annotated[
            str,
            Security(
                security,
                scopes=["user_impersonation"],
            ),
        ],
        response: Response,
    ) -> BaseResponse:
        return await self.authenticate_msoft_user(
            MFALoginRequest(access_token=token), response
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
        current_user: Annotated[JWTPrincipal, Depends(security)],
    ) -> BaseResponse:
        return await self._refresh_access_token(
            RefreshTokenRequest(credentials=current_user),
        )

    async def enable_new_location(self, token: str) -> BaseResponse:
        return await self._enable_new_loc(EnableLocationRequest(token=token))
