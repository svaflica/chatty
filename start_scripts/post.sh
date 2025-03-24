#!/bin/bash

python -m alembic upgrade heads
uvicorn --host 0.0.0.0 --port 8001 post.main:app
