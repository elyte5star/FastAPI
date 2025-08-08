from pathlib import Path
from dotenv import load_dotenv
import logging
from pydantic import (
    AnyHttpUrl,
    DirectoryPath,
    SecretStr,
    EmailStr,
    Field,
    AliasChoices,
    HttpUrl,
    BaseModel,
)
from datetime import datetime
from pydantic_settings import (
    BaseSettings,
    PydanticBaseSettingsSource,
    PyprojectTomlConfigSettingsSource,
    SettingsConfigDict,
)


load_dotenv()

toml_path = Path(__file__).parent.parent.parent.resolve() / "pyproject.toml"

email_template_path: Path = Path(__file__).parent.parent.resolve() / "templates"


class ApiContact(BaseModel):
    email: EmailStr | str = ""
    name: str = ""
    url: str | HttpUrl = ""
    username: str = ""
    telephone: str = ""


class ApiDoc(BaseModel):
    description: str = ""
    name: str = ""
    terms_of_service: str | HttpUrl = ""
    version: str = ""


class ApiLicense(BaseModel):
    name: str = ""
    url: str | HttpUrl = ""


class DbParams(BaseModel):
    db: str = ""
    host: str = ""
    port: int = 0
    pwd: str = ""
    user: str = ""


class AmqpParams(BaseModel):
    host_name: str = ""
    port: str = ""
    pwd: str = ""
    user: str = ""
    exchange_name: str = ""
    exchange_type: str = ""


class Settings(BaseSettings):

    # PROJECT DETAILS
    api_contact: ApiContact
    api_doc: ApiDoc
    api_license: ApiLicense

    # API
    debug: bool = False
    auth_methods: list[str] = []
    host_url: str = ""
    log_level: int | str = logging.NOTSET
    log_file_path: DirectoryPath | str = ""
    host_url: str = ""
    max_login_attempt: int = 0
    lock_duration: int = 0
    cor_origins: list[str | AnyHttpUrl] = Field(
        default=["http://localhost:8000"],
        validation_alias="cors_origins",
    )
    roles: list[str] = ["ADMIN", "USER"]
    pwd_length: int = 0
    rounds: int = 0
    encoding: str = ""
    enabled_geoip: bool = False
    otp_expiry: int = 0
    failed_login_attempt_count: int = 0
    blocked_ips: dict[str, datetime] = {}
    algorithm: str = Field(
        default="HS256",
        validation_alias="api_algorithm",
    )
    secret_key: str = Field(
        default="",
        validation_alias="api_secret",
    )
    refresh_token_expire_min: int = Field(
        default=0,
        validation_alias="jwt_refresh_token_expire_minutes",
    )
    token_expire_min: int = Field(
        default=0,
        validation_alias="jwt_expire_minutes",
    )

    # CLIENT
    client_url: str = ""
    logger: logging.Logger = logging.getLogger(__name__)
    password: str | SecretStr = ""

    # Google AUTH
    google_client_id: str = ""
    google_client_secret: str = ""
    google_issuer: str = ""
    google_auth_url: str = ""
    google_token_url: str = ""
    google_token_info_url: str = ""
    google_scopes: dict = {}

    # MSOFT AUTH
    msal_tenant_id: str = ""
    msal_client_id: str = ""
    msal_client_secret: str = ""
    msal_scope_name: str = ""
    msal_scope_desc: str = ""
    msal_scopes: dict = {}
    msal_jwks_url: str = ""
    msal_auth_url: str = ""
    msal_token_url: str = ""
    msal_issuer: str = ""

    # EMAIL CONFIG
    mail_from: EmailStr | str = ""
    mail_username: str = ""
    mail_password: SecretStr | str = ""
    mail_port: int = 0
    mail_server: str = ""
    mail_from_name: str | None = None
    mail_starttls: bool = True
    mail_ssl_tls: bool = False
    use_credentials: bool = False
    validate_certs: bool = False
    template_folder: DirectoryPath | None = email_template_path

    # RabbitMQ
    amqp_params: AmqpParams

    amqp_url: str = Field(
        default="amqp://rabbitUser:elyteRQ@localhost:5672/",
        validation_alias=AliasChoices("RQ_URL", "amqp_url"),
    )
    queue_names: list[str] = []

    # Database
    db_params: DbParams
    db_url: str = Field(
        default="postgresql+asyncpg://userExample:54321@localhost:5432/elyte",
        validation_alias=AliasChoices("db_url", "postgres_url"),
    )

    # Visa Payment API
    # visa_params: dict = {}

    @classmethod
    def settings_customise_sources(
        cls,
        settings_cls: type[BaseSettings],
        init_settings: PydanticBaseSettingsSource,
        env_settings: PydanticBaseSettingsSource,
        dotenv_settings: PydanticBaseSettingsSource,
        file_secret_settings: PydanticBaseSettingsSource,
    ) -> tuple[PydanticBaseSettingsSource, ...]:
        return (
            # env_settings,
            PyprojectTomlConfigSettingsSource(settings_cls, toml_path),
            init_settings,
        )

    model_config = SettingsConfigDict(
        extra="ignore",
        pyproject_toml_table_header=(),
        env_ignore_empty=True,
        env_file_encoding="utf-8",
        env_nested_delimiter="_",
        env_file=".env",
    )


aux = Settings()

print(aux.model_dump())
