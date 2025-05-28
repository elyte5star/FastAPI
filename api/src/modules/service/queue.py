from modules.repository.queries.queue import JobTaskQueries
from modules.repository.schema.queue import (
    QueueItem,
    Task,
    JobStatus,
    Job,
    JobType,
    JobState,
)
from modules.utils.misc import get_indent, time_now_utc


class QueueHandler(JobTaskQueries):

    async def _get_job(self):
        pass

    async def _get_jobs(self, data):
        pass

    async def _get_job_response(self):
        pass

    async def get_task(self):
        pass

    async def _create_job(self, job_type: JobType, userid: str) -> Job:
        new_job = Job()
        new_job.userid = userid
        new_job.job_type = job_type
        new_job.job_id = get_indent()
        new_job.job_status.state = JobState.Pending
        new_job.created_at = time_now_utc()
        return new_job

    async def _add_job_tasks_to_db(
        self,
        job: Job,
        tasks_list: list[Task],
        queue_name: str,
        queue_items_list: list[QueueItem],
    ) -> tuple[bool, str]:
        pass

    async def _add_job_with_one_task(self, job: Job, queue_name: str):
        job.number_of_tasks = 1
        task = Task(
            task_id=get_indent(),
            job_id=job.job_id,
            status=JobStatus(state=JobState.Received),
            created_at=time_now_utc(),
        )
        queue_items_list = [QueueItem(job, task)]
        success, msg = self._add_job_tasks_to_db(
            job, [task], queue_items_list, queue_name
        )
        if success:
            return True, msg
        return False, msg

    async def _check_job_and_tasks(self, job: Job):
        pass

    async def _check_job_result(self, job: Job):
        pass
