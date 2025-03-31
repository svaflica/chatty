import pytest
import pytest_asyncio
import os
from dotenv import load_dotenv
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

import auth
from auth_client import get_auth_client
from minio_client import MinioClient, get_minio_client
from models import Base
from database import get_db
from auth.main import app as auth_app
from post.main import app as post_app
from httpx import ASGITransport, AsyncClient

# TEST_DATABASE_URL = "postgresql+asyncpg://test-user:password@localhost:5434/test_db"


@pytest.fixture(scope="session")
def test_db_url():
    """Собирает URL тестовой базы данных из .env.local."""
    load_dotenv(".env.test")
    db_user = os.getenv("DB_USER")
    db_password = os.getenv("DB_PASSWORD")
    db_host = os.getenv("DB_HOST")
    db_port = os.getenv("DB_PORT")
    db_name = os.getenv("DB_NAME")

    if not all([db_user, db_password, db_host, db_port, db_name]):
        raise ValueError(
            "Не все необходимые переменные окружения для тестовой БД заданы в .env.local"
        )

    db_url = (
        f"postgresql+asyncpg://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}"
    )
    return db_url

@pytest_asyncio.fixture
async def test_db(test_db_url):
    engine = create_async_engine(test_db_url, echo=True)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    AsyncTestingSessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with AsyncTestingSessionLocal() as session:
        yield session

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest.fixture(scope="session")
def test_minio_values():
    """Собирает URL тестовой базы данных из .env.local."""
    load_dotenv(".env.test")
    bucket = os.getenv("FILE_BUCKET_NAME")
    access_key = os.getenv("AWS_ACCESS_KEY")
    secret_access_key = os.getenv("AWS_SECRET_KEY")
    minio_url = os.getenv("MINIO_URL")

    if not all([bucket, access_key, secret_access_key, minio_url]):
        raise ValueError(
            "Не все необходимые переменные окружения для тестовой БД заданы в .env.local"
        )
    return minio_url, access_key, secret_access_key, bucket


@pytest_asyncio.fixture
async def test_minio(test_minio_values):
    minio_client = MinioClient(
        *test_minio_values
    )
    yield minio_client


@pytest_asyncio.fixture
async def auth_client(test_db, test_minio):
    # Переопределяем зависимость get_db
    def override_get_db():
        yield test_db

    def override_get_minio_client():
        yield test_minio

    auth_app.dependency_overrides[get_db] = override_get_db
    auth_app.dependency_overrides[get_minio_client] = override_get_minio_client

    # Используем AsyncClient
    async with AsyncClient(transport=ASGITransport(app=auth_app), base_url="http://auth:8000") as client:
        yield client


@pytest_asyncio.fixture
async def post_client(test_db):
    # Переопределяем зависимость get_db
    def override_get_db():
        yield test_db

    def override_get_minio_client():
        yield test_minio

    class MockAuthClient:
        def validate_token(self, token):
            return None

    def override_get_auth_client():
        yield MockAuthClient()

    post_app.dependency_overrides[get_db] = override_get_db
    post_app.dependency_overrides[get_minio_client] = override_get_minio_client
    post_app.dependency_overrides[get_auth_client] = override_get_auth_client

    # Используем AsyncClient
    async with AsyncClient(transport=ASGITransport(app=post_app), base_url="http://post:8000") as client:
        yield client
