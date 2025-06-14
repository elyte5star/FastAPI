from pydantic import BaseModel, Field, ConfigDict, Json, computed_field
from datetime import datetime
from modules.utils.misc import date_time_now_utc
from typing_extensions import Annotated
from decimal import Decimal
from modules.repository.validators.base import ValidateUUID
from modules.queue.enums import (
    JobState,
    JobType,
    ResultState,
    ResultType,
)


class CartItem(BaseModel):
    price: float = Field(
        repr=True,
        gt=0,
    )
    discount: float
    quantity: Annotated[
        int,
        Field(
            examples=[1, 3, 4],
            strict=True,
            repr=True,
            gt=0,
        ),
    ]
    pid: ValidateUUID

    @computed_field
    @property
    def calculated_price(self) -> str:
        discount = Decimal(self.price) * Decimal(self.discount)
        sale_price = Decimal(self.price) - discount
        amount = sale_price * self.quantity
        return "{:.2f}".format(amount)

    model_config = ConfigDict(extra="forbid")


class ShippingAddress(BaseModel):
    first_name: Annotated[
        str,
        Field(
            validation_alias="firstName",
            serialization_alias="firstName",
        ),
    ]
    last_name: Annotated[
        str, Field(validation_alias="lastName", serialization_alias="lastName")
    ]
    street_address: Annotated[
        str,
        Field(
            validation_alias="streetAddress",
            serialization_alias="streetAddress",
        ),
    ]
    country: str
    state: str
    email: str
    zip_code: Annotated[
        str,
        Field(
            validation_alias="zipCode",
            serialization_alias="zipCode",
        ),
    ]
    model_config = ConfigDict(extra="forbid", serialize_by_alias=True)


class BookingModel(BaseModel):
    cart: list[CartItem]
    total_price: Annotated[
        str,
        Field(
            serialization_alias="totalPrice",
            repr=True,
        ),
    ]
    shipping_address: Annotated[
        ShippingAddress,
        Field(
            serialization_alias="shippingAddress",
            repr=True,
        ),
    ]
    user_id: str = Field(serialization_alias="userId", repr=True)

    model_config = ConfigDict(serialize_by_alias=True)


class SearchModel(BaseModel):
    text: list[str] = []
    categories: list[str] = []
    return_count: int | None = Field(
        None, exclude=False, serialization_alias="returnCount"
    )
    model_config = ConfigDict(extra="allow")


class JobStatus(BaseModel):
    state: JobState = JobState.NotSet
    success: bool = False
    is_finished: bool = Field(default=False, serialization_alias="isFinished")
    model_config = ConfigDict(serialize_by_alias=True)


class Job(BaseModel):
    id: str = Field(default="", serialization_alias="jobId")
    user_id: str = Field(default="", serialization_alias="userId")
    job_type: JobType = Field(
        default=JobType.Empty,
        serialization_alias="jobType",
    )
    created_at: datetime = Field(
        default=date_time_now_utc(), serialization_alias="createdAt"
    )
    job_status: JobStatus = Field(
        default=JobStatus(),
        serialization_alias="jobStatus",
    )
    number_of_tasks: int = Field(
        default=0,
        serialization_alias="numberOfTasks",
    )
    create_booking: BookingModel | None = Field(
        default=None,
        serialization_alias="bookingRequest",
    )
    create_search: SearchModel | None = Field(
        default=None, serialization_alias="searchRequest"
    )

    model_config = ConfigDict(serialize_by_alias=True, from_attributes=True)


class Task(BaseModel):
    id: str = Field(default="", serialization_alias="taskId")
    job_id: str = Field(default="", serialization_alias="jobId")
    status: JobStatus = JobStatus()
    created_at: datetime | None = Field(
        default=None,
        serialization_alias="createdAt",
    )

    started: datetime | None = None
    finished: datetime | None = None

    model_config = ConfigDict(serialize_by_alias=True, from_attributes=True)


class Result(BaseModel):
    id: str = Field(default="", serialization_alias="resultId")
    result_type: ResultType = ResultType.Database
    result_state: ResultState = ResultState.NotSet
    task_id: str = Field(serialization_alias="taskId")
    data: Json = None
    data_checksum: str | None = None


class ResultLog(BaseModel):
    result_id: str = ""
    created_at: datetime = date_time_now_utc()
    handled: bool = False
    handled_date: datetime | None = Field(
        default=None,
        serialization_alias="handledDate",
    )

    model_config = ConfigDict(serialize_by_alias=True)


class QueueItem(BaseModel):
    job: Job | None = None
    task: Task | None = None
