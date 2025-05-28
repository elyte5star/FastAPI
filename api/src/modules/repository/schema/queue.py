from typing import Optional, Any
from datetime import datetime
from enum import Enum
from modules.utils.misc import time_now_utc
from typing_extensions import Annotated
from modules.repository.request_models.booking import BookingModel
from sqlalchemy import (
    Integer,
    ForeignKey,
    Enum,
    JSON,
)
from modules.repository.schema.base import (
    Audit,
    PydanticColumn,
    Base,
    str_60,
    str_pk_60,
    required_60,
    timestamp,
)
from sqlalchemy.orm import relationship, Mapped
from modules.queue.base import JobType, JobStatus, ResultType, ResultState
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column


class Job(Audit):
    # add ForeignKey to mapped_column(String, primary_key=True)
    id: Mapped[str_pk_60] = mapped_column(ForeignKey("audit.id"))
    userid: Mapped[str_60] = mapped_column(
        ForeignKey("user.id", onupdate="CASCADE", ondelete="CASCADE"),
        nullable=False,
    )
    job_type: Mapped[JobType] = mapped_column(Enum(JobType), nullable=False)
    task_ids: Mapped[list[str]] = mapped_column(default=[])
    job_status: Mapped[JobStatus] = mapped_column(
        PydanticColumn(JobStatus), nullable=False
    )
    number_of_tasks: Mapped[int] = mapped_column(Integer, nullable=False)
    booking_request: Mapped[Optional[BookingModel]] = mapped_column(
        PydanticColumn(BookingModel), nullable=True
    )
    # pep-484 type will be Optional, but column will be
    # NOT NULL
    search_request: Mapped[Optional[JSON]]


class Task(Base):
    id: Mapped[str_pk_60]
    job_id: Mapped[str_60] = mapped_column(
        ForeignKey("job.id", onupdate="CASCADE", ondelete="CASCADE"),
        nullable=False,
    )
    result_id: Mapped[str_60] = mapped_column(
        ForeignKey("result.id", onupdate="CASCADE", ondelete="CASCADE"),
        nullable=False,
    )
    status: JobStatus = JobStatus()
    created_at: Mapped[timestamp]
    started: Mapped[Optional[timestamp]]
    finished: Mapped[Optional[timestamp]]


class Result(Base):
    id: Mapped[str_pk_60]
    result_type: Mapped[ResultType] = mapped_column(
        Enum(ResultType), default=ResultType.Database
    )
    result_state: Mapped[ResultState] = mapped_column(
        Enum(ResultState), default=ResultState.NotSet
    )
    task_id: Mapped[str_60] = mapped_column(
        ForeignKey("task.id", onupdate="CASCADE", ondelete="CASCADE"),
        nullable=False,
    )
    data: Mapped[Optional[JSON]]
    data_checksum: Mapped[Optional[JSON]]
