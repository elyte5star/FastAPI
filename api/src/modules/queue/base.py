from modules.repository.queries.queue import JobTaskQueries
from modules.queue.enums import JobState, JobType
from modules.queue.models import Job, Task, JobStatus
from modules.queue.models import QueueItem
from modules.utils.misc import get_indent, time_now_utc


class RabbitMQueueHandler(JobTaskQueries):

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
        try:
            
        
        except Exception as e:
            print(e)
            

    async def _add_job_with_one_task(self, job: Job, queue_name: str):
        job.number_of_tasks = 1
        task = Task(
            task_id=get_indent(),
            job_id=job.job_id,
            status=JobStatus(state=JobState.Received),
            created_at=time_now_utc(),
        )
        queue_items_list = [QueueItem(job=job, task=task)]
        success, msg = await self._add_job_tasks_to_db(
            job, [task], queue_name, queue_items_list
        )
        if success:
            return True, msg
        return False, msg
