# Development - Overview

The Development guide is aimed at users who wish to understand the code base and make changes to it if need be.

This overview page describes at a high-level what the website's infrastructure is, how it all relates, and why those things are in the app.

!!! tip
    Make sure to go through the [setup guide](../setup) before doing anything in the development guide.

## Dependency Diagram

```mermaid
classDiagram
class Twitter Bot
Twitter Bot : /twitter.py
Heroku Task Scheduler ..> Twitter Bot
Heroku Task Scheduler ..> PostgreSQL
Heroku <.. gunicorn
gunicorn <.. Flask : create_app()
gunicorn : /../Procfile
Heroku <.. PostgreSQL
class Flask
Flask : /app.py
class Swagger
Swagger : /app.py
Flask <.. Swagger : init_swagger(app)
Swagger ..> blueprints : wraps RESTful API
class SQLAlchemy
SQLAlchemy : /data/database.py
class Jinja2
Jinja2 : /app.py
Flask <.. Jinja2
SQLAlchemy <.. PostgreSQL: Connected via psycopg2
Flask <.. SQLAlchemy : db.init_app(app)
class blueprints
blueprints : blueprints/flagging.py
blueprints : blueprints/api.py
Flask <.. blueprints
Jinja2 <.. blueprints : Renders HTML
class Admin
Admin : /admin.py
SQLAlchemy <.. Admin
Flask <.. Admin : init_admin(app)
class BasicAuth
BasicAuth : /admin.py
BasicAuth ..> Admin
Heroku .. Heroku Task Scheduler
```
