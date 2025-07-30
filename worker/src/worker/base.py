from multiprocessing import Process
from worker.src.booking.base import BookingHandler
from worker.src.rabbitmq.base import Queue
from worker.src.config.settings import AppConfig
from worker.src.models.enums import WorkerType, JobType, JobState
from worker.src.models.misc import get_indent, date_time_now_utc
from worker.src.models.base import Worker, QueueItem, Task, Job
import psycopg
import json
from pika.adapters.blocking_connection import BlockingChannel
from pika.spec import BasicProperties
from pika.spec import Basic
from psycopg.types.json import Jsonb


class Consumer(Process):

    def __init__(
        self,
        config: AppConfig,
        worker_type: WorkerType,
        queue_name: str,
        routing_key: str,
    ) -> None:
        super().__init__()
        self.cfg = config
        self.worker_type = worker_type
        self.queue_name = queue_name
        self.routing_key = routing_key

    def create_worker(self) -> Worker:
        worker = Worker()
        worker.id = get_indent()
        worker.worker_type = self.worker_type
        worker.queue_name = self.queue_name
        worker.queue_host = self.cfg.amqp_url
        worker.process_id = str(self.pid)
        return worker

    def db_conn(self):
        try:
            conn = psycopg.connect(self.cfg.database_url)
            return conn
        except psycopg.errors.DatabaseError as e:
            print(e)
            raise

    def insert_worker_into_db(self, worker: Worker):
        with self.db_conn() as conn:
            # Open a cursor to perform database operations
            with conn.cursor() as cur:
                stm = "INSERT INTO worker (id, worker_type,created_at,queue_name,queue_host,process_id) VALUES (%s, %s,%s, %s,%s, %s)"
                data = (
                    worker.id,
                    worker.worker_type.name,
                    worker.created_at,
                    worker.queue_name,
                    worker.queue_host,
                    worker.process_id,
                )
                cur.execute(stm, data)
                # Make the changes to the database persistent
                conn.commit()

    def update_on_going_tasks_in_db(self, task_id: str):
        with self.db_conn() as conn:
            # Open a cursor to perform database operations
            with conn.cursor() as cur:
                stm = "UPDATE task SET status= %s,started= %s WHERE id= %s"
                status = {
                    "state": JobState.PENDING,
                    "success": False,
                    "isFinished": False,
                }
                data = (Jsonb(status), date_time_now_utc(), task_id)
                cur.execute(stm, data)
                # Make the changes to the database persistent
                conn.commit()
                print(f"Rows updated: {cur.rowcount}")

    def call_back(
        self,
        channel: BlockingChannel,
        method: Basic.Deliver,
        properties: BasicProperties,
        body,
    ) -> None:
        # Get job and task from queue item.
        try:
            received = body.decode()
            queue_item_dict = json.loads(received)
            queue_item = QueueItem(**queue_item_dict)
            channel.basic_ack(delivery_tag=method.delivery_tag)
            print(f"[x] Received job with id : {queue_item_dict["job"]["jobId"]}")
            self.do_work(queue_item)
        except Exception as e:
            print(e)

    def update_finished_tasks_in_db(self):

        pass

    def update_result(self):
        pass

    def do_work(self, queue_item: QueueItem):
        try:
            task: Task = queue_item.task
            self.update_on_going_tasks_in_db(task.id)
            job: Job = queue_item.job
            success = False
            match job.job_type:
                case JobType.EMPTY:
                    raise SystemExit("No job on the queue")
                case JobType.SEARCH:
                    raise SystemExit("Create Search job in wrong queue.")
                case JobType.BOOKING:
                    booking = BookingHandler(queue_item, self.db_conn())
                    booking.handle()
                case _:
                    raise SystemExit(f"Unknown job type: {job_type}")

        except Exception as e:
            print(e)
        finally:
            print("yes")

    def run(self) -> None:
        queue: Queue = Queue(self.cfg)
        queue.create_exchange(
            self.queue_name, "elyteExchange", "direct", self.routing_key
        )
        self.insert_worker_into_db(self.create_worker())
        print(" [*] Worker Waiting for JOB.")
        queue.listen_to_queue(self.queue_name, self.call_back)


cfg = AppConfig()

w = Consumer(cfg, WorkerType.BOOKING, "BOOKING", "BOOKING")
w.start()
w.join()
