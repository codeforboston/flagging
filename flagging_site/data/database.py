"""
This file should handle all database connection stuff, namely: writing and
retrieving data.
"""
import os
import click
import psycopg2
import psycopg2.extensions

from flask import g
from flask import current_app
from flask import Flask

from ..config import ROOT_DIR
from flask_sqlalchemy import SQLAlchemy


SCHEMA_FILE = os.path.join(ROOT_DIR, 'data', 'schema.sql')
db = SQLAlchemy()


# # this function connects to the database and creates a cursor
# def db_get() -> SQLAlchemy:  # psycopg2.extensions.connection:
#     with current_app.app_context():
#         if 'db' not in g:
#
#             g.db = conn
#         return g.db


def close_db(e=None):
    """If this request connected to the database, close the
    connection.
    """
    db = g.pop('db', None)
    if db is not None:
        db.close()


def execute_sql(query: str):
    with db.engine.connect() as conn:
        return conn.execute(query)


def init_db():
    """Clear existing data and create new tables."""
    with current_app.app_context():

        # Read the `schema.sql` file, which initializes the database.
        with current_app.open_resource(SCHEMA_FILE) as f:
            schema = f.read().decode('utf8')

        # Run `schema.sql`
        execute_sql(schema)

        # Populate the `usgs` table.
        from .usgs import get_usgs_data
        df = get_usgs_data()
        df.to_sql('usgs', con=db.engine, index=False, if_exists='append')

        # Populate the `hobolink` table.
        from .hobolink import get_hobolink_data
        df = get_hobolink_data()
        df.to_sql('hobolink', con=db.engine, index=False, if_exists='append')
