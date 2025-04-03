from fastapi import Depends, HTTPException, status, FastAPI, Header, Path
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete

import models

from database import get_db
from post import schemas


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")


async def create_post_user(
    post_data: schemas.Post,
    db: AsyncSession = Depends(get_db),
):
    db_item = models.Post(**post_data.model_dump())
    db.add(db_item)
    await db.commit()
    await db.refresh(db_item)


async def get_post(
    db: AsyncSession,
    id: int,
):
    result = await db.execute(select(models.Post).where(
        models.Post.id == id
    ))
    items = result.scalars().all()
    if not items:
        raise HTTPException(status_code=404, detail="Post not found")
    return items[0]


async def get_posts(
    db: AsyncSession,
    user_id: int,
):
    result = await db.execute(select(models.Post).where(
        models.Post.user_id == user_id
    ))
    items = result.scalars().all()
    if not items:
        raise HTTPException(status_code=404, detail="Post not found")
    return items


async def edit_post_user(
    db: AsyncSession,
    post: schemas.EditPost,
):
    db_item = await get_post(db, post.id)

    if db_item is None:
        raise HTTPException(status_code=400, detail="Inactive user")

    db_item.text = post.text
    db.add(db_item)
    await db.commit()
    await db.refresh(db_item)


async def remove_post_user(
    db: AsyncSession,
    post_data: schemas.DeletePost,
):
    await db.execute(delete(models.Post).where(
        models.Post.id == post_data.id
    ))
    await db.commit()


async def comment_post_user(
    db: AsyncSession,
    comment_data: schemas.CommentPost,
):
    db_item = models.Comment(**comment_data.model_dump())
    db.add(db_item)
    await db.commit()
    await db.refresh(db_item)


async def get_comment(
    db: AsyncSession,
    id: int,
):
    result = await db.execute(select(models.Comment).where(
        models.Comment.id == id
    ))
    items = result.scalars().all()
    if not items:
        raise HTTPException(status_code=404, detail="Post not found")
    return items[0]


async def edit_comment_user(
    db: AsyncSession,
    comment: schemas.EditCommentPost,
):
    db_item = await get_comment(db, comment.id)

    if db_item is None:
        raise HTTPException(status_code=400, detail="Inactive user")

    db_item.text = comment.text
    db.add(db_item)
    await db.commit()
    await db.refresh(db_item)


async def remove_comment_user(
    db: AsyncSession,
    comment_data: schemas.DeleteCommentPost,
):
    await db.execute(delete(models.Comment).where(
        models.Comment.id == comment_data.id
    ))
    await db.commit()


async def like_post_user(
    db: AsyncSession,
    like_data: schemas.Like,
):
    db_item = models.Like(**like_data.model_dump())
    db.add(db_item)
    await db.commit()
    await db.refresh(db_item)


async def remove_like_user(
    db: AsyncSession,
    like: schemas.Like,
):
    await db.execute(delete(models.Like).where(
        models.Like.user_id == like.user_id and models.Like.post_id == like.post_id
    ))
    await db.commit()


async def get_rabbit_message(
    db: AsyncSession,
    message_id: str,
):
    result = await db.execute(select(models.RabbitMessage).where(
        models.RabbitMessage.message_id == message_id
    ))
    items = result.scalars().all()
    if not items:
        raise HTTPException(status_code=404, detail="RabbitMessage not found")
    return items[0]


async def remove_rabbit_message(
    db: AsyncSession,
    message_id: str,
):
    await db.execute(delete(models.RabbitMessage).where(
        models.RabbitMessage.message_id == message_id
    ))
    await db.commit()
