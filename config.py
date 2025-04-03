import logging
import json
import datetime

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file='.env', extra='ignore', case_sensitive=False
    )

    # PostgreSQL database settings
    db_host: str = 'localhost'
    db_port: int = 5432
    db_name: str = 'db'
    db_user: str = 'postgres'
    db_password: str | None = None  # Password can be optional

    # Other settings (optional)
    debug: bool = False

    @property
    def database_url(self) -> str:
        """Construct the async database URL."""
        if self.db_password:
            return (
                f'postgresql://{self.db_user}:{self.db_password}@{self.db_host}:'
                f'{self.db_port}/{self.db_name}'
            )
        else:
            return (
                f'postgresql://{self.db_user}@{self.db_host}:{self.db_port}/{self.db_name}'
            )

    @property
    def async_database_url(self) -> str:
        """Construct the async database URL for asyncpg."""
        return self.database_url.replace("postgresql://", "postgresql+asyncpg://")

    # PostgreSQL database settings
    RABBIT_HOST: str = 'rabbitmq'
    RABBIT_PORT: int = 5672
    RABBIT_PROTOCOL: str = 'amqp'
    RABBIT_USER: str = 'rmuser'
    RABBIT_PASSWORD: str | None = None  # Password can be optional

    @property
    def async_rm_url(self) -> str:
        """Construct the async database URL for asyncpg."""
        return f'{self.RABBIT_PROTOCOL}://{self.RABBIT_USER}:{self.RABBIT_PASSWORD}@{self.RABBIT_HOST}:{self.RABBIT_PORT}'

    # Шифрование пароля
    SECRET_KEY: str = ''
    ALGORITHM: str = 'HS256'
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    # Минио
    MINIO_URL: str = 'minio:9000'
    AWS_ACCESS_KEY: str = 'minioadmin'
    AWS_SECRET_KEY: str = 'minioadmin'
    FILE_BUCKET_NAME: str = 'bucket'

    AUTH_CLIENT_URL: str = ''
    POST_CLIENT_URL: str = ''


class FormatterLogger(logging.Formatter):
    def format(self, record: logging.LogRecord):
        _default_record_fields = dir(
            logging.LogRecord(
                '',
                0,
                '',
                0,
                None,
                None,
                None)
        ) + ['__slotnames__']
        extra = {x: record.__dict__[x] for x in dir(record) if x not in _default_record_fields}

        rv = {
            'msg': record.getMessage(),
            'time': datetime.datetime.now(datetime.timezone.utc).isoformat(),
            'logger_name': record.name,
            'level': record.levelname,
        }

        if record.exc_info:
            rv['exc_info'] = self.formatException(record.exc_info)

        if "message" in extra and "arguments" in extra:
            rv["msg"] = extra["message"].format(extra["arguments"])
            del extra["message"]
            del extra["arguments"]

        return json.dumps(dict(**rv, **extra), ensure_ascii=False, default=repr)


settings = Settings()


# Set up logger
stream_handler = logging.StreamHandler()
stream_handler.setFormatter(FormatterLogger())

jrpc_logger = logging.getLogger("fastapi")
# Turn off default log formatter
jrpc_logger.propagate = False
jrpc_logger.addHandler(stream_handler)

logger = logging.getLogger("uvicorn")
if len(logger.handlers) > 0:
    logger.removeHandler(logger.handlers[0])
logger.propagate = False
logger.addHandler(stream_handler)

logger = logging.getLogger("uvicorn.access")
if len(logger.handlers) > 0:
    logger.removeHandler(logger.handlers[0])
logger.propagate = False
logger.addHandler(stream_handler)

logger = logging.getLogger("uvicorn.error")
logger.propagate = False
logger.addHandler(stream_handler)

logger = logging.getLogger("uvicorn.asgi")
logger.propagate = False
logger.addHandler(stream_handler)

# ...for our logger
logger = logging.getLogger("logger_app")
logger.setLevel(logging.INFO)
# Turn off default log formatter
logger.propagate = False
logger.addHandler(stream_handler)


if __name__ == '__main__':
    print(settings.model_dump())
    print(settings.database_url)
    print(settings.async_database_url)
