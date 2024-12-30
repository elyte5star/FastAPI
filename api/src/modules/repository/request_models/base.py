import time
from modules.utils.misc import get_indent
from modules.repository.response_models.base import BaseResponse


class BaseReq(BaseResponse):

    def model_post_init(self, ctx):
        self.req_id = get_indent()
        self.start_time = time.perf_counter()

    def req_success(self, message=""):
        self.success = True
        if message:
            self.message = message
        self.req_process_time()
        return self.result

    def req_failure(self, message=""):
        self.req_success = False
        if message:
            self.message = message
        self.req_process_time()
        return self.result

    def req_process_time(self):
        self.stop_time = time.perf_counter()
        self.process_time = str((self.stop_time - self.start_time))
