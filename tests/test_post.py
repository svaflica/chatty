import pytest
import pytest_asyncio
import base64

from sqlalchemy import select

import models
from auth.utils import get_password_hash
from models import User


@pytest_asyncio.fixture
async def add_users(test_db, test_minio):
    with open('tests/resources/1.png', 'rb') as f:
        photo = base64.b64encode(f.read()).decode('utf-8')
    filename = test_minio.put_object(photo)

    item = {"email": "pa@mail.ru", "password": get_password_hash("12345"), "photo": filename}
    db_item = User(**item)
    test_db.add(db_item)

    await test_db.commit()
    await test_db.refresh(db_item)
    return db_item


@pytest_asyncio.fixture
async def add_posts(test_db, add_users):
    item = {"user_id": 1, "text": "Lalalalal"}
    db_item = models.Post(**item)
    test_db.add(db_item)

    await test_db.commit()
    await test_db.refresh(db_item)
    return db_item


@pytest_asyncio.fixture
async def add_likes(test_db, add_posts):
    item = {"user_id": 1, "post_id": 1}
    db_item = models.Like(**item)
    test_db.add(db_item)

    await test_db.commit()
    await test_db.refresh(db_item)
    return db_item


@pytest_asyncio.fixture
async def add_comments(test_db, add_posts):
    item = {"user_id": 1, "text": "Comment", "post_id": 1}
    db_item = models.Comment(**item)
    test_db.add(db_item)

    await test_db.commit()
    await test_db.refresh(db_item)
    return db_item


@pytest.mark.asyncio
async def test_post_get(auth_client, post_client, add_posts, test_db):
    response = await auth_client.post(
        "/login",
        json={"email": "pa@mail.ru", "password": "12345"}
    )
    data = response.json()
    token = data["access_token"]

    response = await post_client.get(
        "/post/get/1",
        headers={
            "Authorization": f"Bearer {token}"
        }
    )
    assert response.status_code == 200

    result = response.json()

    assert isinstance(result, dict)
    assert result["id"] == 1
    assert result["user_id"] == 1
    assert result["text"] == "Lalalalal"


@pytest.mark.asyncio
async def test_post_create(auth_client, post_client, add_users, test_db):
    response = await auth_client.post(
        "/login",
        json={"email": "pa@mail.ru", "password": "12345"}
    )
    data = response.json()
    token = data["access_token"]

    response = await post_client.post(
        "/post/create",
        json={"user_id": 1, "text": "Text very useful"},
        headers={
            "Authorization": f"Bearer {token}"
        }
    )
    assert response.status_code == 200

    result = await test_db.execute(select(models.Post).where(
        models.Post.id == 1
    ))
    result = result.scalars().all()

    assert len(result) == 1
    assert result[0].id == 1
    assert result[0].user_id == 1
    assert result[0].text == "Text very useful"


@pytest.mark.asyncio
async def test_post_edit(auth_client, post_client, add_posts, test_db):
    response = await auth_client.post(
        "/login",
        json={"email": "pa@mail.ru", "password": "12345"}
    )
    data = response.json()
    token = data["access_token"]

    response = await post_client.post(
        "/post/edit",
        json={"user_id": 1, "text": "Text very useful", "id": 1},
        headers={
            "Authorization": f"Bearer {token}"
        }
    )
    assert response.status_code == 200

    result = await test_db.execute(select(models.Post).where(
        models.Post.id == 1
    ))
    result = result.scalars().all()

    assert len(result) == 1
    assert result[0].id == 1
    assert result[0].user_id == 1
    assert result[0].text == "Text very useful"


@pytest.mark.asyncio
async def test_post_remove(auth_client, post_client, add_posts, test_db):
    response = await auth_client.post(
        "/login",
        json={"email": "pa@mail.ru", "password": "12345"}
    )
    data = response.json()
    token = data["access_token"]

    response = await post_client.post(
        "/post/remove",
        json={"id": 1},
        headers={
            "Authorization": f"Bearer {token}"
        }
    )
    assert response.status_code == 200

    result = await test_db.execute(select(models.Post).where(
        models.Post.id == 1
    ))
    result = result.scalars().all()

    assert len(result) == 0


