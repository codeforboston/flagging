FROM python:3.12-slim
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

WORKDIR /app
ENV UV_PROJECT_ENVIRONMENT=/usr/local

RUN --mount=type=cache,target=/root/.cache/uv \
    --mount=type=bind,source=requirements.txt,target=requirements.txt \
    uv pip install -r requirements.txt --compile-bytecode --system

COPY . /app

EXPOSE 80 443

CMD ["bash", "-c", "flask db migrate && gunicorn -c gunicorn_conf.py app.main:create_app\\(\\)"]
