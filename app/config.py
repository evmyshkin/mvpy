"""Конфигурация приложения c Pydantic Settings.

Задает конфиги по-умолчанию, если они не заданы в .env или не переданы аргументами при
инициализации
"""

from typing import Any

from pydantic import BaseModel
from pydantic import model_validator
from pydantic_settings import BaseSettings
from pydantic_settings import SettingsConfigDict
from sqlalchemy import URL


class AppConfig(BaseModel):
    name: str = 'mvpy'
    host: str = '127.0.0.1'
    port: int = 8000
    environment: str = 'LOCAL'


class PostgresConfig(BaseModel):
    user: str = ''
    password: str = ''
    host: str = ''
    port: int = 5432
    db: str = ''
    database_uri: str = ''
    test_database_uri: str = ''
    pool_size: int = 40
    overflow_pool_size: int = 40

    @model_validator(mode='before')
    @classmethod
    def database_uri_validator(cls, data: Any) -> Any:
        """Собираем PG-URI."""
        sqlalchemy_db_uri = URL.create(
            drivername='postgresql+asyncpg',
            username=data.get('user'),
            password=data.get('password'),
            host=data.get('host'),
            port=data.get('port', 5432),
            database=data.get('db', ''),
        )
        data['database_uri'] = sqlalchemy_db_uri
        return data


class ImageHubConfig(BaseModel):
    url: str = 'ghcr.io'
    repo: str = ''  # Название вашего репозитория


class Settings(BaseSettings):
    """Настройки приложения."""

    model_config = SettingsConfigDict(
        env_nested_delimiter='__',
        env_file='.env',
        env_file_encoding='UTF-8',
        arbitrary_types_allowed=True,
    )

    app: AppConfig = AppConfig()
    postgres: PostgresConfig = PostgresConfig()
    image_hub: ImageHubConfig = ImageHubConfig()


config = Settings()
