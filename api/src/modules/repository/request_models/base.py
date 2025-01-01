import time
from modules.utils.misc import get_indent

from modules.repository.response_models.base import BaseResponse
from pydantic import BaseModel, ConfigDict


class BaseReq(BaseModel):
    model_config = ConfigDict(validate_assignment=True, str_strip_whitespace=True)

    def model_post_init(self, ctx):
        self.result: BaseResponse = BaseResponse()
        self.result.req_id = get_indent()
        self.result.start_time = time.perf_counter()

    def req_success(self, message="") -> BaseResponse:
        self.result.success = True
        if message:
            self.result.message = message
        self.req_process_time()
        return self.result

    def req_failure(self, message="") -> BaseResponse:
        self.result.success = False
        if message:
            self.result.message = message
        self.req_process_time()
        return self.result

    def req_process_time(self):
        self.result.stop_time = time.perf_counter()
        self.result.process_time = str((self.result.stop_time - self.result.start_time))
