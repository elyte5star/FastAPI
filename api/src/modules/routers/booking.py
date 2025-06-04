from modules.service.booking import BookingHandler
from fastapi import APIRouter, Depends, status
from typing import Annotated
from modules.repository.request_models.booking import (
    CreateBooking,
    CreateBookingRequest,
)
from modules.repository.response_models.booking import CreateBookingResponse
from modules.security.dependency import security, JWTPrincipal
from modules.repository.response_models.job import JobResponse


class BookingRouter(BookingHandler):
    def __init__(self, config):
        super().__init__(config)
        self.router: APIRouter = APIRouter(
            prefix="/booking",
            tags=["Bookings"],
        )
        self.router.add_api_route(
            path="/create",
            status_code=status.HTTP_201_CREATED,
            endpoint=self.create_booking,
            response_model=JobResponse,
            methods=["POST"],
            description="Register a booking",
        )

    async def create_booking(
        self,
        data: CreateBooking,
        current_user: Annotated[JWTPrincipal, Depends(security)],
    ) -> JobResponse:
        return await self.__create_booking(
            CreateBookingRequest(new_order=data, credentials=current_user)
        )
