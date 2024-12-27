from pathlib import Path
from os import getenv, path
from pyconfs import Configuration
import json
from pprint import pprint
from dotenv import load_dotenv
import logging
from typing import Any, Dict, Self

load_dotenv()


project_root = Path(__file__).parent.parent.parent
toml_path = path.join(project_root, "pyproject.toml")
config = Configuration.from_file(toml_path)


class ApiConfig:

    def __init__(self) -> None:
        # API
        self.log_type: str = ""
        self.log_file_path: str = ""
        self.host_url: str = ""
        self.debug: bool = False
        self.auth_type: str = ""
        self.origins: list[str] = ["*"]
        self.pwd_len: int = 0
        self.round: int = 0
        self.encoding: str = ""
        self.sql_url: str = ""
        self.logger: logging.Logger = None
        self.queries: Dict[Any, Any] = None

        # PROJECT DETAILS
        self.name: str = ""
        self.version: str = ""
        self.description: str = ""
        self.terms: str = ""
        self.contacts: dict = {}
        self.license: dict = {}

        # JWT PARAMS
        self.algorithm: str = ""
        self.secret_key: str = ""
        self.token_expire_min: int = 0
        self.refresh_token_expire_min: int = 0
        self.token_url: str = ""
        self.grant_type: str = ""

        # MSOFT AUTH
        self.msal_login_authority: str = ""
        self.msal_client_id: str = ""
        self.msal_issuer: str = ""

        # CLIENT
        self.client_url: str = ""

    def from_toml_file(self) -> Self:
        self.sql_username = config.database.user
        self.sql_password = config.database.pwd
        self.sql_host = config.database.host
        self.sql_port = config.database.port
        self.sql_db = config.database.db
        self.db_url = f"postgresql+asyncpg://{self.sql_username}:{self.sql_password}@{self.sql_host}:{self.sql_port}/{self.sql_db}"
        self.log_type = config.api.log_type
        self.log_file_path = config.api.log_file_path
        self.host_url = config.api.host_url
        self.debug = config.api.debug
        self.auth_type = config.api.auth_type

        self.pwd_len = config.encryption.length
        self.rounds = config.encryption.rounds
        self.encoding = config.encryption.encoding

        self.name = config.api.doc["name"]
        self.terms = config.api.doc.terms_of_service
        self.version = config.tool.poetry.version
        self.description = config.api.doc.description
        self.contacts = config.api.doc.contact.as_dict()
        self.license = config.api.doc.contact.license.as_dict()

        self.algorithm = config.encryption.algorithm
        self.secret_key = config.encryption.secret_key
        self.token_expire_min = config.encryption.token_expire_min
        self.refresh_token_expire_min = config.encryption.refresh_token_expire_min
        self.grant_type = config.encryption.grant_type
        return self

    def from_env_file(self) -> Self:
        print("Injecting enviroment variables")
        self.db_url = str(getenv("DB_URL"))
        self.token_expire_min = int(
            getenv("API_JWT_TOKEN_EXPIRE_MINUTES", self.token_expire_min)
        )
        self.origins = json.loads(getenv("API_CORS_ORIGINS", '["*"]'))
        self.client_url = str(getenv("CLIENT_URL", self.client_url))
        self.refresh_token_expire_min = int(
            getenv(
                "API_JWT_REFRESH_TOKEN_EXPIRE_MINUTES", self.refresh_token_expire_min
            )
        )
        return self

    def pretty_print(self):
        pprint(vars(self))
