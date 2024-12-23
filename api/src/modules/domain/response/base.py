from pydantic import BaseModel, ConfigDict
import time
from modules.utils.misc import get_indent


class BaseParams(BaseModel):
    model_config: ConfigDict = ConfigDict(
        from_attributes=True, validate_assignment=True, use_enum_values=True
    )
    req_id: str = ""
    start_time: float = 0.0
    stop_time: float = 0.0
    process_time: str = ""
    success: bool = False
    message: str = ""


class BaseReq(BaseParams):

    def model_post_init(self, ctx):
        self.req_id = get_indent()
        self.start_time = time.perf_counter()

    def req_success(self, message=""):
        self.success = True
        if message:
            self.message = message
        self.req_process_time()
        return self

    def req_failure(self, message=""):
        self.success = False
        if message:
            self.message = message
        self.req_process_time()
        return self

    def req_process_time(self):
        self.stop_time = time.perf_counter()
        self.process_time = str((self.start_time - self.stop_time))
