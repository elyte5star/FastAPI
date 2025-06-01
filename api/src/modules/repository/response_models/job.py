from modules.repository.request_models.base import BaseResponse
from modules.queue.enums import (
    JobType,
)
from pydantic import Field
from modules.queue.schema import (
    JobStatus,
)
from modules.queue.base import Job


class GetJobResponse(BaseResponse):
    userid: str = Field(default="", serialization_alias="userId")
    start_time: float = 0.0
    stop_time: float = 0.0
    process_time: str = ""
    job_type: JobType = Field(
        default=JobType.Empty,
        serialization_alias="jobType",
    )
    job_id: str = Field(default="", serialization_alias="jobId")
    job_status: JobStatus = Field(
        default=JobStatus(),
        serialization_alias="jobStatus",
    )


class GetJobsResponse(BaseResponse):
    jobs: list[GetJobResponse] = []


class CreateJobResponse(BaseResponse):
    job: Job | None = None


class JobResponse(BaseResponse):
    job_id: str = Field(default="", serialization_alias="jobId")
