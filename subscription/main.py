from typing import Annotated
from fastapi import Depends, HTTPException, status, FastAPI, Header, Path
from starlette_exporter import PrometheusMiddleware, handle_metrics
from sqlalchemy.ext.asyncio import AsyncSession
from auth_client import get_auth_client, AuthClient

from database import get_db
from post_client import PostClient, get_post_client
from subscription import schemas
from subscription.utils import (
    oauth2_scheme,
    create_subscription_user,
    remove_subscr_user,
    get_subscr_posts_user,
    get_recommendation_user,
)


app = FastAPI()

app.add_middleware(PrometheusMiddleware, prefix='chatty')
app.add_route("/metrics", handle_metrics)


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


@app.get('/recommendation/{user_id}/users')
async def get_recommendation(
    token: Annotated[str, Depends(oauth2_scheme)],
    user_id: int = Path(),
    db: AsyncSession = Depends(get_db),
    auth_client: AuthClient = Depends(get_auth_client),
):
    auth_client.validate_token(token)

    posts = await get_recommendation_user(user_id, db)
    return posts
