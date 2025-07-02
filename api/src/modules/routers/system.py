from modules.security.dependency import JWTBearer, JWTPrincipal, security
from fastapi import APIRouter, Depends
from modules.repository.request_models.base import (
    GetInfoResponse,
    GetSystemInfoRequest,
    BaseResponse,
)
from typing import Annotated
from modules.service.system import SystemHandler


class SystemInfoRouter(SystemHandler):
    def __init__(self, config):
        super().__init__(config)
        self.router: APIRouter = APIRouter(
            prefix="/system",
            tags=["System"],
        )
        self.router.add_api_route(
            path="/info",
            endpoint=self.get_system_info,
            response_model=GetInfoResponse,
            methods=["GET"],
        )

    async def get_system_info(
        self,
        current_user: Annotated[
            JWTPrincipal, Depends(JWTBearer(allowed_roles=["ADMIN"]))
        ],
    ) -> BaseResponse:
        return await self._get_sys_info(
            GetSystemInfoRequest(
                credentials=current_user,
            ),
        )
