from enum import Enum


class WorkerType(str, Enum):
    NONE = "0"
    BOOKING = "1"
    SEARCH = "2"


class JobType(str, Enum):
    Empty = "0"
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
    Pending = "10"
    Present = "20"
    Archived = "30"
    Removed = "40"


class ResultType(str, Enum):
    Unknown = "0"
    Database = "10"
    File = "30"
