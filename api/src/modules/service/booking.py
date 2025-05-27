from modules.repository.queries.product import ProductQueries
from modules.repository.request_models.booking import (
    CreateBookingRequest,
    PaymentDetails,
    GetBookingRequest,
)
from modules.repository.response_models.booking import (
    CreateBookingResponse,
    GetBookingsResponse,
    GetBookingResponse,
)
from decimal import Decimal


class BookingHandler(ProductQueries):

    async def _create_booking(self, req: CreateBookingRequest) -> CreateBookingResponse:
        print(req)
        pass

    async def _get_bookings(self, req: CreateBookingRequest) -> GetBookingsResponse:
        pass

    async def _get_booking(self, req: GetBookingRequest) -> GetBookingResponse:
        pass

    async def make_payment(self, data: PaymentDetails, amount_to_pay: Decimal) -> bool:
        # TODO implement card payment
        return True
