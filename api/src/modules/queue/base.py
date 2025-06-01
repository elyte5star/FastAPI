from typing import Optional
from pydantic import BaseModel, Field, ConfigDict, Json
from datetime import datetime
from modules.utils.misc import time_now_utc
from typing_extensions import Annotated
from decimal import Decimal

# from modules.repository.request_models.booking import BookingModel
from modules.queue.enums import (
    JobState,
    JobType,
    ResultState,
    ResultType,
)


class CartItem(BaseModel):
    price: Decimal
    discount: Decimal
    quantity: int
    pid: str
    calculated_price: Annotated[
        Decimal, Field(serialization_alias="calculatedPrice", repr=True)
    ]
    model_config = ConfigDict(extra="forbid", serialize_by_alias=True)


class ShippingDetails(BaseModel):
    full_name: Annotated[str, Field(serialization_alias="fullName", repr=True)]
    street_address: Annotated[
        str,
        Field(
            serialization_alias="streetAddress",
            repr=True,
        ),
    ]
    country: str
    state: str
    email: str
    zip_code: Annotated[str, Field(serialization_alias="zip", repr=True)]
    model_config = ConfigDict(extra="forbid", serialize_by_alias=True)


class BookingModel(BaseModel):
    cart: list[CartItem]
    total_price: Annotated[
        Decimal,
        Field(
            serialization_alias="totalPrice",
            repr=True,
        ),
    ]
    shipping_details: Annotated[
        ShippingDetails,
        Field(
            serialization_alias="shippingDetails",
            repr=True,
        ),
    ]
    userid: str = Field(serialization_alias="userId", repr=True)

    model_config = ConfigDict(serialize_by_alias=True)


class SearchModel(BaseModel):
    text: list[str] = []
    categories: list[str] = []
    return_count: Optional[int]
    model_config = ConfigDict(extra="allow")


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
    job_type: JobType = Field(
        default=JobType.Empty,
        serialization_alias="jobType",
    )
    job_id: str = Field(default="", serialization_alias="jobId")
    task_ids: list = Field(default=[], serialization_alias="taskIds")
    job_status: JobStatus = Field(
        default=JobStatus(),
        serialization_alias="jobStatus",
    )
    number_of_tasks: int = Field(
        default=0,
        serialization_alias="numberOfTasks",
    )
    create_booking: Optional[
        Annotated[
            BookingModel,
            Field(
                default=None,
                serialization_alias="createBooking",
            ),
        ]
    ]
    create_search: Optional[
        Annotated[
            SearchModel,
            Field(default=None, serialization_alias="createSearch"),
        ]
    ]

    model_config = ConfigDict(serialize_by_alias=True)


class Task(BaseModel):
    task_id: str = Field(default="", serialization_alias="taskId")
    job_id: str = Field(default="", serialization_alias="jobId")
    result_id: str = ""
    status: JobStatus = JobStatus()
    created_at: Optional[
        Annotated[
            datetime,
            Field(
                default=None,
                serialization_alias="createdAt",
            ),
        ]
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
        Annotated[
            datetime,
            Field(
                default=None,
                serialization_alias="handledDate",
            ),
        ]
    ]

    model_config = ConfigDict(serialize_by_alias=True)


class QueueItem(BaseModel):
    job: Optional[Job] = None
    task: Optional[Task] = None
