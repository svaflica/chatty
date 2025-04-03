import json

from typing import Annotated
from fastapi import Depends, HTTPException, status, FastAPI, Header, Path
from sqlalchemy.ext.asyncio import AsyncSession
from faststream.rabbit.fastapi import RabbitRouter

import models

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
    oauth2_scheme, get_rabbit_message, remove_rabbit_message,
)


broker = RabbitRouter(settings.async_rm_url)


@broker.subscriber('event-post', filter=lambda m: 'post' in m.message_id)
async def validate_token(
    msg: dict,
    token: Annotated[str, Depends(oauth2_scheme)],
    db: AsyncSession = Depends(get_db),
):
    db_item = models.RabbitMessage(
        message_id=msg["message_id"],
        text=json.dumps(msg),
    )
    db.add(db_item)
    await db.commit()
    await db.refresh(db_item)

    await broker.broker.publish(
        message={"message_id": msg["message_id"]},
        queue='event-auth',
        message_id='check-token' + msg["message_id"],
        headers={
            'Authorization': f'Bearer {token}'
        }
    )


@broker.subscriber('event-auth-result-post', filter=lambda m: 'post' in m.message_id)
async def validate_token_result(
    msg: dict,
    db: AsyncSession = Depends(get_db),
):
    db_item = await get_rabbit_message(db, msg["message_id"])
    data = json.loads(db_item.text)

    await remove_rabbit_message(db, msg["message_id"])
    await db.commit()

    await broker.broker.publish(
        message=data,
        queue='event-post-verified',
        message_id=msg["message_id"],
    )


@broker.subscriber('event-post-verified', filter=lambda m: 'post-create' in m.message_id)
async def create_post_rabbit(
    post_data: schemas.PostRabbit,
    db: AsyncSession = Depends(get_db),
):
    await create_post_user(schemas.Post(**post_data.model_dump()), db)
    await broker.broker.publish(
        message={"status": "post created"},
        queue='event-post-result',
        message_id=post_data.message_id,
    )


@broker.subscriber('event-post-verified', filter=lambda m: 'post-get' in m.message_id)
async def get_post_method_rabbit(
    form_data: schemas.PostGetRabbit,
    token: Annotated[str, Depends(oauth2_scheme)],
    db: AsyncSession = Depends(get_db),
    auth_client = Depends(get_auth_client),
):
    auth_client.validate_token(token)

    post = await get_post(db, form_data.id)
    await broker.broker.publish(
        message={'id': post.id, 'text': post.text, 'user_id': post.user_id},
        queue='event-post-result',
        message_id=form_data.message_id,
    )


@broker.subscriber('event-post-verified', filter=lambda m: 'post-edit' in m.message_id)
async def edit_post_rabbit(
    post_data: schemas.EditPostRabbit,
    token: Annotated[str, Depends(oauth2_scheme)],
    db: AsyncSession = Depends(get_db),
    auth_client = Depends(get_auth_client),
):
    auth_client.validate_token(token)

    await edit_post_user(db, schemas.EditPost(post_data.model_dump()))
    await broker.broker.publish(
        message={"status": "post edited"},
        queue='event-post-result',
        message_id=post_data.message_id,
    )


@broker.subscriber('event-post-verified', filter=lambda m: 'post-remove' in m.message_id)
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


@broker.subscriber('event-post-verified', filter=lambda m: 'post-comment-create' in m.message_id)
async def comment_post_rabbit(
    comment_data: schemas.CommentPostRabbit,
    token: Annotated[str, Depends(oauth2_scheme)],
    db: AsyncSession = Depends(get_db),
    auth_client = Depends(get_auth_client),
):
    auth_client.validate_token(token)

    await comment_post_user(db, schemas.CommentPost(**comment_data.model_dump()))
    await broker.broker.publish(
        message={"status": "comment posted"},
        queue='event-post-result',
        message_id=comment_data.message_id,
    )


@broker.subscriber('event-post-verified', filter=lambda m: 'post-comment-get' in m.message_id)
async def get_comment_method_rabbit(
    token: Annotated[str, Depends(oauth2_scheme)],
    form_data: schemas.CommentPostGetRabbit,
    db: AsyncSession = Depends(get_db),
    auth_client = Depends(get_auth_client),
):
    auth_client.validate_token(token)

    comment = await get_comment(db, form_data.id)
    await broker.broker.publish(
        message={
            'id': comment.id,
            'user_id': comment.user_id,
            'post_id': comment.post_id,
            'text': comment.text,
        },
        queue='event-post-result',
        message_id=form_data.message_id,
    )


@broker.subscriber('event-post-verified', filter=lambda m: 'post-comment-edit' in m.message_id)
async def edit_post_rabbit(
    comment_data: schemas.EditCommentPostRabbit,
    token: Annotated[str, Depends(oauth2_scheme)],
    db: AsyncSession = Depends(get_db),
    auth_client = Depends(get_auth_client),
):
    auth_client.validate_token(token)

    await edit_comment_user(db, schemas.EditCommentPost(**comment_data.model_dump()))
    await broker.broker.publish(
        message={"status": "comment edited"},
        queue='event-post-result',
        message_id=comment_data.message_id,
    )


@broker.subscriber('event-post-verified', filter=lambda m: 'post-comment-remove' in m.message_id)
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


@broker.subscriber('event-post-verified', filter=lambda m: 'post-like-create' in m.message_id)
async def like_post_rabbit(
    like_data: schemas.LikeRabbit,
    token: Annotated[str, Depends(oauth2_scheme)],
    db: AsyncSession = Depends(get_db),
    auth_client = Depends(get_auth_client),
):
    auth_client.validate_token(token)

    await like_post_user(db, schemas.Like(**like_data.model_dump()))
    await broker.broker.publish(
        message={"status": "like posted"},
        queue='event-post-result',
        message_id=like_data.message_id,
    )


@broker.subscriber('event-post-verified', filter=lambda m: 'post-like-remove' in m.message_id)
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
