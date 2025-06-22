from modules.repository.request_models.base import BaseResponse
from pydantic import ConfigDict
from modules.repository.response_models.job import JobResponse


class CreateBookingResponse(BaseResponse):
    items: list = []
    oId: str = ""


class GetBookingsResponse(BaseResponse):
    model_config = ConfigDict(from_attributes=True)
    bookings: list = list()


class GetBookingResponse(BaseResponse):
    job: JobResponse = JobResponse()
    data: dict = {}
