#!/bin/bash

python -m alembic upgrade heads
uvicorn --host 0.0.0.0 --port 8002 subscription.main:app
