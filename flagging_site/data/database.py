"""This file handles all database stuff, i.e. writing and retrieving data to
the Postgres database. Note that of the functionality in this file is available
directly in the command line.

While the app is running, the database connection is managed by SQLAlchemy. The
`db` object defined near the top of the file is that connector, and is used
throughout both this file and other files in the code base. The `db` object is
connected to the actual database in the `create_app` function: the app instance
is passed in via `db.init_app(app)`, and the `db` object looks for the config
variable `SQLALCHEMY_DATABASE_URI`.
"""
import os
from typing import Optional

import pandas as pd
import psycopg2
import psycopg2.errors
import click
from flask import current_app
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.exc import ResourceClosedError
from psycopg2 import connect
from flask_caching import Cache


db = SQLAlchemy()
cache = Cache()


def execute_sql(query: str) -> Optional[pd.DataFrame]:
    """Execute arbitrary SQL in the database. This works for both read and
    write operations. If it is a write operation, it will return None;
    otherwise it returns a Pandas dataframe.

    Args:
        query: (str) A string that contains the contents of a SQL query.

    Returns:
        Either a Pandas Dataframe the selected data for read queries, or None
        for write queries.
    """
    with db.engine.connect() as conn:
        res = conn.execute(query)
        try:
            df = pd.DataFrame(
                res.fetchall(),
                columns=res.keys()
            )
            return df
        except ResourceClosedError:
            return None


def execute_sql_from_file(file_name: str) -> Optional[pd.DataFrame]:
    """Execute SQL from a file in the `QUERIES_DIR` directory, which should be
    located at `flagging_site/data/queries`.

    Args:
        file_name: (str) A file name inside the `QUERIES_DIR` directory. It
                   should be only the file name alone and not the full path.

    Returns:
        Either a Pandas Dataframe the selected data for read queries, or None
        for write queries.
    """
    path = os.path.join(current_app.config['QUERIES_DIR'], file_name)
    with current_app.open_resource(path) as f:
        return execute_sql(f.read().decode('utf8'))


def create_db(overwrite: bool = False) -> bool:
    """If the database defined by `POSTGRES_DBNAME` doesn't exist, create it
    and return True, otherwise do nothing and return False. By default, the
    config variable `POSTGRES_DBNAME` is set to "flagging".
    Returns:
        bool for whether the database needed to be created.
    """
    # connect to postgres database, get cursor
    conn = connect(
        user=current_app.config['POSTGRES_USER'],
        password=current_app.config['POSTGRES_PASSWORD'],
        host=current_app.config['POSTGRES_HOST'],
        port=current_app.config['POSTGRES_PORT'],
        dbname='postgres'
    )
    database = current_app.config['POSTGRES_DBNAME']
    cursor = conn.cursor()

    if overwrite:
        cursor.execute("SELECT bool_or(datname = 'flagging') FROM pg_database;")
        exists = cursor.fetchall()[0][0]
        if exists:
            cursor.execute('COMMIT;')
            cursor.execute(f'DROP DATABASE {database};')
            click.echo(f'Dropped database {database!r}.')

    try:
        cursor.execute('COMMIT;')
        cursor.execute(f'CREATE DATABASE {database};')
    except psycopg2.errors.lookup('42P04'):
        click.echo(f'Database {database!r} already exist.')
        return False
    else:
        click.echo(f'Created database {database!r}.')
        return True


def init_db():
    """This data clears and then populates the database from scratch. You only
    need to run this function once per instance of the database.
    """

    # This file drops the tables if they already exist, and then defines
    # the tables. This is the only query that CREATES tables.
    execute_sql_from_file('schema.sql')

    # The models available in Base are given corresponding tables if they
    # do not already exist.
    db.create_all(app=current_app)

    # The boathouses table is populated. This table doesn't change, so it
    # only needs to be populated once.
    execute_sql_from_file('define_boathouse.sql')

    # The file for keeping track of if it's currently boating season
    execute_sql_from_file('define_default_options.sql')

    # The function that updates the database periodically should be run after
    # this runs.


def update_database():
    """This function basically controls all of our data refreshes. The
    following tables are updated in order:

    - usgs
    - hobolink
    - processed_data
    - model_outputs

    The functions run to calculate the data are imported from other files
    within the data folder.
    """
    options = {
        'con': db.engine,
        'index': False,
        'if_exists': 'replace'
    }

    try:
        # Populate the `usgs` table.
        from .usgs import get_live_usgs_data
        df_usgs = get_live_usgs_data()
        df_usgs.to_sql('usgs', **options)

        # Populate the `hobolink` table.
        from .hobolink import get_live_hobolink_data
        df_hobolink = get_live_hobolink_data()
        df_hobolink.to_sql('hobolink', **options)

        # Populate the `processed_data` table.
        from .predictive_models import process_data
        df = process_data(df_hobolink=df_hobolink, df_usgs=df_usgs)
        df.to_sql('processed_data', **options)

        # Populate the `model_outputs` table.
        from .predictive_models import all_models
        model_outs = all_models(df)
        model_outs.to_sql('model_outputs', **options)

    finally:
        # Clear the cache every time this function runs.
        # the try -> finally makes sure this always runs, even if an error
        # occurs somewhere when updating.
        cache.clear()
