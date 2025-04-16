import datetime
import logging

from fastapi import Depends, HTTPException, status, FastAPI
from starlette_exporter import PrometheusMiddleware, handle_metrics
from sqlalchemy.ext.asyncio import AsyncSession
from faststream.rabbit import (
    ExchangeType,
    RabbitBroker,
    RabbitExchange,
    RabbitQueue,
)
from typing import Annotated

from database import get_db
from auth.schemas import (
    User,
    Token,
    GetUserResult,
    LoginUser,
    UserChangePassword,
)
from config import settings
from minio_client import get_minio_client
from auth.utils import (
    register_user,
    create_access_token,
    authenticate_user,
    get_current_active_user,
    oauth2_scheme,
    get_current_user,
    new_password_user,
)
from auth.rabbit import broker

logger = logging.getLogger('logger_app')

app = FastAPI()

app.add_middleware(PrometheusMiddleware, prefix='chatty')
app.add_route("/metrics", handle_metrics)


@app.post('/register')
async def register(
    form_data: User,
    db: AsyncSession = Depends(get_db),
    minio_client = Depends(get_minio_client),
):
    logger.info('Register started')
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
    logger.info('Register ended')
    return Token(access_token=access_token, token_type="bearer")


@app.post("/login")
async def login_for_access_token(
    form_data: LoginUser,
    db: AsyncSession = Depends(get_db),
) -> Token:
    logger.info('Login started')
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
    logger.info('Login ended')
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
    logger.info('Check token started')
    await get_current_user(token, db)
    logger.info('Check token ended')
    return {"status": "ok"}


@app.get("/check_token_admin")
async def check_token_admin(
    token: Annotated[str, Depends(oauth2_scheme)],
    db: AsyncSession = Depends(get_db),
):
    logger.info('Check admin token started')
    user = await get_current_user(token, db)
    if user.is_admin:
        logger.info('Check admin token ended')
        return {"status": "ok"}
    else:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User is not admin",
            headers={"WWW-Authenticate": "Bearer"},
        )


@app.post("/new_password")
async def new_password(
    form_data: UserChangePassword,
    db: AsyncSession = Depends(get_db),
):
    logger.info('Changing password started')
    await new_password_user(db, form_data)
    logger.info('Changing password ended')
    return {"status": "ok"}


@broker.after_startup
async def startup(app: FastAPI):
    await broker.broker.declare_queue(
        RabbitQueue(
            name="event-auth-result",
            durable=False,
        )
    )


app.include_router(broker)
