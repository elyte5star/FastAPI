from pydantic import Field, BaseModel
from datetime import datetime
from modules.queue.enums import JobType
from modules.queue.models import Job
from modules.queue.schema import JobStatus
from modules.repository.request_models.base import BaseResponse


class JobResponse(BaseModel):
    user_id: str = Field(default="", serialization_alias="userId")
    start_time: datetime | None = None
    stop_time: datetime | None = None
    process_time: float = 0.0
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
    jobs_status: list[JobResponse] = []


class GetJobResponse(BaseResponse):
    job_status: JobResponse | None = None


class CreateJobResponse(BaseResponse):
    job: Job | None = None


class GetJobRequestResponse(BaseResponse):
    job_id: str = Field(default="", serialization_alias="jobId")
