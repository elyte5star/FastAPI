import os
from pathlib import Path


class ApiConfig:
    def __init__(self) -> None:
        self.sql_url: str = ""
        pass

    def from_toml_file(self):
        pass
