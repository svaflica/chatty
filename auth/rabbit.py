import datetime

from fastapi import Depends, HTTPException, status, FastAPI
from faststream.rabbit.fastapi import RabbitRouter
from typing import Annotated
from sqlalchemy.ext.asyncio import AsyncSession

from auth.schemas import (
    Token,
    UserRabbit,
    LoginUserRabbit,
    CheckTokenRabbit,
    UserChangePasswordRabbit, User,
)
from auth.utils import (
    register_user,
    create_access_token,
    authenticate_user,
    get_current_active_user,
    oauth2_scheme,
    get_current_user,
    new_password_user,
)
from config import settings
from database import get_db
from minio_client import get_minio_client


broker = RabbitRouter(settings.async_rm_url)


@broker.subscriber('event-auth', filter=lambda m: 'register' in m.message_id)
async def register_rabbit(
    form_data: UserRabbit,
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
    await broker.broker.publish(
        message=Token(access_token=access_token, token_type="bearer"),
        queue='event-auth-result',
        message_id=form_data.message_id,
    )


@broker.subscriber('event-auth', filter=lambda m: 'login' in m.message_id)
async def login_for_access_token_rabbit(
    form_data: LoginUserRabbit,
    db: AsyncSession = Depends(get_db),
):
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
    await broker.broker.publish(
        message=Token(access_token=access_token, token_type="bearer"),
        queue='event-auth-result',
        message_id=form_data.message_id,
    )


@broker.subscriber('event-auth', filter=lambda m: 'get-user' in m.message_id)
async def read_users_me_rabbit(
    current_user: Annotated[User, Depends(get_current_active_user)],
    user: UserRabbit
):
    await broker.broker.publish(
        message=current_user,
        queue='event-auth-result',
        message_id=user.message_id,
    )


@broker.subscriber('event-auth', filter=lambda m: 'check-token' in m.message_id)
async def check_token_rabbit(
    msg: CheckTokenRabbit,
    token: Annotated[str, Depends(oauth2_scheme)],
    db: AsyncSession = Depends(get_db),
):
    await get_current_user(token, db)

    result_queue = 'event-auth-result'
    if 'post' in msg.message_id:
        result_queue += '-post'
    elif 'subscr' in msg.message_id:
        result_queue += '-subscr'

    await broker.broker.publish(
        message={"status": "ok", "message_id": msg.message_id},
        queue=result_queue,
        message_id=msg.message_id,
    )


@broker.subscriber('event-auth', filter=lambda m: 'check-admin-token' in m.message_id)
async def check_admin_token_rabbit(
    msg: CheckTokenRabbit,
    token: Annotated[str, Depends(oauth2_scheme)],
    db: AsyncSession = Depends(get_db),
):
    user = await get_current_user(token, db)

    result_queue = 'event-auth-result'
    if 'post' in msg.message_id:
        result_queue += '-post'
    elif 'subscr' in msg.message_id:
        result_queue += '-subscr'
    elif 'admin' in msg.message_id:
        result_queue += '-admin'

    if user.is_admin:
        await broker.broker.publish(
            message={"status": "ok", "message_id": msg.message_id},
            queue=result_queue,
            message_id=msg.message_id,
        )
    else:
        await broker.broker.publish(
            message={"status": "error", "message_id": msg.message_id},
            queue=result_queue,
            message_id=msg.message_id,
        )
