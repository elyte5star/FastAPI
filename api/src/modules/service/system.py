from modules.repository.request_models.base import (
    GetSystemInfoRequest,
    GetInfoResponse,
)
from modules.repository.queries.common import CommonQueries


class SystemHandler(CommonQueries):
    async def _get_sys_info(
        self,
        req: GetSystemInfoRequest,
    ) -> GetInfoResponse:
        result = await self.system_info()
        req.result.info = result
        self.logger.info(f"{req.credentials.username} checked the system")
        return req.req_success("System information")
