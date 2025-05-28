from typing import Optional, Any
from pydantic import BaseModel, Field, ConfigDict, Json
from datetime import datetime
from enum import Enum
from modules.utils.misc import time_now_utc
from typing_extensions import Annotated
from modules.repository.request_models.booking import BookingModel


class JobType(str, Enum):
    Noop = "0"
    CreateSearch = "10"
    CreateBooking = "30"


class JobState(str, Enum):
    NotSet = "0"
    Received = "10"
    Pending = "20"
    Finished = "30"
    Timeout = "666"
    NoTasks = "999"


class ResultState(str, Enum):
    NotSet = "0"
    Present = "10"
    Archived = "30"
    Removed = "30"


class ResultType(str, Enum):
    Noop = "0"
    Database = "10"
    File = "30"


class JobStatus(BaseModel):
    state: JobState = JobState.NotSet
    success: bool = False
    is_finished: bool = Field(default=False, serialization_alias="isFinished")
    model_config = ConfigDict(serialize_by_alias=True)


class Job(BaseModel):
    userid: str = Field(default="", serialization_alias="userId")
    created_at: datetime = Field(
        default=time_now_utc(), serialization_alias="createdAt"
    )
    job_type: JobType = Field(default=JobType.Noop, serialization_alias="jobType")
    job_id: str = Field(default="", serialization_alias="jobId")
    task_ids: list = Field(default=[], serialization_alias="taskIds")
    job_status: Annotated[
        JobStatus, Field(default=JobStatus(), serialization_alias="jobStatus")
    ]
    number_of_tasks: int = Field(default=0, serialization_alias="numberOfTasks")
    booking_request: Optional[
        Annotated[
            BookingModel, Field(default=None, serialization_alias="bookingRequest")
        ]
    ]
    search_request: Optional[
        Annotated[Any, Field(default=None, serialization_alias="searchRequest")]
    ]

    model_config = ConfigDict(serialize_by_alias=True)


class Task(BaseModel):
    task_id: str = Field(default="", serialization_alias="taskId")
    job_id: str = Field(default="", serialization_alias="jobId")
    result_id: str = ""
    status: JobStatus = JobStatus()
    created_at: Optional[
        Annotated[datetime, Field(default=None, serialization_alias="createdAt")]
    ]
    started: Optional[datetime] = None
    finished: Optional[datetime] = None

    model_config = ConfigDict(serialize_by_alias=True)


class Result(BaseModel):
    result_id: str = Field(default="", serialization_alias="resultId")
    result_type: ResultType = ResultType.Database
    result_state: ResultState = ResultState.NotSet
    task_id: str = Field(default="", serialization_alias="taskId")
    data: Json = None
    data_checksum: Optional[str] = None


class ResultLog(BaseModel):
    result_id: str = ""
    created_at: datetime = time_now_utc()
    handled: bool = False
    handled_date: Optional[
        Annotated[datetime.date, Field(default=None, serialization_alias="handledDate")]
    ]

    model_config = ConfigDict(serialize_by_alias=True)


class QueueItem(BaseModel):
    job: Optional[Job] = None
    task: Optional[Task] = None
