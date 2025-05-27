from pathlib import Path
from os import getenv, path
from pyconfs import Configuration
import json
from pprint import pprint
from dotenv import load_dotenv
import logging
from typing import Any, Dict, Self
from fastapi_mail import ConnectionConfig

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
        self.debug: int = 0
        self.auth_type: str = ""
        self.origins: list[str] = ["*"]
        self.roles: list[str] = [""]
        self.pwd_len: int = 0
        self.encoding: str = ""
        self.sql_url: str = ""
        self.logger: logging.Logger = None
        self.queries: Dict[Any, Any] = None
        self.max_login_attempt: int = 0
        self.lock_duration: int = 0
        self.is_geo_ip_enabled: bool = False
        self.otp_expiry: int = 0

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
        self.rounds: int = 0
        self.token_expire_min: int = 0
        self.refresh_token_expire_min: int = 0
        self.token_url: str = ""
        self.grant_type: str = ""

        # MSOFT AUTH
        self.msal_login_authority: str = ""
        self.msal_client_id: str = ""
        self.msal_issuer: str = ""

        # EMAIL CONFIG
        self.email: str = ""
        self.mail_username: str = ""
        self.mail_password: str = ""
        self.mail_port: int = 0
        self.mail_server: str = ""
        self.mail_from_name: str = ""
        self.mail_starttls: bool = False
        self.mail_ssl_tls: bool = False
        self.use_credentials: bool = False
        self.validate_certs: bool = False
        self.email_config: ConnectionConfig = None

        # RabbitMQ
        self.rabbit_host_name: str = ""
        self.rabbit_host_port: str = ""
        self.rabbit_connect_string: str = ""
        self.queue_name: list = []
        self.rabbit_user: str = ""
        self.rabbit_pass: str = ""
        self.rabbit_connect_string: str = ""

        # Visa Payment API
        self.visa_userid: str = ""
        self.visa_password: str = ""
        self.visa_cert: str = ""
        self.visa_key: str = ""
        self.visa_url: str = ""
        self.visa_shared_secret: str = ""

        # CLIENT
        self.client_url: str = ""

    def from_toml_file(self) -> Self:
        self.sql_username = config.database.user
        self.sql_password = config.database.pwd
        self.sql_host = config.database.host
        self.sql_port = config.database.port
        self.sql_db = config.database.db
        self.db_url = f"postgresql+asyncpg://{self.sql_username}:{self.sql_password}@{self.sql_host}:{self.sql_port}/{self.sql_db}"
        self.log_level = config.api.log_level
        self.log_file_path = config.api.log_file_path
        self.host_url = config.api.host_url
        self.debug = config.api.debug
        self.auth_type = config.api.auth_type
        self.max_login_attempt = config.api.login_attempts
        self.lock_duration = config.api.lock_duration
        self.is_geo_ip_enabled = config.api.enabled_geoip
        self.otp_expiry = config.api.otp_expiry

        self.pwd_len = config.encryption.length
        self.rounds = config.encryption.rounds
        self.encoding = config.encryption.encoding
        self.roles = config.encryption.roles

        self.rabbit_host_name = config.queue.params.host_name
        self.rabbit_host_port = config.queue.params.port
        self.rabbit_user = config.queue.params.user
        self.rabbit_pass = config.queue.params.pwd
        self.queue_name = config.queue.params.my_queue
        self.rabbit_connect_string = (
            f"amqp://{self.rabbit_user}:{self.rabbit_pass}@"
            + self.rabbit_host_name
            + ":"
            + self.rabbit_host_port
            + "/"
        )

        self.mail_username = config.api.doc.contact["mail_username"]
        self.mail_port = config.api.doc.contact["mail_port"]
        self.mail_server = config.api.doc.contact["mail_server"]
        self.mail_from_name = config.api.doc.contact["mail_from_name"]
        self.mail_starttls = config.api.doc.contact["mail_starttls"]
        self.mail_ssl_tls = config.api.doc.contact["mail_ssl_tls"]
        self.use_credentials = config.api.doc.contact["use_credentials"]
        self.validate_certs = config.api.doc.contact["validate_certs"]
        self.email = config.api.doc.contact["email"]

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

        # Visa Payment API
        self.visa_userid = config.VDP.userId
        self.visa_password = config.VDP.password
        self.visa_cert = config.VDP.cert
        self.visa_key = config.VDP.key
        self.visa_url = config.VDP.visaUrl
        self.visa_shared_secret = config.VDP.sharedSecret

        return self

    def from_env_file(self) -> Self:
        self.db_url = str(getenv("DB_URL"))
        self.token_expire_min = int(
            getenv("API_JWT_TOKEN_EXPIRE_MINUTES", self.token_expire_min)
        )
        self.mail_password = str(getenv("MAIL_PASSWORD"))
        self.email_config = ConnectionConfig(
            MAIL_USERNAME=self.mail_username,
            MAIL_PASSWORD=self.mail_password,
            MAIL_FROM=self.email,
            MAIL_PORT=self.mail_port,
            MAIL_SERVER=self.mail_server,
            MAIL_STARTTLS=self.mail_starttls,
            MAIL_SSL_TLS=self.mail_ssl_tls,
            MAIL_DEBUG=self.debug,
            MAIL_FROM_NAME="Elyte Application",
            TEMPLATE_FOLDER=Path(__file__).parent.parent / "templates",
        )
        if self.log_file_path == "":
            self.log_file_path = str(getenv("LOG_PATH"))
        self.origins = json.loads(getenv("API_CORS_ORIGINS", '["*"]'))
        self.client_url = str(getenv("CLIENT_URL", self.client_url))
        self.log_level = getenv("LOG_LEVEL", self.log_level)
        self.refresh_token_expire_min = int(
            getenv(
                "API_JWT_REFRESH_TOKEN_EXPIRE_MINUTES",
                self.refresh_token_expire_min,
            )
        )
        return self

    def pretty_print(self):
        pprint(vars(self))
