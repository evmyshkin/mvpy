"""Конфигурация приложения c Pydantic Settings.

Задает конфиги по-умолчанию, если они не заданы в .env или не переданы аргументами при
инициализации
"""

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
    test_api_base_url: str = 'http://test'


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

    @model_validator(mode='after')
    def build_database_uri(self) -> 'PostgresConfig':
        """Собираем PG-URI из компонентов."""
        if not self.database_uri:
            sqlalchemy_db_uri = URL.create(
                drivername='postgresql+asyncpg',
                username=self.user,
                password=self.password,
                host=self.host,
                port=self.port,
                database=self.db,
            )
            self.database_uri = str(sqlalchemy_db_uri)
            self.test_database_uri = str(sqlalchemy_db_uri)
        return self


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
