from multiprocessing import Process
from config.settings import AppConfig
from models.enums import WorkerType
from models.misc import get_indent
from models.base import Worker,QueueItem
import psycopg
from psycopg.connection import Connection


class BaseWorker(Process):

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

    def insert_work_ito_db(self, worker: Worker):
        with self.db_conn() as conn:
            # Open a cursor to perform database operations
            with conn.cursor() as cur:
                stm = "INSERT INTO worker (id, worker_type,created,queue_name,queue_host,process_id) VALUES (%s, %s,%s, %s,%s, %s)"
                data = (
                    worker.id,
                    worker.worker_type,
                    worker.created_at,
                    worker.queue_name,
                    worker.queue_host,
                    worker.process_id,
                )
                cur.execute(stm, data)
                # Make the changes to the database persistent
                conn.commit()

    def update_on_going_tasks_in_db(self,):

        pass

    def update_finished_asks_in_db(self):

        pass
    def do_work(self,queue_item:QueueItem)
    def run(self) -> None:
        return
