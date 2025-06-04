from modules.repository.queries.queue import JobTaskQueries
from modules.queue.enums import JobState, JobType, ResultType
from modules.queue import models
from modules.queue import schema
from modules.utils.misc import get_indent, time_now_utc
import hashlib
from aio_pika import Message, connect, DeliveryMode


class RQHandler(JobTaskQueries):

    async def _create_job(self, job_type: JobType, userid: str) -> models.Job:
        new_job = models.Job()
        new_job.user_id = userid
        new_job.job_type = job_type
        new_job.job_id = get_indent()
        new_job.job_status.state = JobState.Pending
        new_job.created_at = time_now_utc()
        return new_job

    def create_checksum(self, data: str) -> str:
        digest = hashlib.sha256()
        digest.update(data.encode("utf-8"))
        return digest.hexdigest()

    def validate_checksum(self, data: str, checksum: str) -> bool:
        return self.create_checksum(data) == checksum

    async def create_task_result(
        self, result_type: ResultType, task_id: str
    ) -> models.Result:
        new_result = models.Result()
        new_result.result_id = get_indent()
        new_result.result_type = result_type
        new_result.task_id = task_id
        return new_result

    async def _add_job_tasks_to_queue(
        self,
        job: models.Job,
        tasks: list[models.Task],
        queue_name: str,
        queue_items: list[models.QueueItem],
        result_type: ResultType,
    ) -> tuple[bool, str]:
        try:
            sql_job_model = schema.Job(
                id=job.job_id,
                user_id=job.user_id,
                job_type=job.job_type,
                job_status=job.job_status,
                number_of_tasks=job.number_of_tasks,
                create_booking=job.create_booking,
                create_search=job.create_search,
                created_at=job.created_at,
            )
            await self.add_job_to_db_query(sql_job_model)
            for task in tasks:
                task_result = await self.create_task_result(result_type, task.task_id)
                sql_task_model = schema.Task(
                    id=task.task_id,
                    job_id=task.job_id,
                    created_at=task.created_at,
                    status=task.status,
                )
                await self.add_tasks_to_db_query(task)
                await self.add_task_result_db_query(task_result)
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
                            queue_item.model_dump_json().encode(),
                            delivery_mode=DeliveryMode.PERSISTENT,
                        ),
                        routing_key=queue_name,
                    )
            pass

        except Exception as e:
            return (False, f"Failed to create job. {str(e)}.")
        else:
            return (True, f"Job with id '{job.job_id}' created.")

    async def _add_job_with_one_task(
        self, job: models.Job, queue_name: str, result_type: ResultType
    ) -> tuple[bool, str]:
        job.number_of_tasks = 1
        task = models.Task(
            task_id=get_indent(),
            job_id=job.job_id,
            status=models.JobStatus(state=JobState.Received),
            created_at=time_now_utc(),
        )
        queue_items = [models.QueueItem(job=job, task=task)]
        success, message = await self._add_job_tasks_to_queue(
            job, [task], queue_name, queue_items, result_type
        )
        return success, message
