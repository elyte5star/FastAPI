from typing import Optional, List

# from modules.repository.request_models.booking import BookingModel
from sqlalchemy import Integer, ForeignKey, Enum, PickleType
from modules.database.schema.base import (
    Audit,
    PydanticColumn,
    Base,
    str_60,
    str_pk_60,
    timestamp,
    JSONEncodedDict,
)
from modules.queue.base import JobStatus
from sqlalchemy.orm import mapped_column, Mapped, relationship
from modules.queue.enums import (
    JobType,
    ResultState,
    ResultType,
)
from sqlalchemy.ext.mutable import MutableList, MutableDict


class Job(Audit):
    __mapper_args__ = {
        "polymorphic_identity": "job",
    }
    # add ForeignKey to mapped_column(String, primary_key=True)
    id: Mapped[str_pk_60] = mapped_column(ForeignKey("audit.id"))
    userid: Mapped[str_60] = mapped_column(
        ForeignKey("user.id", onupdate="CASCADE", ondelete="CASCADE"),
        nullable=False,
    )
    job_type: Mapped[JobType] = mapped_column(Enum(JobType), nullable=False)
    tasks: Mapped[List["Task"]] = relationship(cascade="all, delete", lazy="selectin")
    job_status: Mapped[JobStatus] = mapped_column(
        PydanticColumn(JobStatus), nullable=False
    )
    number_of_tasks: Mapped[int] = mapped_column(Integer, nullable=False)
    booking_request: Mapped[Optional[dict[str, str]]] = mapped_column(
        MutableDict.as_mutable(JSONEncodedDict)
    )
    # pep-484 type will be Optional, but column will be
    # NOT NULL
    search_request: Mapped[Optional[dict[str, str]]] = mapped_column(
        MutableDict.as_mutable(JSONEncodedDict)
    )


class Task(Base):
    id: Mapped[str_pk_60]
    job_id: Mapped[str_60] = mapped_column(
        ForeignKey("job.id", onupdate="CASCADE", ondelete="CASCADE"),
        nullable=False,
    )
    result: Mapped["Result"] = relationship(back_populates="task")
    status: Mapped[JobStatus] = mapped_column(
        PydanticColumn(JobStatus), default=JobStatus()
    )
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
    task: Mapped["Task"] = relationship(back_populates="result")
    data: Mapped[dict[str, str]] = mapped_column(
        MutableDict.as_mutable(JSONEncodedDict)
    )
    data_checksum: Mapped[Optional[bytes]]
