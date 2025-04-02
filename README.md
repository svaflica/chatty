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
