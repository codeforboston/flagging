FROM python:3.12

ADD --chmod=755 https://astral.sh/uv/install.sh /install.sh
RUN /install.sh && rm /install.sh

WORKDIR /app
COPY requirements.txt ./requirements.txt

RUN /root/.cargo/bin/uv sync --system --no-cache

COPY ./ .

EXPOSE 80

CMD ["bash", "-c", "flask db migrate && gunicorn -c gunicorn_conf.py app.main:create_app\\(\\)"]
