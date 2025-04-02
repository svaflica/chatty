from typing import Annotated

from fastapi import Depends, HTTPException, status, FastAPI
from fastapi.security import HTTPBasic
from starlette_exporter import PrometheusMiddleware, handle_metrics
from fastapi.security import OAuth2PasswordBearer
from passlib.context import CryptContext
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete

import models
from admin.schemas import User, Post, Comment, Feedback
from auth_client import get_auth_client

from database import get_db


pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")
security = HTTPBasic()

app = FastAPI()

app.add_middleware(PrometheusMiddleware, prefix='chatty')
app.add_route("/metrics", handle_metrics)


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


@app.post('/block-user')
async def block_user(
    user: User,
    token: Annotated[str, Depends(oauth2_scheme)],
    auth_client = Depends(get_auth_client),
    db: AsyncSession = Depends(get_db),
):
    auth_client.validate_token_admin(token)

    await block_user_f(user, db)

    return {"status": f"user {user.user_id} blocked"}


async def remove_user_f(
    user: User,
    db: AsyncSession,
):
    await db.execute(delete(models.User).where(
        models.User.id == user.user_id
    ))
    await db.commit()


@app.post('/delete-user')
async def remove_user(
    user: User,
    token: Annotated[str, Depends(oauth2_scheme)],
    auth_client = Depends(get_auth_client),
    db: AsyncSession = Depends(get_db),
):
    auth_client.validate_token_admin(token)

    await remove_user_f(user, db)

    return {"status": f"user {user.user_id} deleted"}


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


@app.post('/verification-post')
async def verificate_post(
    post: Post,
    token: Annotated[str, Depends(oauth2_scheme)],
    auth_client = Depends(get_auth_client),
    db: AsyncSession = Depends(get_db),
):
    auth_client.validate_token_admin(token)

    await verificate_post_f(post, db)

    return {"status": f"post {post.post_id} status changed"}


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


@app.post('/verification-comment')
async def verificate_comment(
    comment: Comment,
    token: Annotated[str, Depends(oauth2_scheme)],
    auth_client = Depends(get_auth_client),
    db: AsyncSession = Depends(get_db),
):
    auth_client.validate_token_admin(token)

    await verificate_post_f(comment, db)

    return {"status": f"comment {comment.comment_id} status changed"}


async def post_feedback(
    feedback: Feedback,
    db: AsyncSession,
):
    db_item = models.Feedback(text=feedback.text, status="new")
    db.add(db_item)
    await db.commit()
    await db.refresh(db_item)


@app.post('/send-feedback')
async def send_feedback(
    feedback: Feedback,
    token: Annotated[str, Depends(oauth2_scheme)],
    auth_client = Depends(get_auth_client),
    db: AsyncSession = Depends(get_db),
):
    auth_client.validate_token(token)

    await post_feedback(feedback, db)

    return {"status": f"feedback sent"}


@app.get('/stats')
async def get_stats(
    comment: Comment,
    token: Annotated[str, Depends(oauth2_scheme)],
    auth_client = Depends(get_auth_client),
    db: AsyncSession = Depends(get_db),
):
    auth_client.validate_token_admin(token)

    await verificate_post_f(comment, db)

    return {"status": f"comment {comment.comment_id} status changed"}
