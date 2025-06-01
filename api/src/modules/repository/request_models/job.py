from modules.repository.request_models.base import BaseReq
from modules.repository.response_models.job import (
    GetJobResponse,
    GetJobsResponse,
    CreateJobResponse,
)
from modules.queue.base import Job


class GetJobRequest(BaseReq):
    job_id: str = ""
    result: GetJobResponse = GetJobResponse()


class GetJobsRequest(BaseReq):
    result: GetJobsResponse = GetJobsResponse()


class CreateJobRequest(BaseReq):
    new_job: Job | None = None
    result: CreateJobResponse = CreateJobResponse()
