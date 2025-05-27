from modules.service.queue import QueueHandler
from modules.repository.request_models.booking import (
    CreateBookingRequest,
    PaymentDetails,
    GetBookingRequest,
    CartItem,
)
from modules.repository.response_models.booking import (
    CreateBookingResponse,
    GetBookingsResponse,
    GetBookingResponse,
)
from decimal import Decimal
from modules.utils.misc import get_indent, obj_as_json


class BookingHandler(QueueHandler):

    async def _create_booking(self, req: CreateBookingRequest) -> CreateBookingResponse:

        pass

    async def _get_bookings(self, req: CreateBookingRequest) -> GetBookingsResponse:
        pass

    async def _get_booking(self, req: GetBookingRequest) -> GetBookingResponse:
        pass

    async def make_payment(self, data: PaymentDetails, amount_to_pay: Decimal) -> bool:
        # TODO implement card payment
        return True

    async def check_products(self, items: list[CartItem]) -> tuple | None:
        avaliable_prods, unavaliable_prods = [], []
        for item in items:
            product_id = item.pid
            product = await self.find_product_by_id(product_id)
            if product is None:
                return None
            product_dict = obj_as_json(product)
            if product_dict["stock_quantity"] >= item.quantity:
                avaliable_prods.append(product_dict)
            else:
                unavaliable_prods.append(product_dict)
        return (avaliable_prods, unavaliable_prods)
