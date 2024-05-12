FROM python:3.8

MAINTAINER Daniel Reeves "xdanielreeves@gmail.com"

WORKDIR /

ADD --chmod=755 https://astral.sh/uv/install.sh /install.sh
RUN /install.sh && rm /install.sh

COPY requirements.txt app/requirements.txt
RUN /root/.cargo/bin/uv pip install --system --no-cache -r app/requirements.txt

COPY ./ /home/
WORKDIR /home/

ENV PYTHONPATH=/home
EXPOSE 80

CMD ["gunicorn", \
    "-c", "gunicorn_conf.py", \
    "app.main:create_app()"]
