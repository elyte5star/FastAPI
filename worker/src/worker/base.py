from multiprocessing import Process


class BaseWorker(Process):
    def __init__(self) -> None:
        pass

    def create_worker(self):
        pass

    def create_db_conn(self):
        pass

    def update_on_going_job_with_tasks_in_db(self):
        pass

    def update_finished_job_with_tasks_in_db(self):
        pass
