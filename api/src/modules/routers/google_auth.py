from fastapi import APIRouter, Depends, Request, Response
from modules.service.google import GoogleHandler
from modules.repository.response_models.auth import TokenResponse, BaseResponse
from modules.repository.request_models.auth import GoogleLoginRequest


class GoogleAuthRouter(GoogleHandler):

    def __init__(self, config):
        super().__init__(config)
        self.router: APIRouter = APIRouter(
            prefix="/google",
            tags=["GOOGLE"],
        )

        self.router.add_api_route(
            path="/login/{token}",
            endpoint=self.login,
            response_model=TokenResponse,
            methods=["GET"],
            description="Verify google token",
        )

    async def login(
        self,
        token: str,
        response: Response,
    ) -> BaseResponse:
        return await self.authenticate_google_user(
            GoogleLoginRequest(token=token), response
        )
