from typing import Annotated
from fastapi import Depends, HTTPException, status, FastAPI, Header, Path
from starlette_exporter import PrometheusMiddleware, handle_metrics
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete

import models

from auth_client import get_auth_client
from database import get_db
from post import schemas

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

app = FastAPI()

app.add_middleware(PrometheusMiddleware, prefix='chatty')
app.add_route("/metrics", handle_metrics)


async def create_post_user(
    post_data: schemas.Post,
    db: AsyncSession = Depends(get_db),
):
    db_item = models.Post(**post_data.model_dump())
    db.add(db_item)
    await db.commit()
    await db.refresh(db_item)


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


async def remove_post_user(
    db: AsyncSession,
    post_data: schemas.DeletePost,
):
    await db.execute(delete(models.Post).where(
        models.Post.id == post_data.id
    ))
    await db.commit()


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


async def comment_post_user(
    db: AsyncSession,
    comment_data: schemas.CommentPost,
):
    db_item = models.Comment(**comment_data.model_dump())
    db.add(db_item)
    await db.commit()
    await db.refresh(db_item)


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


async def remove_comment_user(
    db: AsyncSession,
    comment_data: schemas.DeleteCommentPost,
):
    await db.execute(delete(models.Comment).where(
        models.Comment.id == comment_data.id
    ))
    await db.commit()


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


async def like_post_user(
    db: AsyncSession,
    like_data: schemas.Like,
):
    db_item = models.Like(**like_data.model_dump())
    db.add(db_item)
    await db.commit()
    await db.refresh(db_item)


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


async def remove_like_user(
    db: AsyncSession,
    like: schemas.Like,
):
    await db.execute(delete(models.Like).where(
        models.Like.user_id == like.user_id and models.Like.post_id == like.post_id
    ))
    await db.commit()


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
