FROM python:3.8

# MAINTAINER Daniel Reeves "xdanielreeves@gmail.com"

WORKDIR /
COPY requirements.txt app/requirements.txt
RUN pip install --no-cache-dir -r app/requirements.txt

COPY ./ /home/
WORKDIR /home/

ENV PYTHONPATH=/home
EXPOSE 80

CMD ["gunicorn", \
    "-k", "egg:meinheld#gunicorn_worker", \
    "-c", "gunicorn_conf.py", \
    "app.main:create_app()"]
