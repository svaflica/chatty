import pytest
import pytest_asyncio
import base64

from sqlalchemy import select

from auth.utils import get_password_hash
from models import User, Subscription, Post


@pytest_asyncio.fixture
async def add_users(test_db, test_minio):
    with open('tests/resources/1.png', 'rb') as f:
        photo = base64.b64encode(f.read()).decode('utf-8')
    filename = test_minio.put_object(photo)

    item = {"email": "pa@mail.ru", "password": get_password_hash("12345"), "photo": filename}
    db_item = User(**item)
    test_db.add(db_item)

    item = {"email": "p22a@mail.ru", "password": get_password_hash("123456"), "photo": filename}
    db_item2 = User(**item)
    test_db.add(db_item2)

    await test_db.commit()
    await test_db.refresh(db_item)
    await test_db.refresh(db_item2)
    return db_item, db_item2


@pytest_asyncio.fixture
async def add_subscr(add_users, test_db):
    item = {"user_id": 1, "subscriber_id": 2}
    db_item = Subscription(**item)
    test_db.add(db_item)

    await test_db.commit()
    await test_db.refresh(db_item)
    return db_item


@pytest_asyncio.fixture
async def add_posts(add_subscr, test_db):
    item = {"user_id": 1, "text": "Lalalalal"}
    db_item = Post(**item)
    test_db.add(db_item)

    item = {"user_id": 1, "text": "LalalalaPOMPOMl"}
    db_item2 = Post(**item)
    test_db.add(db_item2)

    await test_db.commit()
    await test_db.refresh(db_item)
    await test_db.refresh(db_item2)
    return db_item, db_item2



@pytest.mark.asyncio
async def test_subscribe_add(add_subscr, auth_client, subscr_client, test_db):
    response = await auth_client.post(
        "/login",
        json={"email": "pa@mail.ru", "password": "12345"}
    )
    data = response.json()
    token = data["access_token"]

    response = await subscr_client.post(
        "/subscription/create",
        headers={
            "Authorization": f"Bearer {token}"
        },
        json={
            'user_id': 1,
            'subscriber_id': 2,
        }
    )
    assert response.status_code == 200

    result = await test_db.execute(select(Subscription).where(
        Subscription.id == 1
    ))
    result = result.scalars().all()

    assert len(result) == 1
    assert result[0].id == 1
    assert result[0].user_id == 1
    assert result[0].subscriber_id == 2


@pytest.mark.asyncio
async def test_subscribe_remove(add_subscr, auth_client, subscr_client, test_db):
    response = await auth_client.post(
        "/login",
        json={"email": "pa@mail.ru", "password": "12345"}
    )
    data = response.json()
    token = data["access_token"]

    response = await subscr_client.post(
        "/subscription/remove",
        headers={
            "Authorization": f"Bearer {token}"
        },
        json={
            'user_id': 1,
            'subscriber_id': 2,
        }
    )
    assert response.status_code == 200

    result = await test_db.execute(select(Subscription).where(
        Subscription.id == 1
    ))
    result = result.scalars().all()

    assert len(result) == 0


@pytest.mark.asyncio
async def test_subscribe_get_posts(add_posts, auth_client, subscr_client, test_db):
    response = await auth_client.post(
        "/login",
        json={"email": "pa@mail.ru", "password": "12345"}
    )
    data = response.json()
    token = data["access_token"]

    response = await subscr_client.get(
        "/2/subscription/posts",
        headers={
            "Authorization": f"Bearer {token}"
        },
    )
    assert response.status_code == 200

    data = response.json()

    assert len(data) == 2
