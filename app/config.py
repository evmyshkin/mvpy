"""Конфигурация приложения c Pydantic Settings.

Задает конфиги по-умолчанию, если они не заданы в .env или не переданы аргументами при
инициализации
"""

from pydantic import BaseModel
from pydantic import Field
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


class JWTConfig(BaseModel):
    """Конфигурация JWT токенов."""

    secret_key: str = Field(
        default='default-secret-key-for-development-min-32-characters',
        description='Секретный ключ для подписи JWT токенов',
        min_length=32,
    )
    access_token_expire_minutes: int = Field(
        default=60,
        description='Время жизни токена в минутах',
        ge=1,  # Минимум 1 минута
        le=43200,  # Максимум 30 дней
    )
    algorithm: str = Field(
        default='HS256',
        description='Алгоритм подписи JWT',
    )


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
    jwt: JWTConfig = JWTConfig()


config = Settings()
