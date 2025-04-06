from modules.repository.request_models.base import (
    GetSystemInfoRequest,
    GetInfoResponse,
)
from modules.database.base import AsyncDatabaseSession


class SystemHandler(AsyncDatabaseSession):
    async def _get_sys_info(
        self,
        req: GetSystemInfoRequest,
    ) -> GetInfoResponse:
        result = await self.system_info()
        req.result.info = result
        self.logger.info(f"{req.credentials.username} checked the system")
        return req.req_success("System information")
