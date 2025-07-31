from modules.repository.request_models.job import GetJobRequest, GetJobsRequest, Job
from modules.repository.response_models.job import JobResponse, BaseResponse
from datetime import datetime
from modules.queue.enums import JobState
from modules.utils.misc import time_then
from modules.repository.queries.common import CommonQueries


class JobHandler(CommonQueries):

    async def _get_job(self, req: GetJobRequest) -> BaseResponse:
        job_in_db = await self.find_job_by_id(req.job_id)
        if job_in_db is None:
            return req.req_failure(f"No job with id::{req.job_id}")
        job = Job.model_validate(job_in_db)
        req.result.job_status = await self.get_job_response(job)
        return req.req_success(
            f"Success getting status for job with id: {req.job_id}.",
        )

    async def _get_jobs(self, req: GetJobsRequest) -> BaseResponse:
        jobs_in_db = await self.get_jobs_query()
        jobs_status = [
            await self.get_job_response(Job.model_validate(job_in_db))
            for job_in_db in jobs_in_db
        ]
        req.result.jobs_status = jobs_status
        return req.req_success(
            f"{len(jobs_status)} found!",
        )

    async def get_job_response(self, job: Job) -> JobResponse:
        states, successes, stops = ([], [], [])
        tasks_exist = False
        tasks = await self.find_tasks_by_job_id(job.id)
        for task in tasks:
            tasks_exist = True
            states.append(task.status.state)
            successes.append(task.status.success)
            stops.append(task.finished)
        if not tasks_exist:
            job.job_status.state = JobState.NoTasks
            job.job_status.success = False
            job.job_status.is_finished = True
            return self.create_job_response(job)

        stops.sort()
        success = True
        state = JobState.FINISHED.name
        is_finished = True
        
        if JobState.TIMEOUT in states:
            state = JobState.TIMEOUT.name
            success = False
            is_finished = True
        elif JobState.NOTSET in states:
            state = JobState.NOTSET.name
            success = False
            is_finished = False
        elif JobState.RECEIVED in states:
            state = JobState.PENDING.name
            success = False
            is_finished = False
        elif JobState.PENDING in states:
            state = JobState.PENDING.name
            success = False
            is_finished = False

        job.job_status.state = state
        job.job_status.success = success
        job.job_status.is_finished = is_finished
        return self.create_job_response(job, stops[-1])

    def create_job_response(
        self, job: Job, stopped: datetime = time_then()
    ) -> JobResponse:
        return JobResponse(
            user_id=job.user_id,
            start_time=job.created_at,
            stop_time=stopped,
            job_type=job.job_type,
            job_id=job.id,
            job_status=job.job_status,
            process_time=float((stopped - job.created_at).total_seconds()),
        )

    def is_job_result_available(self, job: Job) -> bool:
        if job.job_status.is_finished is False:
            return False
        if job.job_status.state != JobState.FINISHED:
            return False
        return job.job_status.success
