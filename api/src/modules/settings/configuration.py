from pathlib import Path
from os import getenv, path
from pyconfs import Configuration
import json
from pprint import pprint
from dotenv import load_dotenv
import logging
from typing import Self
from fastapi_mail import ConnectionConfig
from pydantic import SecretStr, AnyHttpUrl


load_dotenv()


project_root = Path(__file__).parent.parent.parent
toml_path = path.join(project_root, "pyproject.toml")
config = Configuration.from_file(toml_path)


class ApiConfig:

    def __init__(self) -> None:
        # API
        self.log_level: logging._Level = logging.NOTSET
        self.log_file_path: str = ""
        self.host_url: str = ""
        self.debug: bool = False
        self.auth_types: str = ""
        self.origins: list[str | AnyHttpUrl] = ["http://localhost:8000"]
        self.roles: list[str] = [""]
        self.pwd_len: int = 0
        self.encoding: str = ""
        self.db_url: str = ""
        self.logger: logging.Logger = logging.getLogger(__name__)
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
        self.grant_type: str = ""

        # Google AUTH
        self.google_client_id: str = ""
        self.google_jwks_url: str = ""

        # MSOFT AUTH
        self.msal_tenant_id: str = ""
        self.msal_client_id: str = ""
        self.msal_client_secret: str = ""
        self.msal_scope_name: str = ""
        self.msal_scope_desc: str = "user_impersonation"
        self.msal_scopes: dict = {}
        self.msal_jwks_url: str = ""
        self.msal_auth_url: str = ""
        self.msal_token_url: str = ""
        # A cache for Microsoft keys
        self.public_keys: list = []

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
        self.email_config: ConnectionConfig

        # RabbitMQ
        self.rabbit_host_name: str = ""
        self.rabbit_host_port: str = ""
        self.rabbit_connect_string: str = ""
        self.queue_name: list = []
        self.rabbit_user: str = ""
        self.rabbit_pass: str = ""
        self.rabbit_connect_string: str = ""

        # Visa Payment API
        self.visa_params: dict = {}

        # CLIENT
        self.client_url: str = ""

    def from_toml_file(self) -> Self:
        self.sql_username = config.database.user
        self.sql_password = config.database.pwd
        self.sql_host = config.database.host
        self.sql_port = config.database.port
        self.sql_db = config.database.db
        self.db_url = f"""postgresql+asyncpg://{self.sql_username}:
        {self.sql_password}@{self.sql_host}:{self.sql_port}/{self.sql_db}
        """
        self.log_level = getattr(logging, config.api["log_level"])
        self.log_file_path = config.api["log_file_path"]
        self.host_url = config.api["host_url"]
        self.debug = config.api["debug"]
        self.auth_types = config.api["auth_types"]
        self.max_login_attempt = config.api["login_attempts"]
        self.lock_duration = config.api["lock_duration"]
        self.is_geo_ip_enabled = config.api["enabled_geoip"]
        self.otp_expiry = config.api["otp_expiry"]

        self.pwd_len = config.encryption["length"]
        self.rounds = config.encryption["rounds"]
        self.encoding = config.encryption["encoding"]
        self.roles = config.encryption["roles"]

        self.rabbit_host_name = config.queue.params["host_name"]
        self.rabbit_host_port = config.queue.params["port"]
        self.rabbit_user = config.queue.params["user"]
        self.rabbit_pass = config.queue.params["pwd"]
        self.queue_name = config.queue.params["my_queue"]
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
        self.terms = config.api.doc["terms_of_service"]
        self.version = config.tool.poetry["version"]
        self.description = config.api.doc["description"]
        self.contacts = config.api.doc.contact.as_dict()
        self.license = config.api.doc.contact.license.as_dict()

        self.algorithm = config.encryption["algorithm"]
        self.secret_key = config.encryption["secret_key"]
        self.token_expire_min = config.encryption["token_expire_min"]
        self.refresh_token_expire_min = config.encryption["refresh_token_expire_min"]
        self.grant_type = config.encryption["grant_type"]

        # Visa Payment API
        self.visa_params = config.visa.params.as_dict()
        return self

    def from_env_file(self) -> Self:
        self.db_url = str(getenv("DB_URL"))
        self.rabbit_connect_string = str(getenv("RQ_URL"))
        self.token_expire_min = int(
            getenv("API_JWT_EXPIRE_MINUTES", self.token_expire_min)
        )
        self.mail_password = str(getenv("MAIL_PASSWORD"))
        self.email_config = ConnectionConfig(
            MAIL_USERNAME=self.mail_username,
            MAIL_PASSWORD=SecretStr(self.mail_password),
            MAIL_FROM=self.email,
            MAIL_PORT=self.mail_port,
            MAIL_SERVER=self.mail_server,
            MAIL_STARTTLS=self.mail_starttls,
            MAIL_SSL_TLS=self.mail_ssl_tls,
            MAIL_DEBUG=0,
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
        self.msal_tenant_id = str(getenv("MICROSOFT_TENANT_ID"))
        self.msal_client_id = str(getenv("MICROSOFT_CLIENT_ID"))
        self.msal_client_secret = str(getenv("MICROSOFT_CLIENT_SECRET"))
        self.msal_scope_desc = str(getenv("MICROSOFT_SCOPE_DESC", self.msal_scope_desc))
        self.msal_scope_name = f"api://{self.msal_client_id}/{self.msal_scope_desc}"
        self.msal_scopes = {self.msal_scope_name: self.msal_scope_desc}
        self.msal_jwks_url = f"https://login.microsoftonline.com/{self.msal_tenant_id}/discovery/v2.0/keys"
        self.msal_auth_url = f"https://login.microsoftonline.com/{self.msal_tenant_id}/oauth2/v2.0/authorize"
        self.msal_token_url = (
            f"https://login.microsoftonline.com/{self.msal_tenant_id}/oauth2/v2.0/token"
        )
        self.msal_config = dict(
            MICROSOFT_TENANT_ID=self.msal_tenant_id,
            MICROSOFT_CLIENT_ID=self.msal_client_id,
            MICROSOFT_CLIENT_SECRET=self.msal_client_secret,
            MICROSOFT_SCOPES=self.msal_scopes,
            MICROSOFT_JWKS_URL=self.msal_jwks_url,
            MICROSOFT_SCOPE_NAME=self.msal_scope_name,
            MICROSOFT_SCOPE_DESC=self.msal_scope_desc,
        )
        self.google_jwks_url = "https://www.googleapis.com/oauth2/v3/certs"
        self.google_client_id = str(getenv("GOOGLE_CLIENT_ID"))
        self.google_audience = f"{self.google_client_id}.apps.googleusercontent.com"
        self.google_issuer = "https://accounts.google.com"
        self.google_config = dict(
            GOOGLE_CLIENT_ID=self.google_client_id,
            GOOGLE_JWKS_URL=self.google_jwks_url,
            GOOGLE_ISSUER=self.google_issuer,
            GOOGLE_AUDIENCE=self.google_audience,
        )
        return self

    def pretty_print(self):
        pprint(vars(self))
