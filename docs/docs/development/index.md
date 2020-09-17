# Development - Overview

The Development guide is aimed at users who wish to understand the code base and make changes to it if need be.

This overview page describes at a high-level what the website's infrastructure is, how it all relates, and why those things are in the app.

!!! tip
    Make sure to go through the [setup guide](../../setup) before doing anything in the development guide.

## Dependency Diagram

```mermaid
classDiagram
Heroku <.. gunicorn
gunicorn <.. Flask : create_app()
gunicorn : /../Procfile
Heroku <.. PostgreSQL
class Flask
Flask : /app.py
Flask : create_app()
Flask : app = Flask(...)
class Config
Config : /config.py
Config : config = get_config_from_env(...)
class vault
vault : /vault.zip
vault : /app.py
Config <.. vault : update_config_from_vault(app)
class Swagger
Swagger : /app.py
Swagger : Swagger(app, ...)
Flask <.. Swagger : init_swagger(app)
Swagger ..> blueprints : wraps RESTful API
Flask <.. Config : app.config.from_object(config)
class SQLAlchemy
SQLAlchemy : /data/database.py
SQLAlchemy : db = SqlAlchemy()
class Jinja2
Jinja2 : /app.py
Flask <.. Jinja2 : Built-in Flask
SQLAlchemy <.. PostgreSQL: Connected via psycopg2
Flask <.. SQLAlchemy : db.init_app(app)
class blueprints
blueprints : blueprints/flagging.py
blueprints : blueprints/api.py
blueprints : app.register_blueprint(...)
Flask <.. blueprints
Jinja2 <.. blueprints : Renders HTML
class Admin
Admin : /admin.py
Admin: admin = Admin(...)
SQLAlchemy <.. Admin
Flask <.. Admin : init_admin(app)
class BasicAuth
BasicAuth : /auth.py
BasicAuth : auth = BasicAuth()
BasicAuth ..> Admin : init_auth(app)
```
