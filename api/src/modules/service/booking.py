from modules.repository.request_models.booking import (
    CreateBookingRequest,
    PaymentDetails,
    GetBookingRequest,
    CartItem,
    BookingModel,
)
from modules.repository.response_models.booking import (
    GetBookingsResponse,
    GetBookingResponse,
)
from modules.repository.response_models.job import JobResponse
from decimal import Decimal
from modules.utils.misc import obj_as_json
from modules.queue.base import RQHandler, JobType, ResultType
from modules.repository.response_models.product import Product


class BookingHandler(RQHandler):

    async def _create_booking(self, req: CreateBookingRequest) -> JobResponse:
        if req.credentials.userid != req.new_order.userid:
            self.logger.warning(
                f"illegal operation by {req.credentials.userid}",
            )
            return req.req_failure("Forbidden: Access is denied")
        cart = req.new_order.cart
        check_cart = await self.check_products(cart)
        if check_cart is None:
            return req.req_failure("Product in cart does not exist")
        _, unavaliable_prods = check_cart
        if unavaliable_prods:
            req.result = unavaliable_prods
            return req.req_failure("Products out of stock")
        amount_to_pay = sum(item.calculated_price for item in cart)
        check_payment = self.make_payment(req.new_order.payment_details, amount_to_pay)
        if not check_payment:
            return req.req_failure("Problem with payment")

        job = await self._create_job(JobType.CreateBooking, req.credentials.userid)
        booking_model = BookingModel(
            cart=cart,
            total_price=amount_to_pay,
            shipping_details=req.new_order.shipping_details,
            userid=req.credentials.userid,
        )
        job.create_booking = booking_model
        success, message = await self._add_job_with_one_task(
            job, self.cf.queue_name[1], ResultType.Database
        )
        if success:
            req.result = job.job_id
            return req.req_success(message)
        return req.req_failure(message)

    async def _get_bookings(self, req: CreateBookingRequest) -> GetBookingsResponse:
        pass

    async def _get_booking(self, req: GetBookingRequest) -> GetBookingResponse:
        pass

    async def make_payment(self, data: PaymentDetails, amount_to_pay: Decimal) -> bool:
        # TODO implement card payment
        return True

    async def check_products(self, cart: list[CartItem]) -> tuple | None:
        avaliable_prods, unavaliable_prods = [], []
        for item in cart:
            product_in_db = await self.find_product_by_id(item.pid)
            if product_in_db is None:
                return None
            pydantic_model = Product.model_validate(product_in_db)
            if pydantic_model.stock_quantity >= item.quantity:
                avaliable_prods.append(pydantic_model)
            else:
                unavaliable_prods.append(pydantic_model)
        return (avaliable_prods, unavaliable_prods)
