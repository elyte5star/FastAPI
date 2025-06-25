from modules.repository.queries.common import CommonQueries
from modules.repository.request_models.base import BaseResponse, GetSystemInfoRequest


class SystemHandler(CommonQueries):
    async def _get_sys_info(
        self,
        req: GetSystemInfoRequest,
    ) -> BaseResponse:
        if req.credentials is not None:
            info = await self.system_info()
            info["currentUser"] = dict(req.credentials)
            req.result.info = info
            self.logger.info(f"{req.credentials.username} checked the system")
            return req.req_success("System information")
        return req.req_failure("No valid user session")
