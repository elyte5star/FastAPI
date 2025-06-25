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
        info = await self.system_info()
        info["currentUser"] = dict(req.credentials)
        req.result.info = info
        self.logger.info(f"{req.credentials.username} checked the system")
        return req.req_success("System information")
