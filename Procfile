# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# This file is used to deploy the website to Heroku
#
# See here for more:
# https://devcenter.heroku.com/articles/procfile
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

release: flask db migrate & flask clear-cache
web: gunicorn -c gunicorn_conf.py "app.main:create_app()"
worker: flask celery worker
