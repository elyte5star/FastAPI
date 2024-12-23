from pydantic import BaseModel, ConfigDict
from datetime import datetime
from modules.utils.misc import get_indent, time_then, time_now_utc


class BaseParams(BaseModel):
    model_config: ConfigDict = ConfigDict(
        from_attributes=True, validate_assignment=True, use_enum_values=True
    )
    req_id: str = ""
    start_time: datetime = time_then()
    stop_time: datetime = time_then()
    process_time: float = 0.0
    success: bool = False
    message: str = ""


class BaseReq(BaseParams):

    def model_post_init(self, ctx):
        self.req_id = get_indent()
        self.start_time = time_now_utc()

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
        self.stop_time = time_now_utc()
        self.process_time = float((self.start_time - self.stop_time).total_seconds())
