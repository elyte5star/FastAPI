from enum import Enum


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
    Present = "10"
    Archived = "30"
    Removed = "30"


class ResultType(str, Enum):
    Noop = "0"
    Database = "10"
    File = "30"
