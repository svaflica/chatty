import pytest
import pytest_asyncio
import base64

from auth.main import get_password_hash
from models import User


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


@pytest.mark.asyncio
async def test_register(auth_client):
    with open('tests/resources/1.png', 'rb') as f:
        photo = base64.b64encode(f.read()).decode('utf-8')

    response = await auth_client.post(
        "/register",
        json={"email": "pam@mail.ru", "password": "12345", "photo": photo}
    )
    assert response.status_code == 200

    data = response.json()

    assert "access_token" in data
    assert "token_type" in data
    assert data["token_type"] == "bearer"


@pytest.mark.asyncio
async def test_auth(auth_client, add_users):
    response = await auth_client.post(
        "/login",
        json={"email": "pa@mail.ru", "password": "12345"}
    )
    assert response.status_code == 200

    data = response.json()

    assert "access_token" in data
    assert "token_type" in data
    assert data["token_type"] == "bearer"

    response = await auth_client.post(
        "/login",
        json={"email": "pampampam@mail.ru", "password": "12345"}
    )
    assert response.status_code != 200

    response = await auth_client.post(
        "/login",
        json={"email": "pa@mail.ru", "password": "12345666"}
    )
    assert response.status_code != 200


@pytest.mark.asyncio
async def test_check_token(auth_client, add_users):
    response = await auth_client.post(
        "/login",
        json={"email": "pa@mail.ru", "password": "12345"}
    )
    assert response.status_code == 200

    data = response.json()
    token = data["access_token"]

    response = await auth_client.get(
        "/check_token",
        headers={
            "Authorization": f"Bearer {token}"
        }
    )
    assert response.status_code == 200

    token += "44444444"

    response = await auth_client.get(
        "/check_token",
        headers={
            "Authorization": f"Bearer {token}"
        }
    )
    assert response.status_code != 200


@pytest.mark.asyncio
async def test_new_password(auth_client, add_users):
    response = await auth_client.post(
        "/new_password",
        json={"email": "pa@mail.ru", "password": "123456666666"}
    )
    assert response.status_code == 200

    response = await auth_client.post(
        "/login",
        json={"email": "pa@mail.ru", "password": "12345"}
    )
    assert response.status_code != 200

    response = await auth_client.post(
        "/login",
        json={"email": "pa@mail.ru", "password": "123456666666"}
    )
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_check_users_me(auth_client, add_users):
    response = await auth_client.post(
        "/login",
        json={"email": "pa@mail.ru", "password": "12345"}
    )
    assert response.status_code == 200

    data = response.json()
    token = data["access_token"]

    response = await auth_client.get(
        "/users/me/",
    )
    assert response.status_code == 401

    response = await auth_client.get(
        "/users/me/",
        headers={
            "Authorization": f"Bearer {token}"
        }
    )
    assert response.status_code == 200

    data = response.json()

    assert data['email'] == 'pa@mail.ru'
