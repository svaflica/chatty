import pytest
import pytest_asyncio
import base64

from sqlalchemy import select

from auth.main import get_password_hash
from models import User, Subscription, Post, Comment, Feedback, Complaint


@pytest_asyncio.fixture
async def add_users(test_db, test_minio):
    with open('tests/resources/1.png', 'rb') as f:
        photo = base64.b64encode(f.read()).decode('utf-8')
    filename = test_minio.put_object(photo)

    item = {"email": "pa@mail.ru", "password": get_password_hash("12345"), "photo": filename}
    db_item = User(**item)
    db_item.is_admin = True
    test_db.add(db_item)

    item = {"email": "p22a@mail.ru", "password": get_password_hash("123456"), "photo": filename}
    db_item2 = User(**item)
    test_db.add(db_item2)

    await test_db.commit()
    await test_db.refresh(db_item)
    await test_db.refresh(db_item2)
    return db_item, db_item2


@pytest_asyncio.fixture
async def add_posts(add_users, test_db):
    item = {"user_id": 2, "text": "Lalalalal"}
    db_item = Post(**item)
    test_db.add(db_item)

    item = {"user_id": 2, "text": "LalalalaPOMPOMl"}
    db_item2 = Post(**item)
    test_db.add(db_item2)

    await test_db.commit()
    await test_db.refresh(db_item)
    await test_db.refresh(db_item2)
    return db_item, db_item2


@pytest_asyncio.fixture
async def add_comments(add_posts, test_db):
    item = {"user_id": 2, "text": "Lalalalalcomment", "post_id": 1}
    db_item = Comment(**item)
    test_db.add(db_item)

    item = {"user_id": 2, "text": "LalalalaPOMPOMlcomment", "post_id": 2}
    db_item2 = Comment(**item)
    test_db.add(db_item2)

    await test_db.commit()
    await test_db.refresh(db_item)
    await test_db.refresh(db_item2)
    return db_item, db_item2


@pytest.mark.asyncio
async def test_block_user(add_users, auth_client, admin_client, test_db):
    response = await auth_client.post(
        "/login",
        json={"email": "pa@mail.ru", "password": "12345"}
    )
    data = response.json()
    token = data["access_token"]

    response = await admin_client.post(
        "/block-user",
        headers={
            "Authorization": f"Bearer {token}"
        },
        json={
            'user_id': 2,
        }
    )
    assert response.status_code == 200

    result = await test_db.execute(select(User).where(
        User.id == 2
    ))
    result = result.scalars().all()

    assert len(result) == 1
    assert result[0].blocked == True


@pytest.mark.asyncio
async def test_remove_user(add_users, auth_client, admin_client, test_db):
    response = await auth_client.post(
        "/login",
        json={"email": "pa@mail.ru", "password": "12345"}
    )
    data = response.json()
    token = data["access_token"]

    response = await admin_client.post(
        "/delete-user",
        headers={
            "Authorization": f"Bearer {token}"
        },
        json={
            'user_id': 2,
        }
    )
    assert response.status_code == 200

    result = await test_db.execute(select(User).where(
        User.id == 2
    ))
    result = result.scalars().all()

    assert len(result) == 0


@pytest.mark.asyncio
async def test_verify_post(add_posts, auth_client, admin_client, test_db):
    response = await auth_client.post(
        "/login",
        json={"email": "pa@mail.ru", "password": "12345"}
    )
    data = response.json()
    token = data["access_token"]

    response = await admin_client.post(
        "/verification-post",
        headers={
            "Authorization": f"Bearer {token}"
        },
        json={
            'post_id': 1
        }
    )
    assert response.status_code == 200

    result = await test_db.execute(select(Post).where(
        Post.id == 1
    ))
    result = result.scalars().all()

    assert len(result) == 1
    assert result[0].verified == True


@pytest.mark.asyncio
async def test_verify_comment(add_comments, auth_client, admin_client, test_db):
    response = await auth_client.post(
        "/login",
        json={"email": "pa@mail.ru", "password": "12345"}
    )
    data = response.json()
    token = data["access_token"]

    response = await admin_client.post(
        "/verification-comment",
        headers={
            "Authorization": f"Bearer {token}"
        },
        json={
            'comment_id': 1
        }
    )
    assert response.status_code == 200

    result = await test_db.execute(select(Comment).where(
        Comment.id == 1
    ))
    result = result.scalars().all()

    assert len(result) == 1
    assert result[0].verified == True


@pytest.mark.asyncio
async def test_send_feedback(add_users, auth_client, admin_client, test_db):
    response = await auth_client.post(
        "/login",
        json={"email": "pa@mail.ru", "password": "12345"}
    )
    data = response.json()
    token = data["access_token"]

    response = await admin_client.post(
        "/send-feedback",
        headers={
            "Authorization": f"Bearer {token}"
        },
        json={
            'text': 'feedback test'
        }
    )
    assert response.status_code == 200

    result = await test_db.execute(select(Feedback).where(
        Feedback.id == 1
    ))
    result = result.scalars().all()

    assert len(result) == 1
    assert result[0].text == 'feedback test'


@pytest.mark.asyncio
async def test_send_complaint(add_users, auth_client, admin_client, test_db):
    response = await auth_client.post(
        "/login",
        json={"email": "pa@mail.ru", "password": "12345"}
    )
    data = response.json()
    token = data["access_token"]

    response = await admin_client.post(
        "/send-complaint",
        headers={
            "Authorization": f"Bearer {token}"
        },
        json={
            'user_id': 2,
            'text': 'complaint test'
        }
    )
    assert response.status_code == 200

    result = await test_db.execute(select(Complaint).where(
        Complaint.id == 1
    ))
    result = result.scalars().all()

    assert len(result) == 1
    assert result[0].text == 'complaint test'
    assert result[0].user_id == 2
