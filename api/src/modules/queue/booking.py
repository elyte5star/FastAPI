from modules.database.schema.product import Product
from modules.repository.request_models.booking import (
    CreateBookingRequest,
    PaymentDetails,
    BookingResultRequest,
)
from modules.repository.response_models.booking import (
    GetBookingsResponse,
)
from modules.repository.response_models.job import BaseResponse
from decimal import Decimal
from modules.queue.base import RQHandler, JobType, ResultType, JobState
from modules.queue.models import (
    BookingModel,
    CartItem,
    Task,
    QueueItem,
    JobStatus,
    TaskResult,
    Job,
)
from modules.utils.misc import get_indent, date_time_now_utc, time_then


class BookingHandler(RQHandler):

    async def _create_booking(
        self,
        req: CreateBookingRequest,
    ) -> BaseResponse:
        if req.credentials is None:
            return req.req_failure("No valid user session found")
        current_user = req.credentials
        new_order = req.new_order
        if current_user.user_id != new_order.user_id:
            self.logger.warning(
                f"illegal operation by {current_user.user_id}",
            )
            return req.req_failure("Forbidden: Access is denied")
        cart: list[CartItem] = new_order.cart
        check_cart = await self.check_products(cart)
        avaliable_prods, unavaliable_items = check_cart
        if unavaliable_items:
            return req.req_failure(f"Product(s):{unavaliable_items} out of stock")
        sum_of_items = sum(Decimal(item.calculated_price) for item in cart)
        amount_to_pay = "{:.2f}".format(sum_of_items)
        check_payment = await self.make_payment(
            new_order.payment_details,
            amount_to_pay,
        )
        if not check_payment:
            return req.req_failure("Problem with payment")
        await self.update_products_in_db(avaliable_prods)
        job = self._create_job(
            JobType.BOOKING,
            current_user.user_id,
        )
        booking_model = BookingModel(
            cart=cart,
            total_price=amount_to_pay,
            shipping_address=new_order.shipping_address,
            user_id=current_user.user_id,
        )
        job.booking = booking_model
        tasks, queue_items, tasks_result = ([], [], [])
        for item in cart:
            task = Task(
                id=get_indent(),
                job_id=job.id,
                status=JobStatus(state=JobState.RECEIVED),
                created_at=date_time_now_utc(),
                finished=time_then(),
            )
            result = self.create_task_result(ResultType.DATABASE, task.id)
            tasks.append(task)
            tasks_result.append(result)
            queue_items.append(QueueItem(job=job, task=task, result=result))
        job.number_of_tasks = len(tasks)
        QUEUE = self.cf.queue_name[1]
        success, message = await self._add_job_tasks_to_queue(
            job,
            tasks,
            tasks_result,
            QUEUE,
            queue_items,
        )
        if success:
            req.result.job_id = job.id
            return req.req_success(message)
        return req.req_failure(message)

    async def update_products_in_db(
        self,
        avaliable_prods: list[tuple[Product, int]],
    ):
        for item in avaliable_prods:
            product_in_db, quantity_requested = item
            pid = product_in_db.id
            new_quantity = product_in_db.stock_quantity - quantity_requested
            await self.update_product_info_query(
                pid,
                dict(stock_quantity=new_quantity),
            )

    async def _get_bookings(
        self,
        req: CreateBookingRequest,
    ) -> GetBookingsResponse:
        return GetBookingsResponse()

    async def _get_booking_result(
        self,
        req: BookingResultRequest,
    ) -> BaseResponse:
        job_id = req.job_id
        job_in_db = await self.find_job_by_id(job_id)
        if job_in_db is None:
            return req.req_failure(f"No job with id::{req.job_id}")
        job = Job.model_validate(job_in_db)
        if job.job_type != JobType.BOOKING:
            return req.req_failure("Wrong job type")
        req.result.job = await self.get_job_response(job)
        if not self.is_job_result_available(job):
            return req.req_failure("No result for job")
        req.result.data = await self.create_booking_result(job.tasks)
        return req.req_success(
            f"Success getting result for job with id: {job_id}.",
        )

    async def create_booking_result(self, tasks: list[Task]) -> dict:
        result = {}
        if not tasks:
            return result
        for task in tasks:
            result_in_db = await self.find_result_by_task_id(task.id)
            res = TaskResult.model_validate(result_in_db)
            result[task.job_id] = (task.id, dict(res))
        return result

    async def make_payment(
        self,
        data: PaymentDetails,
        amount_to_pay: str,
    ) -> bool:
        # TODO implement card payment
        return True

    async def check_products(self, cart: list[CartItem]) -> tuple[list, list]:
        avaliable_prods, unavaliable_prods = [], []
        for item in cart:
            product_in_db = await self.find_product_by_id(item.pid)
            if product_in_db is None or product_in_db.stock_quantity < item.quantity:
                unavaliable_prods.append(item)
            else:
                avaliable_prods.append((product_in_db, item.quantity))
        return (avaliable_prods, unavaliable_prods)
