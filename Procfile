# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# This file is used to deploy the website to Heroku
#
# See here for more:
# https://devcenter.heroku.com/articles/procfile
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

web: gunicorn \
    --worker-class="egg:meinheld#gunicorn_worker" \
    "flagging_site:create_app('production')"
