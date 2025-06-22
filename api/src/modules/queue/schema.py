from typing import List
from sqlalchemy import Integer, ForeignKey, Enum, UniqueConstraint
from modules.database.schema.base import (
    Audit,
    PydanticColumn,
    Base,
    str_60,
    str_pk_60,
    str_500,
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
    booking: Mapped[dict[str, str] | None] = mapped_column(
        MutableDict.as_mutable(JSONEncodedDict)
    )
    search: Mapped[dict[str, str] | None] = mapped_column(
        MutableDict.as_mutable(JSONEncodedDict)
    )

    def __repr__(self):
        return (
            f"<{self.__class__.__name__}("
            f" id:{self.id}, "
            f" user_id:{self.user_id}, "
            f" status:{self.job_status},"
            f" number_of_tasks:{self.number_of_tasks},"
            f" tasks:{self.tasks}, "
            f" booking_request:{self.booking},"
            f" search_request:{self.search},"
            f" created_at:{self.created_at},"
            f" created_by:{self.created_by},"
            f" modified_at:{self.modified_at},"
            f" modified_by:{self.modified_by}"
            f")>"
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
    data_checksum: Mapped[str_500 | None] = mapped_column(
        default=None,
        nullable=True,
    )

    __table_args__ = (UniqueConstraint("task_id"),)
