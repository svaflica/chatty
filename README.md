# chatty

## Запуск проекта

1. Создайте docker образ для сервиса auth ```docker build -t auth -f Dockerfile.auth .```
2. Создайте docker образ для сервиса post ```docker build -t post -f Dockerfile.post .```
3. Создайте docker образ для сервиса subscr ```docker build -t subscr -f Dockerfile.subscr .```
4. Создайте docker образ для сервиса admin ```docker build -t admin -f Dockerfile.admin .```
5. Запустите docker compose ```docker compose up```

## Запуск автотестов

1. Создайте docker образ для сервиса auth ```docker build -t auth -f Dockerfile.auth .```
2. Создайте docker образ для сервиса post ```docker build -t post -f Dockerfile.post .```
3. Создайте docker образ для сервиса subscr ```docker build -t subscr -f Dockerfile.subscr .```
4. Создайте docker образ для сервиса admin ```docker build -t admin -f Dockerfile.admin .```
5. Запустите docker compose ```docker compose up```
6. Создайте виртуальное окружение и установите зависимости из requirements.txt
7. Выполните команду ```pytest -v```

## Пример регистрации и получения токена доступа

```python
import requests
import base64

with open('photo.jpg', 'rb') as f:
    photo = base64.b64encode(f.read())

res = requests.post('http://localhost:8000/register', json={'email': 'a@mail.ru', 'password': 'password', 'photo': photo.decode('utf-8')})
token = res.json()['access_token']
```

## Пример регистрации через rabbit

```python
import asyncio
from faststream.rabbit import RabbitBroker

broker = RabbitBroker(f'amqp://rmuser:rmpassword@localhost:5672')

with open('photo.jpg', 'rb') as f:
    photo = base64.b64encode(f.read())

async def rm():
    await broker.connect()
    await broker.publish(
        {'message_id': 'register-1', 'email': 'a@mail.ru', 'password': 'password', 'photo': photo.decode('utf-8')},
        'event-auth',
        message_id='register-1'
    )

loop = asyncio.get_event_loop()
loop.create_task(rm())

```
