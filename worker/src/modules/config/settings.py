from pydantic import Field
from typing import Literal
from pydantic_settings import (
    BaseSettings,
    SettingsConfigDict,
    PydanticBaseSettingsSource,
)
from dotenv import load_dotenv
from pydantic import AliasChoices


load_dotenv()


class AppConfig(BaseSettings):

    # Database settings
    database_url: str = Field(
        default="postgresql+psycopg2://userExample:54321@db:5432/elyte",
        validation_alias=AliasChoices("DB_URL", "postgres_url"),
    )
    amqp_url: str = Field(
        default="amqp://rabbitUser:elyteRQ@localhost:5672/",
        validation_alias=AliasChoices("RQ_URL", "amqp_url"),
    )

    queue_name: Literal["SEARCH", "BOOKING", "LOST_ITEM"] = "SEARCH"

    amqp_routing_key: str = ""

    exchange_name: str = ""

    worker_type: str = ""

    @classmethod
    def settings_customise_sources(
        cls,
        settings_cls: type[BaseSettings],
        init_settings: PydanticBaseSettingsSource,
        env_settings: PydanticBaseSettingsSource,
        dotenv_settings: PydanticBaseSettingsSource,
        file_secret_settings: PydanticBaseSettingsSource,
    ) -> tuple[PydanticBaseSettingsSource, ...]:
        return env_settings, init_settings, file_secret_settings

    model_config = SettingsConfigDict(
        env_ignore_empty=True,
        env_file_encoding="utf-8",
        env_file=".env",
    )
