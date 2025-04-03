from typing import Annotated
from fastapi import Depends, HTTPException, status, FastAPI, Header, Path
from starlette_exporter import PrometheusMiddleware, handle_metrics
from sqlalchemy.ext.asyncio import AsyncSession
from faststream.rabbit import (
    ExchangeType,
    RabbitBroker,
    RabbitExchange,
    RabbitQueue,
)

from auth_client import get_auth_client
from database import get_db
from post import schemas
from post.utils import (
    create_post_user,
    get_post,
    get_posts,
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
from post.rabbit import broker


app = FastAPI()

app.add_middleware(PrometheusMiddleware, prefix='chatty')
app.add_route("/metrics", handle_metrics)


@app.post('/post/create')
async def create_post(
    post_data: schemas.Post,
    token: Annotated[str, Depends(oauth2_scheme)],
    auth_client = Depends(get_auth_client),
    db: AsyncSession = Depends(get_db),
):
    auth_client.validate_token(token)

    await create_post_user(post_data, db)
    return {"status": "post added"}


@app.get('/post/get/{id}')
async def get_post_method(
    token: Annotated[str, Depends(oauth2_scheme)],
    id: int = Path(),
    db: AsyncSession = Depends(get_db),
    auth_client = Depends(get_auth_client),
):
    auth_client.validate_token(token)

    post = await get_post(db, id)
    return post


@app.get('/posts/user/{user_id}')
async def get_posts_method(
    token: Annotated[str, Depends(oauth2_scheme)],
    user_id: int = Path(),
    db: AsyncSession = Depends(get_db),
    auth_client = Depends(get_auth_client),
):
    auth_client.validate_token(token)

    posts = await get_posts(db, user_id)
    return posts


@app.post('/post/edit')
async def edit_post(
    post_data: schemas.EditPost,
    token: Annotated[str, Depends(oauth2_scheme)],
    db: AsyncSession = Depends(get_db),
    auth_client = Depends(get_auth_client),
):
    auth_client.validate_token(token)

    await edit_post_user(db, post_data)
    return {"status": "post edited"}


@app.post('/post/remove')
async def remove_post(
    post_data: schemas.DeletePost,
    token: Annotated[str, Depends(oauth2_scheme)],
    db: AsyncSession = Depends(get_db),
    auth_client = Depends(get_auth_client),
):
    auth_client.validate_token(token)

    await remove_post_user(db, post_data)
    return {"status": "post removed"}


@app.post('/post/comment/create')
async def comment_post(
    comment_data: schemas.CommentPost,
    token: Annotated[str, Depends(oauth2_scheme)],
    db: AsyncSession = Depends(get_db),
    auth_client = Depends(get_auth_client),
):
    auth_client.validate_token(token)

    await comment_post_user(db, comment_data)
    return {"status": "comment posted"}


@app.get('/post/comment/get/{id}')
async def get_post_method(
    token: Annotated[str, Depends(oauth2_scheme)],
    id: int = Path(),
    db: AsyncSession = Depends(get_db),
    auth_client = Depends(get_auth_client),
):
    auth_client.validate_token(token)

    post = await get_comment(db, id)
    return post


@app.post('/post/comment/edit')
async def edit_post(
    comment_data: schemas.EditCommentPost,
    token: Annotated[str, Depends(oauth2_scheme)],
    db: AsyncSession = Depends(get_db),
    auth_client = Depends(get_auth_client),
):
    auth_client.validate_token(token)

    await edit_comment_user(db, comment_data)
    return {"status": "comment edited"}


@app.post('/post/comment/remove')
async def remove_comment_post(
    comment_data: schemas.DeleteCommentPost,
    token: Annotated[str, Depends(oauth2_scheme)],
    db: AsyncSession = Depends(get_db),
    auth_client = Depends(get_auth_client),
):
    auth_client.validate_token(token)

    await remove_comment_user(db, comment_data)
    return {"status": "comment removed"}


@app.post('/post/like/create')
async def like_post(
    like_data: schemas.Like,
    token: Annotated[str, Depends(oauth2_scheme)],
    db: AsyncSession = Depends(get_db),
    auth_client = Depends(get_auth_client),
):
    auth_client.validate_token(token)

    await like_post_user(db, like_data)
    return {"status": "like posted"}


@app.post('/post/like/remove')
async def remove_like_post(
    like_data: schemas.Like,
    token: Annotated[str, Depends(oauth2_scheme)],
    db: AsyncSession = Depends(get_db),
    auth_client = Depends(get_auth_client),
):
    auth_client.validate_token(token)

    await remove_like_user(db, like_data)
    return {"status": "like removed"}


@broker.after_startup
async def startup(app: FastAPI):
    await broker.broker.declare_queue(
        RabbitQueue(
            name="event-post-result",
            durable=True,
        )
    )


app.include_router(broker)
