#!/bin/bash
set -e

python3 /wait_postgres.py

gunicorn -w1 -b0.0.0.0:80 --worker-class=aiohttp.GunicornWebWorker app:get_app
