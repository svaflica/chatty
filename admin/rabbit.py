import json

from typing import Annotated
from fastapi import Depends, HTTPException, status, FastAPI, Header, Path
from sqlalchemy.ext.asyncio import AsyncSession
from faststream.rabbit.fastapi import RabbitRouter

import models

from config import settings
from database import get_db
from admin.schemas import (
    UserRabbit, CommentRabbit, PostRabbit, FeedbackRabbit, ComplaintRabbit, Feedback, Complaint
)
from admin.utils import (
    oauth2_scheme,
    block_user_f,
    remove_user_f,
    verificate_post_f,
    verificate_comment_f,
    post_feedback,
    post_complaint,
    get_stats_complaint_f,
    get_stats_feedback_f, get_rabbit_message, remove_rabbit_message
)

broker = RabbitRouter(settings.async_rm_url)


@broker.subscriber('event-admin', filter=lambda m: 'admin' in m.message_id)
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
        message_id='check-admin-token' + msg["message_id"],
        headers={
            'Authorization': f'Bearer {token}'
        }
    )


@broker.subscriber('event-auth-result-admin', filter=lambda m: 'admin' in m.message_id)
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
        queue='event-admin-verified',
        message_id=msg["message_id"],
    )


@broker.subscriber('event-verified-admin', filter=lambda m: 'block-user' in m.message_id)
async def block_user(
    user: UserRabbit,
    db: AsyncSession = Depends(get_db),
):
    await block_user_f(user, db)
    await broker.broker.publish(
        message={"status": f"user {user.user_id} blocked"},
        queue='event-admin-result',
        message_id=user.message_id,
    )


@broker.subscriber('event-verified-admin', filter=lambda m: 'remove-user' in m.message_id)
async def remove_user(
    user: UserRabbit,
    db: AsyncSession = Depends(get_db),
):
    await remove_user_f(user, db)
    await broker.broker.publish(
        message={"status": f"user {user.user_id} deleted"},
        queue='event-admin-result',
        message_id=user.message_id,
    )


@broker.subscriber('event-verified-admin', filter=lambda m: 'verificate-post' in m.message_id)
async def verificate_post(
    post: PostRabbit,
    db: AsyncSession = Depends(get_db),
):
    await verificate_post_f(post, db)
    await broker.broker.publish(
        message={"status": f"post {post.post_id} status changed"},
        queue='event-admin-result',
        message_id=post.message_id,
    )


@broker.subscriber('event-verified-admin', filter=lambda m: 'verificate-comment' in m.message_id)
async def verificate_comment(
    comment: CommentRabbit,
    db: AsyncSession = Depends(get_db),
):
    await verificate_comment_f(comment, db)
    await broker.broker.publish(
        message={"status": f"comment {comment.comment_id} status changed"},
        queue='event-admin-result',
        message_id=comment.message_id,
    )


@broker.subscriber('event-verified-admin', filter=lambda m: 'send-feedback' in m.message_id)
async def send_feedback(
    feedback: FeedbackRabbit,
    db: AsyncSession = Depends(get_db),
):
    await post_feedback(Feedback(**feedback.model_dump()), db)
    await broker.broker.publish(
        message={"status": f"feedback sent"},
        queue='event-admin-result',
        message_id=feedback.message_id,
    )


@broker.subscriber('event-verified-admin', filter=lambda m: 'send-complaint' in m.message_id)
async def send_complaint(
    complaint: ComplaintRabbit,
    db: AsyncSession = Depends(get_db),
):
    await post_complaint(Complaint(**complaint.model_dump()), db)
    await broker.broker.publish(
        message={"status": f"complaint sent"},
        queue='event-admin-result',
        message_id=complaint.message_id,
    )


@broker.subscriber('event-verified-admin', filter=lambda m: 'stats-complaint' in m.message_id)
async def get_stats_complaint(
    msg: dict,
    db: AsyncSession = Depends(get_db),
):
    result = await get_stats_complaint_f(db)
    await broker.broker.publish(
        message=result,
        queue='event-admin-result',
        message_id=msg.get("message_id", ""),
    )


@broker.subscriber('event-verified-admin', filter=lambda m: 'stats-feedback' in m.message_id)
async def get_stats_feedback(
    msg: dict,
    db: AsyncSession = Depends(get_db),
):
    result = await get_stats_feedback_f(db)
    await broker.broker.publish(
        message=result,
        queue='event-admin-result',
        message_id=msg.get("message_id", ""),
    )
