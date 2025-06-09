from modules.repository.request_models.booking import (
    CreateBookingRequest,
    PaymentDetails,
    GetBookingRequest,
)
from modules.repository.response_models.booking import (
    GetBookingsResponse,
    GetBookingResponse,
)
from modules.repository.response_models.job import JobResponse, BaseResponse
from decimal import Decimal
from modules.queue.base import RQHandler, JobType, ResultType
from modules.repository.response_models.product import Product
from modules.queue.models import BookingModel, CartItem


class BookingHandler(RQHandler):

    async def _create_booking(
        self,
        req: CreateBookingRequest,
    ) -> BaseResponse:
        if req.credentials is not None and req.new_order is not None:
            current_user = req.credentials
            new_order = req.new_order
            if current_user.user_id != new_order.user_id:
                self.logger.warning(
                    f"illegal operation by {current_user.user_id}",
                )
                return req.req_failure("Forbidden: Access is denied")
            cart = new_order.cart
            check_cart = await self.check_products(cart)
            if check_cart is None:
                return req.req_failure("Product in cart does not exist")
            _, unavaliable_prods = check_cart
            if unavaliable_prods:
                req.result = unavaliable_prods
                return req.req_failure("Products out of stock")
            sum_of_items = sum(Decimal(item.calculated_price) for item in cart)
            amount_to_pay = "{:.2f}".format(sum_of_items)
            check_payment = await self.make_payment(
                new_order.payment_details,
                amount_to_pay,
            )
            if not check_payment:
                return req.req_failure("Problem with payment")
            job = await self._create_job(
                JobType.CreateBooking,
                current_user.user_id,
            )
            booking_model = BookingModel(
                cart=cart,
                total_price=amount_to_pay,
                shipping_address=new_order.shipping_address,
                user_id=current_user.user_id,
            )
            job.create_booking = booking_model
            success, message = await self._add_job_with_one_task(
                job, self.cf.queue_name[1], ResultType.Database
            )
            if success:
                req.result.job_id = job.id
                return req.req_success(message)
            return req.req_failure(message)
        return req.req_failure(" Access is denied")

    async def _get_bookings(
        self,
        req: CreateBookingRequest,
    ) -> GetBookingsResponse:
        return GetBookingsResponse()

    async def _get_booking(self, req: GetBookingRequest) -> GetBookingResponse:
        return GetBookingResponse()

    async def make_payment(
        self,
        data: PaymentDetails,
        amount_to_pay: str,
    ) -> bool:
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
