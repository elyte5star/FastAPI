import time
from modules.utils.misc import get_indent
from typing import Self
from modules.repository.response_models.base import BaseResponse


class BaseReq(BaseResponse):

    def model_post_init(self, ctx):
        self.req_id = get_indent()
        self.start_time = time.perf_counter()

    def success(self, message="") -> Self:
        self.req_success = True
        if message:
            self.message = message
        self.req_process_time()
        return self

    def failure(self, message="") -> Self:
        self.req_success = False
        if message:
            self.message = message
        self.req_process_time()
        return self

    def req_process_time(self):
        self.stop_time = time.perf_counter()
        self.process_time = str((self.stop_time - self.start_time))
