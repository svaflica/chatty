from typing import Annotated
from fastapi import Depends, HTTPException, status, FastAPI, Header, Path
from starlette_exporter import PrometheusMiddleware, handle_metrics
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete

import models
from auth_client import get_auth_client, AuthClient

from database import get_db
from post_client import PostClient, get_post_client
from subscription import schemas

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

app = FastAPI()

app.add_middleware(PrometheusMiddleware, prefix='chatty')
app.add_route("/metrics", handle_metrics)


async def create_subscription_user(
    subscr_data: schemas.Subscription,
    db: AsyncSession = Depends(get_db),
):
    db_item = models.Subscription(**subscr_data.model_dump())
    db.add(db_item)
    await db.commit()
    await db.refresh(db_item)


@app.post('/subscription/create')
async def create_subscription(
    subscr_data: schemas.Subscription,
    token: Annotated[str, Depends(oauth2_scheme)],
    db: AsyncSession = Depends(get_db),
    auth_client: AuthClient = Depends(get_auth_client),
):
    auth_client.validate_token(token)

    await create_subscription_user(subscr_data, db)
    return {"status": "subscription added"}


async def remove_subscr_user(
    db: AsyncSession,
    subscr_data: schemas.Subscription,
):
    await db.execute(delete(models.Subscription).where(
        models.Subscription.user_id == subscr_data.user_id \
        and models.Subscription.subscriber_id == subscr_data.subscriber_id
    ))
    await db.commit()


@app.post('/subscription/remove')
async def remove_subscr(
    subscr_data: schemas.Subscription,
    token: Annotated[str, Depends(oauth2_scheme)],
    db: AsyncSession = Depends(get_db),
    auth_client: AuthClient = Depends(get_auth_client),
):
    auth_client.validate_token(token)

    await remove_subscr_user(db, subscr_data)
    return {"status": "subscription removed"}


async def get_subscr_posts_user(
    db: AsyncSession,
    user_id: int,
    post_client: PostClient,
    token,
):
    result = await db.execute(select(models.Subscription).where(
        models.Subscription.subscriber_id == user_id
    ))
    result = result.scalars().all()

    posts = []
    for res in result:
        posts.extend(await post_client.get_posts(token, res.user_id))
    return posts


@app.get('/{user_id}/subscription/posts')
async def get_subscr_posts(
    token: Annotated[str, Depends(oauth2_scheme)],
    user_id: int = Path(),
    db: AsyncSession = Depends(get_db),
    post_client: PostClient = Depends(get_post_client),
    auth_client: AuthClient = Depends(get_auth_client),
):
    auth_client.validate_token(token)

    posts = await get_subscr_posts_user(db, user_id, post_client, token)
    return posts
