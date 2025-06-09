from typing import List
from sqlalchemy import Integer, ForeignKey, Enum, UniqueConstraint
from modules.database.schema.base import (
    Audit,
    PydanticColumn,
    Base,
    str_60,
    str_pk_60,
    timestamp,
    JSONEncodedDict,
)
from modules.queue.models import JobStatus
from sqlalchemy.orm import mapped_column, Mapped, relationship
from modules.queue.enums import (
    JobType,
    ResultState,
    ResultType,
)
from sqlalchemy.ext.mutable import MutableDict
from modules.queue.models import BookingModel, SearchModel
from datetime import datetime


class Job(Audit):
    __mapper_args__ = {
        "polymorphic_identity": "job",
    }
    # add ForeignKey to mapped_column(String, primary_key=True)
    id: Mapped[str_pk_60] = mapped_column(ForeignKey("audit.id"))
    user_id: Mapped[str_60] = mapped_column(
        ForeignKey("user.id", onupdate="CASCADE", ondelete="CASCADE"),
        nullable=False,
    )
    job_type: Mapped[JobType] = mapped_column(Enum(JobType), nullable=False)
    tasks: Mapped[List["Task"]] = relationship(
        cascade="all, delete",
        lazy="selectin",
    )
    job_status: Mapped[JobStatus] = mapped_column(
        PydanticColumn(JobStatus), nullable=False
    )
    number_of_tasks: Mapped[int] = mapped_column(Integer, nullable=False)
    create_booking: Mapped[BookingModel | None] = mapped_column(
        PydanticColumn(BookingModel), default=None
    )
    create_search: Mapped[SearchModel | None] = mapped_column(
        PydanticColumn(SearchModel), default=None
    )


class Task(Base):
    id: Mapped[str_pk_60]
    job_id: Mapped[str_60] = mapped_column(
        ForeignKey("job.id", onupdate="CASCADE", ondelete="CASCADE"),
        nullable=False,
    )
    result: Mapped["Result"] = relationship(
        back_populates="task", cascade="all, delete-orphan"
    )
    status: Mapped[JobStatus] = mapped_column(
        PydanticColumn(JobStatus), default=JobStatus()
    )
    created_at: Mapped[timestamp]
    started: Mapped[datetime | None] = mapped_column(
        default=None,
        nullable=True,
    )
    finished: Mapped[datetime | None] = mapped_column(
        default=None,
        nullable=True,
    )


class Result(Base):
    id: Mapped[str_pk_60]
    result_type: Mapped[ResultType] = mapped_column(
        Enum(ResultType), default=ResultType.Database
    )
    result_state: Mapped[ResultState] = mapped_column(Enum(ResultState), nullable=False)
    task_id: Mapped[str_60] = mapped_column(
        ForeignKey("task.id", onupdate="CASCADE", ondelete="CASCADE"),
        nullable=False,
    )
    task: Mapped["Task"] = relationship(
        back_populates="result",
        single_parent=True,
    )
    data: Mapped[dict[str, str] | None] = mapped_column(
        MutableDict.as_mutable(JSONEncodedDict)
    )

    __table_args__ = (UniqueConstraint("task_id"),)
