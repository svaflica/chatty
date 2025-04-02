from fastapi import Depends, HTTPException, status, FastAPI
from faststream.rabbit.fastapi import RabbitRouter

from auth.schemas import (
    Token,
    UserRabbit,
    LoginUserRabbit,
    CheckTokenRabbit,
    UserChangePasswordRabbit,
)
from auth.utils import *
from config import settings
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
    await broker.broker.publish(
        message={"status": "ok"},
        queue='event-auth-result',
        message_id=msg.message_id,
    )


@broker.subscriber('event-auth', filter=lambda m: 'new-password' in m.message_id)
async def new_password_rabbit(
    form_data: UserChangePasswordRabbit,
    db: AsyncSession = Depends(get_db),
):
    await new_password_user(db, form_data)
    await broker.broker.publish(
        message={"status": "ok"},
        queue='event-auth-result',
        message_id=form_data.message_id,
    )
