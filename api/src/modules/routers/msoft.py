from fastapi import APIRouter, Response, Depends
from modules.service.msoft import MSOFTHandler
from modules.repository.response_models.auth import TokenResponse, BaseResponse
from modules.repository.request_models.auth import MSOFTMFALoginRequest
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from typing import Annotated


security = HTTPBearer()


class MSOFTAuthRouter(MSOFTHandler):

    def __init__(self, config):
        super().__init__(config)
        self.router: APIRouter = APIRouter(
            prefix="/msal",
            tags=["MSOFT"],
        )

        self.router.add_api_route(
            path="/login",
            endpoint=self.login,
            response_model=TokenResponse,
            methods=["GET"],
            description="Verify MSOFT token",
        )

    async def login(
        self,
        credentials: Annotated[HTTPAuthorizationCredentials, Depends(security)],
        response: Response,
    ) -> BaseResponse:
        return await self.authenticate_msoft_user(
            MSOFTMFALoginRequest(access_token=credentials.credentials), response
        )
