from modules.repository.queries.queue import JobTaskQueries
from modules.repository.schema.queue import QueueItem, Task, Job,JobType


class QueueHandler(JobTaskQueries):

    async def _get_job(self):
        pass

    async def _get_jobs(self, data):
        pass

    async def _get_job_response(self):
        pass

    async def get_task(self):
        pass

    async def _create_job(self, job_type: JobType):
        pass

    async def _add_job_tasks_to_db(
        self,
        job: Job,
        tasks_list: list[Task],
        queue_name: str,
        queue_items_list: list[QueueItem],
    ) -> tuple[bool, str]:
        pass

    async def _add_job_with_one_task(self, job: Job, queue_name: str):
        pass

    async def _check_job_and_tasks(self, job: Job):
        pass

    async def _check_job_result(self, job: Job):
        pass
