import datetime
from typing import Annotated
import jwt

from fastapi import Depends, HTTPException, status, FastAPI
from fastapi.security import HTTPBasic
from starlette_exporter import PrometheusMiddleware, handle_metrics
from fastapi.security import OAuth2PasswordBearer
from jwt.exceptions import InvalidTokenError
from passlib.context import CryptContext
from passlib.hash import bcrypt
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

import models

from database import get_db
from auth.schemas import (
    User,
    Token,
    TokenData,
    GetUserResult,
    LoginUser, UserChangePassword,
)
from config import settings
from minio_client import get_minio_client, MinioClient


pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")
security = HTTPBasic()

app = FastAPI()

app.add_middleware(PrometheusMiddleware, prefix='chatty')
app.add_route("/metrics", handle_metrics)


def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password):
    return pwd_context.hash(password)


async def get_user(db, email: str, password):
    result = await db.execute(select(models.User).where(
        models.User.email == email and models.User.password == password
    ))
    items = result.scalars().all()
    if not items:
        raise HTTPException(status_code=404, detail="User not found")
    return items[0]


async def get_user_by_email(db, email: str):
    result = await db.execute(select(models.User).where(
        models.User.email == email
    ))
    items = result.scalars().all()
    if not items:
        raise HTTPException(status_code=404, detail="User not found")
    return items[0]


async def authenticate_user(db, email: str, password: str):
    user = await get_user_by_email(db, email)
    if not user:
        return False
    if not verify_password(password, user.password):
        return False
    return user


def create_access_token(data: dict, expires_delta: datetime.timedelta | None = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.datetime.now(datetime.timezone.utc) + expires_delta
    else:
        expire = datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt


async def get_current_user(
    token: Annotated[str, Depends(oauth2_scheme)],
    db: AsyncSession = Depends(get_db),
):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        email = payload.get("sub")
        password = payload.get("passwd")
        if email is None:
            raise credentials_exception
        token_data = TokenData(email=email)
    except InvalidTokenError:
        raise credentials_exception

    user = await get_user(db, email=token_data.email, password=password)
    if user is None:
        raise credentials_exception
    return user


async def get_current_active_user(
    current_user: Annotated[User, Depends(get_current_user)],
    minio_client = Depends(get_minio_client),
):
    if current_user is None:
        raise HTTPException(status_code=400, detail="Inactive user")

    photo: bytes = minio_client.get_object(current_user.photo)
    return GetUserResult(email=current_user.email, photo=photo)


async def register_user(
    db: AsyncSession,
    user: User,
    minio_client: MinioClient,
):
    filename = None
    if user.photo is not None:
        filename = minio_client.put_object(user.photo)

    db_item = models.User(
        email = user.email,
        password = get_password_hash(user.password),
        photo = filename,
    )
    db.add(db_item)
    await db.commit()
    await db.refresh(db_item)
    return db_item


async def new_password_user(
    db: AsyncSession,
    user: UserChangePassword,
):
    db_item = await get_user(db, user.email, user.password)

    if db_item is None:
        raise HTTPException(status_code=400, detail="Inactive user")

    db_item.password = get_password_hash(user.password)
    db.add(db_item)
    await db.commit()
    await db.refresh(db_item)


@app.post('/register')
async def register(
    form_data: User,
    db: AsyncSession = Depends(get_db),
    minio_client = Depends(get_minio_client),
):
    user = await register_user(db, form_data, minio_client)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token_expires = datetime.timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.email, "passwd": user.password}, expires_delta=access_token_expires
    )
    return Token(access_token=access_token, token_type="bearer")


@app.post("/login")
async def login_for_access_token(
    form_data: LoginUser,
    db: AsyncSession = Depends(get_db),
) -> Token:
    user = await authenticate_user(db, form_data.email, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = datetime.timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.email, "passw": user.password}, expires_delta=access_token_expires
    )
    return Token(access_token=access_token, token_type="bearer")


@app.get("/users/me/", response_model=GetUserResult)
async def read_users_me(
    current_user: Annotated[User, Depends(get_current_active_user)],
):
    return current_user


@app.get("/check_token")
async def check_token(
    token: Annotated[str, Depends(oauth2_scheme)],
    db: AsyncSession = Depends(get_db),
):
    await get_current_user(token, db)
    return {"status": "ok"}


@app.post("/new_password")
async def new_password(
    form_data: UserChangePassword,
    db: AsyncSession = Depends(get_db),
):
    await new_password_user(db, form_data)
    return {"status": "ok"}
