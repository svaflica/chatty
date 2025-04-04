import logging

from typing import Annotated
from fastapi import Depends, HTTPException, status, FastAPI
from starlette_exporter import PrometheusMiddleware, handle_metrics
from sqlalchemy.ext.asyncio import AsyncSession
from faststream.rabbit import (
    ExchangeType,
    RabbitBroker,
    RabbitExchange,
    RabbitQueue,
)

from admin.schemas import User, Post, Comment, Feedback, Complaint
from auth_client import get_auth_client
from database import get_db
from admin.utils import (
    oauth2_scheme,
    block_user_f,
    remove_user_f,
    verificate_post_f,
    verificate_comment_f,
    post_feedback,
    post_complaint,
    get_stats_complaint_f,
    get_stats_feedback_f
)
from admin.rabbit import broker

logger = logging.getLogger('logger_app')

app = FastAPI()

app.add_middleware(PrometheusMiddleware, prefix='chatty')
app.add_route("/metrics", handle_metrics)


@app.post('/block-user')
async def block_user(
    user: User,
    token: Annotated[str, Depends(oauth2_scheme)],
    auth_client = Depends(get_auth_client),
    db: AsyncSession = Depends(get_db),
):
    logger.info('Blocking user started')
    auth_client.validate_token_admin(token)

    await block_user_f(user, db)
    logger.info('Blocking user ended')

    return {"status": f"user {user.user_id} blocked"}


@app.post('/delete-user')
async def remove_user(
    user: User,
    token: Annotated[str, Depends(oauth2_scheme)],
    auth_client = Depends(get_auth_client),
    db: AsyncSession = Depends(get_db),
):
    logger.info('Deleting user started')
    auth_client.validate_token_admin(token)

    await remove_user_f(user, db)
    logger.info('Deleting user ended')

    return {"status": f"user {user.user_id} deleted"}


@app.post('/verification-post')
async def verificate_post(
    post: Post,
    token: Annotated[str, Depends(oauth2_scheme)],
    auth_client = Depends(get_auth_client),
    db: AsyncSession = Depends(get_db),
):
    logger.info('Verification post started')
    auth_client.validate_token_admin(token)

    await verificate_post_f(post, db)
    logger.info('Verification post started')

    return {"status": f"post {post.post_id} status changed"}


@app.post('/verification-comment')
async def verificate_comment(
    comment: Comment,
    token: Annotated[str, Depends(oauth2_scheme)],
    auth_client = Depends(get_auth_client),
    db: AsyncSession = Depends(get_db),
):
    logger.info('Verification comment started')
    auth_client.validate_token_admin(token)

    await verificate_comment_f(comment, db)
    logger.info('Verification comment ended')

    return {"status": f"comment {comment.comment_id} status changed"}


@app.post('/send-feedback')
async def send_feedback(
    feedback: Feedback,
    token: Annotated[str, Depends(oauth2_scheme)],
    auth_client = Depends(get_auth_client),
    db: AsyncSession = Depends(get_db),
):
    logger.info('Sending feedback started')
    auth_client.validate_token(token)

    await post_feedback(feedback, db)
    logger.info('Sending feedback ended')

    return {"status": f"feedback sent"}


@app.post('/send-complaint')
async def send_complaint(
    complaint: Complaint,
    token: Annotated[str, Depends(oauth2_scheme)],
    auth_client = Depends(get_auth_client),
    db: AsyncSession = Depends(get_db),
):
    logger.info('Sending compliant started')
    auth_client.validate_token(token)

    await post_complaint(complaint, db)
    logger.info('Sending compliant ended')

    return {"status": f"complaint sent"}


@app.get('/stats_complaint')
async def get_stats_complaint(
    token: Annotated[str, Depends(oauth2_scheme)],
    auth_client = Depends(get_auth_client),
    db: AsyncSession = Depends(get_db),
):
    logger.info('Getting stats complaint started')
    auth_client.validate_token_admin(token)

    result = await get_stats_complaint_f(db)
    logger.info('Getting stats complaint ended')
    return result


@app.get('/stats_feedback')
async def get_stats_feedback(
    token: Annotated[str, Depends(oauth2_scheme)],
    auth_client = Depends(get_auth_client),
    db: AsyncSession = Depends(get_db),
):
    logger.info('Getting stats feedback started')
    auth_client.validate_token_admin(token)

    result = await get_stats_feedback_f(db)
    logger.info('Getting stats feedback ended')
    return result


@broker.after_startup
async def startup(app: FastAPI):
    await broker.broker.declare_queue(
        RabbitQueue(
            name="event-admin-result",
            durable=False,
        )
    )


app.include_router(broker)
