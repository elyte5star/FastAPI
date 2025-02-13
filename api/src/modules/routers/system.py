from modules.security.dependency import RoleChecker, JWTPrincipal, security
from fastapi import APIRouter, Depends
from modules.repository.request_models.base import (
    GetInfoResponse,
    GetSystemInfoRequest,
)
from typing import Annotated
from modules.service.system import SystemHandler


class SystemInfoRouter(SystemHandler):
    def __init__(self, config):
        super().__init__(config)
        self.router: APIRouter = APIRouter(
            prefix="/system",
            tags=["System"],
            dependencies=[Depends(RoleChecker(["ADMIN"]))],
        )
        self.router.add_api_route(
            path="/info",
            endpoint=self.get_system_info,
            response_model=GetInfoResponse,
            methods=["GET"],
        )

    async def get_system_info(
        self,
        current_user: Annotated[JWTPrincipal, Depends(security)],
    ) -> GetInfoResponse:
        return await self._get_sys_info(
            GetSystemInfoRequest(
                credentials=current_user,
            )
        )
