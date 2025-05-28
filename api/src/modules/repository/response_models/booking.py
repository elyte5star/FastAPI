from modules.repository.request_models.base import BaseResponse
from typing import Any
from pydantic import ConfigDict


class CreateBookingResponse(BaseResponse):
    items: list = []
    oId: str = ""


class GetBookingsResponse(BaseResponse):
    model_config = ConfigDict(from_attributes=True)
    bookings: list = list()


class GetBookingResponse(BaseResponse):
    model_config = ConfigDict(from_attributes=True)
    booking: Any = {}
