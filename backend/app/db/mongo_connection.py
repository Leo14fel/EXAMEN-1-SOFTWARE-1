"""Explicit opt-in connection for the CU-25 proof; no client at import time."""

from pydantic import Field, SecretStr, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
from pymongo import MongoClient
from pymongo.server_api import ServerApi


class MongoConnectionSettings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    mongodb_uri: SecretStr
    mongodb_database: str = Field(pattern=r"^[A-Za-z0-9_-]{1,63}$")
    mongodb_timeout_ms: int = Field(default=5000, ge=100, le=30000)

    @field_validator("mongodb_uri")
    @classmethod
    def validate_uri(cls, value: SecretStr) -> SecretStr:
        if not value.get_secret_value().startswith(("mongodb://", "mongodb+srv://")):
            raise ValueError("A MongoDB connection URI is required")
        return value


class MongoSettings(MongoConnectionSettings):
    """The destructive test workflow must stay in a dedicated probe database."""

    mongodb_database: str = Field(pattern=r"^[A-Za-z0-9_-]{1,50}_cu25_probe$")


def create_mongo_client(config: MongoConnectionSettings) -> MongoClient:
    return MongoClient(
        config.mongodb_uri.get_secret_value(),
        server_api=ServerApi("1"),
        serverSelectionTimeoutMS=config.mongodb_timeout_ms,
        connectTimeoutMS=config.mongodb_timeout_ms,
        socketTimeoutMS=config.mongodb_timeout_ms,
        timeoutMS=config.mongodb_timeout_ms * 3,
        retryWrites=True,
        w="majority",
        wTimeoutMS=config.mongodb_timeout_ms,
        readConcernLevel="majority",
        readPreference="primary",
        connect=False,
    )
