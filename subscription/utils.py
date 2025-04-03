from fastapi import Depends, HTTPException, status, FastAPI, Header, Path
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete, text

import models

from database import get_db
from post_client import PostClient
from subscription import schemas


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")


async def create_subscription_user(
    subscr_data: schemas.Subscription,
    db: AsyncSession = Depends(get_db),
):
    db_item = models.Subscription(**subscr_data.model_dump())
    db.add(db_item)
    await db.commit()
    await db.refresh(db_item)


async def remove_subscr_user(
    db: AsyncSession,
    subscr_data: schemas.Subscription,
):
    await db.execute(delete(models.Subscription).where(
        models.Subscription.user_id == subscr_data.user_id \
        and models.Subscription.subscriber_id == subscr_data.subscriber_id
    ))
    await db.commit()


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


async def get_recommendation_user(
    user_id: int = Path(),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(models.Like).where(
        models.Like.user_id == user_id
    ))
    result = result.scalars().all()

    posts_id = [res.post_id for res in result]

    post_id_str = ""
    if len(posts_id) != 0:
        post_id_str = f"public.like.post_id IN ({', '.join([str(post_id) for post_id in posts_id])}) AND "

    result = await db.execute(
        # sorts users by common likes and gets 3 most equal
        text(
            f'''
                SELECT public.user.id, COUNT(*) AS count_likes
                FROM public.user
                join public.like on public.user.id = public.like.user_id
                WHERE {post_id_str} public.user.id != {user_id}
                group by public.user.id
                order by count_likes DESC
                LIMIT 3
            '''
        )
    )
    result = result.scalars().all()

    return result


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
