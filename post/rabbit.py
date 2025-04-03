from typing import Annotated
from fastapi import Depends, HTTPException, status, FastAPI, Header, Path
from sqlalchemy.ext.asyncio import AsyncSession
from faststream.rabbit.fastapi import RabbitRouter

from auth_client import get_auth_client
from config import settings
from database import get_db
from post import schemas
from post.utils import (
    create_post_user,
    get_post,
    edit_post_user,
    remove_post_user,
    comment_post_user,
    get_comment,
    edit_comment_user,
    remove_comment_user,
    like_post_user,
    remove_like_user,
    oauth2_scheme,
)


broker = RabbitRouter(settings.async_rm_url)
publisher = broker.publisher('event-result-post')


@broker.subscriber('event-post', filter=lambda m: 'post-create' in m.message_id)
async def create_post_rabbit(
    post_data: schemas.PostRabbit,
    token: Annotated[str, Depends(oauth2_scheme)],
    auth_client = Depends(get_auth_client),
    db: AsyncSession = Depends(get_db),
):
    auth_client.validate_token(token)

    await create_post_user(post_data, db)
    await broker.broker.publish(
        message={"status": "post created"},
        queue='event-post-result',
        message_id=post_data.message_id,
    )


@broker.subscriber('event-post', filter=lambda m: 'post-get' in m.message_id)
async def get_post_method_rabbit(
    form_data: schemas.PostGetRabbit,
    token: Annotated[str, Depends(oauth2_scheme)],
    db: AsyncSession = Depends(get_db),
    auth_client = Depends(get_auth_client),
):
    auth_client.validate_token(token)

    post = await get_post(db, form_data.id)
    await broker.broker.publish(
        message=post,
        queue='event-post-result',
        message_id=form_data.message_id,
    )


@broker.subscriber('event-post', filter=lambda m: 'post-edit' in m.message_id)
async def edit_post_rabbit(
    post_data: schemas.EditPostRabbit,
    token: Annotated[str, Depends(oauth2_scheme)],
    db: AsyncSession = Depends(get_db),
    auth_client = Depends(get_auth_client),
):
    auth_client.validate_token(token)

    await edit_post_user(db, post_data)
    await broker.broker.publish(
        message={"status": "post edited"},
        queue='event-post-result',
        message_id=post_data.message_id,
    )


@broker.subscriber('event-post', filter=lambda m: 'post-remove' in m.message_id)
async def remove_post_rabbit(
    post_data: schemas.DeletePostRabbit,
    token: Annotated[str, Depends(oauth2_scheme)],
    db: AsyncSession = Depends(get_db),
    auth_client = Depends(get_auth_client),
):
    auth_client.validate_token(token)

    await remove_post_user(db, post_data)
    await broker.broker.publish(
        message={"status": "post removed"},
        queue='event-post-result',
        message_id=post_data.message_id,
    )


@broker.subscriber('event-post', filter=lambda m: 'comment-create' in m.message_id)
async def comment_post_rabbit(
    comment_data: schemas.CommentPostRabbit,
    token: Annotated[str, Depends(oauth2_scheme)],
    db: AsyncSession = Depends(get_db),
    auth_client = Depends(get_auth_client),
):
    auth_client.validate_token(token)

    await comment_post_user(db, comment_data)
    await broker.broker.publish(
        message={"status": "comment posted"},
        queue='event-post-result',
        message_id=comment_data.message_id,
    )


@broker.subscriber('event-post', filter=lambda m: 'comment-get' in m.message_id)
async def get_comment_method_rabbit(
    token: Annotated[str, Depends(oauth2_scheme)],
    form_data: schemas.CommentPostGetRabbit,
    db: AsyncSession = Depends(get_db),
    auth_client = Depends(get_auth_client),
):
    auth_client.validate_token(token)

    post = await get_comment(db, form_data.id)
    await broker.broker.publish(
        message=post,
        queue='event-post-result',
        message_id=form_data.message_id,
    )


@broker.subscriber('event-post', filter=lambda m: 'comment-edit' in m.message_id)
async def edit_post_rabbit(
    comment_data: schemas.EditCommentPostRabbit,
    token: Annotated[str, Depends(oauth2_scheme)],
    db: AsyncSession = Depends(get_db),
    auth_client = Depends(get_auth_client),
):
    auth_client.validate_token(token)

    await edit_comment_user(db, comment_data)
    await broker.broker.publish(
        message={"status": "comment edited"},
        queue='event-post-result',
        message_id=comment_data.message_id,
    )


@broker.subscriber('event-post', filter=lambda m: 'comment-remove' in m.message_id)
async def remove_comment_post_rabbit(
    comment_data: schemas.DeleteCommentRabbit,
    token: Annotated[str, Depends(oauth2_scheme)],
    db: AsyncSession = Depends(get_db),
    auth_client = Depends(get_auth_client),
):
    auth_client.validate_token(token)

    await remove_comment_user(db, comment_data)
    await broker.broker.publish(
        message={"status": "comment removed"},
        queue='event-post-result',
        message_id=comment_data.message_id,
    )


@broker.subscriber('event-post', filter=lambda m: 'like-create' in m.message_id)
async def like_post_rabbit(
    like_data: schemas.LikeRabbit,
    token: Annotated[str, Depends(oauth2_scheme)],
    db: AsyncSession = Depends(get_db),
    auth_client = Depends(get_auth_client),
):
    auth_client.validate_token(token)

    await like_post_user(db, like_data)
    await broker.broker.publish(
        message={"status": "like posted"},
        queue='event-post-result',
        message_id=like_data.message_id,
    )


@broker.subscriber('event-post', filter=lambda m: 'like-remove' in m.message_id)
async def remove_like_post_rabbit(
    like_data: schemas.LikeRabbit,
    token: Annotated[str, Depends(oauth2_scheme)],
    db: AsyncSession = Depends(get_db),
    auth_client = Depends(get_auth_client),
):
    auth_client.validate_token(token)

    await remove_like_user(db, like_data)
    await broker.broker.publish(
        message={"status": "like removed"},
        queue='event-post-result',
        message_id=like_data.message_id,
    )
