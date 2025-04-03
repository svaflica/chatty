import json

from typing import Annotated
from fastapi import Depends, HTTPException, status, FastAPI, Header, Path
from sqlalchemy.ext.asyncio import AsyncSession
from faststream.rabbit.fastapi import RabbitRouter

import models

from config import settings
from database import get_db
from subscription import schemas
from subscription.utils import (
    oauth2_scheme,
    get_rabbit_message,
    remove_rabbit_message,
    create_subscription_user,
    remove_subscr_user,
    get_recommendation_user,
)


broker = RabbitRouter(settings.async_rm_url)


@broker.subscriber('event-subscr', filter=lambda m: 'subscr' in m.message_id)
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
        message_id='check-token' + msg["message_id"],
        headers={
            'Authorization': f'Bearer {token}'
        }
    )


@broker.subscriber('event-auth-result-subscr', filter=lambda m: 'subscr' in m.message_id)
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
        queue='event-subscr-verified',
        message_id=msg["message_id"],
    )


@broker.subscriber('event-subscr-verified', filter=lambda m: 'subscr-create' in m.message_id)
async def create_subscription(
    subscr_data: schemas.SubscriptionRabbit,
    db: AsyncSession = Depends(get_db),
):
    await create_subscription_user(schemas.Subscription(**subscr_data.model_dump()), db)
    await broker.broker.publish(
        message={"status": "subscription added"},
        queue='event-subscr-result',
        message_id=subscr_data.message_id,
    )


@broker.subscriber('event-subscr-verified', filter=lambda m: 'subscr-remove' in m.message_id)
async def remove_subscr(
    subscr_data: schemas.SubscriptionRabbit,
    db: AsyncSession = Depends(get_db),
):
    await remove_subscr_user(db, subscr_data)
    await broker.broker.publish(
        message={"status": "subscription removed"},
        queue='event-subscr-result',
        message_id=subscr_data.message_id,
    )


@broker.subscriber('event-subscr-verified', filter=lambda m: 'subscr-recommend' in m.message_id)
async def get_recommendation(
    msg: dict,
    db: AsyncSession = Depends(get_db),
):
    users = await get_recommendation_user(msg["user_id"], db)
    await broker.broker.publish(
        message=str(users),
        queue='event-subscr-result',
        message_id=msg["message_id"],
    )
