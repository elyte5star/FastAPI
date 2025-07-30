from worker.src.models.base import Worker, QueueItem, Task, Job, BookingModel
from psycopg.connection import Connection
from worker.src.models.misc import get_indent, date_time_now_utc
import pickle


class BookingHandler:

    def __init__(self, queue_item: QueueItem, db_conn: Connection) -> None:
        self.queue_item = queue_item
        self.db_conn = db_conn

    def handle(self) -> tuple[bool, dict]:
        booking_request: BookingModel = self.queue_item.job.booking
        num_of_tasks = self.queue_item.job.number_of_tasks
        with self.db_conn.cursor() as cur:
            stm = "INSERT INTO booking (id, user_id,cart,address,created_at,total_price) VALUES (%s, %s,%s, %s,%s, %s)"
            # Serialize the list using pickle
            pickled_data = pickle.dumps(booking_request.cart)
            data = (
                get_indent(),
                booking_request.user_id,
                pickled_data,
                booking_request.shipping_address.model_dump_json(),
                date_time_now_utc(),
                booking_request.total_price,
            )
            cur.execute(stm, data)
            # Make the changes to the database persistent
            self.db_conn.commit()
            print(f"Rows updated: {cur.rowcount}")

        return (False, {})

    def purchase_product(self, booking_request: BookingModel):
        pass
