# Development - Overview

The Development guide is aimed at users who wish to understand the code base and make changes to it if need be.

This overview page describes at a high-level what the website's infrastructure is, how it all relates, and why those things are in the app.

## Website System Design

```mermaid
classDiagram
class Twitter Bot
Twitter Bot : /twitter.py
Heroku Task Scheduler ..> PostgreSQL
Heroku <.. Gunicorn
Gunicorn .. Meinheld
Heroku .. Redis
SQLAlchemy ..> blueprints
Gunicorn <.. Flask : create_app()
Gunicorn : /../Procfile
Meinheld : /../Procfile
Heroku .. PostgreSQL
blueprints ..> FlaskCaching
class Flask
Flask : /app.py
class Swagger
Swagger : /app.py
Flask <.. Swagger
Swagger ..> blueprints
class SQLAlchemy
SQLAlchemy : /data/database.py
class Jinja2
Jinja2 : /app.py
Flask <.. Jinja2
class blueprints
blueprints : /blueprints/flagging.py
blueprints : /blueprints/api.py
Flask <.. blueprints
Jinja2 <.. blueprints
class Admin
Admin : /admin.py
class SQLAlchemy
PostgreSQL : (Heroku service)
SQLAlchemy <.. Admin
SQLAlchemy <.. PostgreSQL
Flask <.. Admin
class BasicAuth
BasicAuth : /admin.py
BasicAuth ..> Admin
class HerokuTaskScheduler
HerokuTaskScheduler : (Heroku service)
class Redis
Redis : (Heroku service)
Heroku .. Heroku Task Scheduler
FlaskCaching ..> Redis
class FlaskCaching
FlaskCaching: /data/database.py
Flask <.. SQLAlchemy
Predictive Models ..> PostgreSQL
Heroku Task Scheduler ..> Predictive Models
Heroku Task Scheduler ..> Twitter Bot
PostgreSQL ..> Twitter Bot
Predictive Models : /data/predictive_models.py
```

## Overview of repo

Sometimes it can be a little confusing and overwhelming seeing all the files strewn about in the root directory of the repo. I get it! Here are all the files (as of writing) and why they're there.

```
.
├── .flaskenv
├── .github
│   └── workflows
│       └── tests.yml
├── .gitignore
├── app.json
├── docs
│   ├── README.md
│   ├── mkdocs.yml
│   ├── site
│   └── src
├── app
│   └── ...
├── LICENSE
├── Procfile
├── pytest.ini
├── README.md
├── requirements
│   └── ...
├── requirements.txt
├── run_unix_dev.sh
├── run_windows_dev.bat
├── runtime.txt
└── tests
     └── ...
```

- `.flaskenv`: Helper file for Flask local deployment. ([more info](https://flask.palletsprojects.com/en/1.1.x/cli/#environment-variables-from-dotenv))
- `.github/workflows/tests.yml`: This file is handled by Github Actions. It runs the unit-tests. ([more info](https://docs.github.com/en/actions/learn-github-actions))
- `.gitignore`: Tells git what files to ignore. ([more info](https://git-scm.com/docs/gitignore))
- `app.json`: Used by Heroku to set up one-click deployment for the app. ([more info](https://devcenter.heroku.com/articles/app-json-schema))
- `docs`: Contains source code for the documentation. Rendered with Mkdocs. ([more info](https://www.mkdocs.org/))
- `app`: The actual code base for the flagging website.
- `LICENSE`: License that governs the project's code base.
- `Procfile`: Heroku uses this to know what to run on the deployed instance. ([more info](https://devcenter.heroku.com/articles/procfile))
- `pytest.ini`: Unit-testing configuration. When you run `python -m pytest ./tests`, this file is read in. We need it for some Pytest extensions, and to define a label we use to skip tests that require credentials. ([more info](https://docs.pytest.org/en/stable/customize.html))
- `README.md`: Self-explanatory.
- `requirements`: This folder contains the various environment configurations, e.g. local development needs different things than production, Windows needs different things than OS X, etc. ([more info](https://github.com/jazzband/pip-tools) and [more info](https://docs.python.org/3/tutorial/venv.html))
- `requirements.txt`: Heroku requires a `requirements.txt` in the root of the repo.
- `run_unix_dev.sh`: On OS X and Linux, you should run this to fire up the website locally.
- `run_windows_dev.sh`: On Windows, you should run this to fire up the website locally. This one is less maintained than the unix dev script, and may require minor manual editing to work.
- `runtime.txt`: Heroku requires this to define the runtime. ([more info](https://devcenter.heroku.com/articles/python-runtimes))
