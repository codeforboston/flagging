FROM python:3.12

MAINTAINER Daniel Reeves "xdanielreeves@gmail.com"

ADD --chmod=755 https://astral.sh/uv/install.sh /install.sh
RUN /install.sh && rm /install.sh

WORKDIR /app
COPY requirements.txt ./requirements.txt

RUN /root/.cargo/bin/uv pip install --system --no-cache -r requirements.txt

COPY ./ .

EXPOSE 80

CMD ["bash", "-c", "flask db migrate && gunicorn -c gunicorn_conf.py app.main:create_app\\(\\)"]
