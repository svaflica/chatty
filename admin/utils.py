from fastapi import Depends, HTTPException, status, FastAPI
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete, func

import models
from admin.schemas import User, Post, Comment, Feedback, Complaint
from database import get_db


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")


async def get_user(
    user_id: int,
    db: AsyncSession,

):
    result = await db.execute(select(models.User).where(
        models.User.id == user_id,
    ))
    items = result.scalars().all()
    if not items:
        raise HTTPException(status_code=404, detail="User not found")
    return items[0]


async def block_user_f(
    user: User,
    db: AsyncSession,
):
    db_item = await get_user(user.user_id, db)

    db_item.blocked = True
    db.add(db_item)
    await db.commit()
    await db.refresh(db_item)


async def remove_user_f(
    user: User,
    db: AsyncSession,
):
    await db.execute(delete(models.User).where(
        models.User.id == user.user_id
    ))
    await db.commit()


async def get_post(
    post_id: int,
    db: AsyncSession,

):
    result = await db.execute(select(models.Post).where(
        models.Post.id == post_id,
    ))
    items = result.scalars().all()
    if not items:
        raise HTTPException(status_code=404, detail="Post not found")
    return items[0]


async def verificate_post_f(
    post: Post,
    db: AsyncSession,
):
    db_item = await get_post(post.post_id, db)

    db_item.verified = True
    db.add(db_item)
    await db.commit()
    await db.refresh(db_item)


async def get_comment(
    comment_id: int,
    db: AsyncSession,
):
    result = await db.execute(select(models.Comment).where(
        models.Comment.id == comment_id,
    ))
    items = result.scalars().all()
    if not items:
        raise HTTPException(status_code=404, detail="Comment not found")
    return items[0]


async def verificate_comment_f(
    comment: Comment,
    db: AsyncSession,
):
    db_item = await get_comment(comment.comment_id, db)

    db_item.verified = True
    db.add(db_item)
    await db.commit()
    await db.refresh(db_item)


async def post_feedback(
    feedback: Feedback,
    db: AsyncSession,
):
    db_item = models.Feedback(text=feedback.text, status="new")
    db.add(db_item)
    await db.commit()
    await db.refresh(db_item)


async def post_complaint(
    complaint: Complaint,
    db: AsyncSession,
):
    db_item = models.Complaint(text=complaint.text, user_id=complaint.user_id, status="new")
    db.add(db_item)
    await db.commit()
    await db.refresh(db_item)


async def get_stats_complaint_f(
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(func.count()).select_from(models.Complaint))
    return {'complaint_count': result.scalar()}


async def get_stats_feedback_f(
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(func.count()).select_from(models.Feedback))
    return {'feedback_count': result.scalar()}


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
