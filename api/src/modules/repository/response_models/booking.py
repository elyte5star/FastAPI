
from modules.repository.request_models.base import BaseResponse


class CreateBookingResponse(BaseResponse):
    oid: str = ""
    