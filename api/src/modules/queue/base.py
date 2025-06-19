from modules.repository.queries.queue import JobTaskQueries
from modules.queue.enums import JobState, JobType, ResultType, ResultState
from modules.queue import models
from modules.queue import schema
from modules.utils.misc import get_indent, date_time_now_utc
import hashlib
from aio_pika import Message, connect, DeliveryMode


class RQHandler(JobTaskQueries):

    async def _create_job(self, job_type: JobType, user_id: str) -> models.Job:
        job = models.Job()
        job.user_id = user_id
        job.job_type = job_type
        job.id = get_indent()
        job.job_status.state = JobState.Pending
        job.created_at = date_time_now_utc()
        job.created_by = user_id
        return job

    def create_checksum(self, data: str) -> str:
        digest = hashlib.sha256()
        digest.update(data.encode("utf-8"))
        return digest.hexdigest()

    def validate_checksum(self, data: str, checksum: str) -> bool:
        return self.create_checksum(data) == checksum

    def create_task_result(
        self, result_type: ResultType, task_id: str
    ) -> models.Result:
        return models.Result(
            id=get_indent(),
            task_id=task_id,
            result_type=result_type,
            result_state=ResultState.Pending,
        )

    async def _add_job_tasks_to_queue(
        self,
        job: models.Job,
        tasks: list[models.Task],
        results: list[models.Result],
        queue_name: str,
        queue_items: list[models.QueueItem],
    ) -> tuple[bool, str]:
        try:
            # ADD JOB,TASK,RESULT TO DB
            aux_job = job
            aux_job.booking = job.booking.model_dump()
            new_job = schema.Job(**dict(aux_job))
            _ = await self.add_job_to_db_query(new_job)
            for task, result in zip(tasks, results):
                new_task = schema.Task(**dict(task))
                _ = await self.add_task_to_db_query(new_task)
                new_result = schema.Result(**dict(result))
                _ = await self.add_task_result_db_query(new_result)

            # Perform connection
            connection = await connect(self.cf.rabbit_connect_string)
            async with connection:
                # Creating a channel
                channel = await connection.channel()
                # Declaring queue
                _ = await channel.declare_queue(queue_name, durable=True)
                for queue_item in queue_items:
                    # Sending the message
                    await channel.default_exchange.publish(
                        Message(
                            queue_item.model_dump_json(by_alias=True).encode(),
                            delivery_mode=DeliveryMode.PERSISTENT,
                        ),
                        routing_key=queue_name,
                    )
            pass

        except Exception as e:
            self.cf.logger.error(f"Error creating JOB:: {str(e)}")
            return (False, f"Failed to create job. {str(e)}.")
        else:
            return (True, f"Job with id '{job.id}' created.")

    async def _add_job_with_one_task(
        self, job: models.Job, queue_name: str, result_type: ResultType
    ) -> tuple[bool, str]:
        job.number_of_tasks = 1
        task = models.Task(
            id=get_indent(),
            job_id=job.id,
            status=models.JobStatus(state=JobState.Received),
            created_at=date_time_now_utc(),
        )
        task_result = self.create_task_result(
            result_type,
            task.id,
        )
        queue_items = [models.QueueItem(job=job, task=task)]
        success, message = await self._add_job_tasks_to_queue(
            job,
            [task],
            [task_result],
            queue_name,
            queue_items,
        )
        return success, message
