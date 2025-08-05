from pathlib import Path
from dotenv import load_dotenv
import logging
from pydantic import AnyHttpUrl
from fastapi_mail import ConnectionConfig
from datetime import datetime
from pydantic_settings import (
    BaseSettings,
    PydanticBaseSettingsSource,
    PyprojectTomlConfigSettingsSource,
    SettingsConfigDict,
)

load_dotenv()

toml_path = Path(__file__).parent.parent.parent.resolve() / "pyprojecttoml"


class Settings(BaseSettings):

    # API
    log_level: int | str = logging.NOTSET
    log_file_path: str = ""
    host_url: str = ""
    debug: bool = False
    auth_methods: list = []
    origins: list[str | AnyHttpUrl] = ["http://localhost:8000"]
    roles: list[str] = [""]
    pwd_len: int = 0
    encoding: str = ""
    db_url: str = ""
    logger: logging.Logger = logging.getLogger(__name__)
    max_login_attempt: int = 0
    failed_login_attempt_count: int = 0
    lock_duration: int = 0
    blocked_ips: dict[str, datetime] = {}
    is_geo_ip_enabled: bool = False
    otp_expiry: int = 0

    # PROJECT DETAILS
    name: str = ""
    version: str = ""
    description: str = ""
    terms: str = ""
    contacts: dict = {}
    license: dict = {}

    # JWT PARAMS
    algorithm: str = ""
    secret_key: str = ""
    rounds: int = 0
    token_expire_min: int = 0
    refresh_token_expire_min: int = 0
    grant_type: str = ""

    # Google AUTH
    google_client_id: str = ""
    google_client_secret: str = ""

    # MSOFT AUTH
    msal_tenant_id: str = ""
    msal_client_id: str = ""
    msal_client_secret: str = ""
    msal_scope_name: str = ""
    msal_scope_desc: str = "user_impersonation"
    msal_scopes: dict = {}
    msal_jwks_url: str = ""
    msal_auth_url: str = ""
    msal_token_url: str = ""
    msal_issuer: str = ""

    # EMAIL CONFIG
    email: str = ""
    mail_username: str = ""
    mail_password: str = ""
    mail_port: int = 0
    mail_server: str = ""
    mail_from_name: str = ""
    mail_starttls: bool = False
    mail_ssl_tls: bool = False
    use_credentials: bool = False
    validate_certs: bool = False
    email_config: ConnectionConfig = {}

    # RabbitMQ
    rabbit_host_name: str = ""
    rabbit_host_port: str = ""
    rabbit_connect_string: str = ""
    queue_name: list = []
    rabbit_user: str = ""
    rabbit_pass: str = ""
    rabbit_connect_string: str = ""

    # Visa Payment API
    visa_params: dict = {}

    # CLIENT
    client_url: str = ""

    @classmethod
    def settings_customise_sources(
        cls,
        settings_cls: type[BaseSettings],
        init_settings: PydanticBaseSettingsSource,
        env_settings: PydanticBaseSettingsSource,
        dotenv_settings: PydanticBaseSettingsSource,
        file_secret_settings: PydanticBaseSettingsSource,
    ) -> tuple[PydanticBaseSettingsSource,]:
        return (
            env_settings,
            init_settings,
            PyprojectTomlConfigSettingsSource(settings_cls, toml_path),
        )

    model_config = SettingsConfigDict(
        env_ignore_empty=True,
        env_file_encoding="utf-8",
        env_file="env",
        pyproject_toml_table_header=(),
    )


aux = Settings()

print(aux.log_level)
