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

    # Шифрование пароля
    SECRET_KEY: str = ''
    ALGORITHM: str = 'HS256'
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    # Минио
    AWS_ACCESS_KEY: str = 'aaaa'
    AWS_SECRET_KEY: str = 'bbbb'
    FILE_BUCKET_NAME: str = 'bucket'


settings = Settings()

if __name__ == '__main__':
    print(settings.model_dump())
    print(settings.database_url)
    print(settings.async_database_url)
