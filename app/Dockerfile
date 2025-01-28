FROM python:3-bookworm

EXPOSE 80

RUN pip install gunicorn

COPY requirements.txt /requirements.txt
RUN pip install -r requirements.txt

COPY docker-entrypoint.sh /docker-entrypoint.sh
COPY wait_postgres.py /wait_postgres.py
COPY app.py /app.py

ENV PYTHONUNBUFFERED 0

ENTRYPOINT ["sh", "-c", "/docker-entrypoint.sh"]