@pytest.mark.asyncio
async def test_comment_create(auth_client, post_client, add_posts, test_db):
    response = await auth_client.post(
        "/login",
        json={"email": "pa@mail.ru", "password": "12345"}
    )
    data = response.json()
    token = data["access_token"]

    response = await post_client.post(
        "/post/comment/create",
        json={"user_id": 1, "post_id": 1, "text": "Plohoy"},
        headers={
            "Authorization": f"Bearer {token}"
        }
    )
    assert response.status_code == 200

    result = await test_db.execute(select(models.Comment).where(
        models.Comment.id == 1
    ))
    result = result.scalars().all()

    assert len(result) == 1
    assert result[0].id == 1
    assert result[0].user_id == 1
    assert result[0].post_id == 1
    assert result[0].text == "Plohoy"



@pytest.mark.asyncio
async def test_comment_edit(auth_client, post_client, add_comments, test_db):
    response = await auth_client.post(
        "/login",
        json={"email": "pa@mail.ru", "password": "12345"}
    )
    data = response.json()
    token = data["access_token"]

    response = await post_client.post(
        "/post/comment/edit",
        json={"id": 1, "text": "Text very useful edited"},
        headers={
            "Authorization": f"Bearer {token}"
        }
    )
    assert response.status_code == 200

    result = await test_db.execute(select(models.Comment).where(
        models.Comment.id == 1
    ))
    result = result.scalars().all()

    assert len(result) == 1
    assert result[0].id == 1
    assert result[0].user_id == 1
    assert result[0].text == "Text very useful edited"


@pytest.mark.asyncio
async def test_comment_remove(auth_client, post_client, add_comments, test_db):
    response = await auth_client.post(
        "/login",
        json={"email": "pa@mail.ru", "password": "12345"}
    )
    data = response.json()
    token = data["access_token"]

    response = await post_client.post(
        "/post/comment/remove",
        json={"id": 1},
        headers={
            "Authorization": f"Bearer {token}"
        }
    )
    assert response.status_code == 200

    result = await test_db.execute(select(models.Comment).where(
        models.Comment.id == 1
    ))
    result = result.scalars().all()

    assert len(result) == 0


@pytest.mark.asyncio
async def test_comment_get(auth_client, post_client, add_comments, test_db):
    response = await auth_client.post(
        "/login",
        json={"email": "pa@mail.ru", "password": "12345"}
    )
    data = response.json()
    token = data["access_token"]

    response = await post_client.get(
        "/post/comment/get/1",
        headers={
            "Authorization": f"Bearer {token}"
        }
    )
    assert response.status_code == 200

    result = response.json()

    assert isinstance(result, dict)
    assert result["id"] == 1
    assert result["user_id"] == 1
    assert result["text"] == "Comment"
    assert result["post_id"] == 1


@pytest.mark.asyncio
async def test_like_create(auth_client, post_client, add_posts, test_db):
    response = await auth_client.post(
        "/login",
        json={"email": "pa@mail.ru", "password": "12345"}
    )
    data = response.json()
    token = data["access_token"]

    response = await post_client.post(
        "/post/like/create",
        json={"user_id": 1, "post_id": 1},
        headers={
            "Authorization": f"Bearer {token}"
        }
    )
    assert response.status_code == 200

    result = await test_db.execute(select(models.Like).where(
        models.Like.id == 1
    ))
    result = result.scalars().all()

    assert len(result) == 1
    assert result[0].id == 1
    assert result[0].user_id == 1
    assert result[0].post_id == 1


@pytest.mark.asyncio
async def test_like_remove(auth_client, post_client, add_comments, test_db):
    response = await auth_client.post(
        "/login",
        json={"email": "pa@mail.ru", "password": "12345"}
    )
    data = response.json()
    token = data["access_token"]

    response = await post_client.post(
        "/post/like/remove",
        json={"user_id": 1, "post_id": 1},
        headers={
            "Authorization": f"Bearer {token}"
        }
    )
    assert response.status_code == 200

    result = await test_db.execute(select(models.Like).where(
        models.Like.id == 1
    ))
    result = result.scalars().all()

    assert len(result) == 0

