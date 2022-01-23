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
import subprocess
from typing import Optional

import pandas as pd
from flask import current_app

from flask_sqlalchemy import SQLAlchemy
from flask_postgres import init_db_callback
from sqlalchemy.exc import ResourceClosedError


db = SQLAlchemy()


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
    located at `app/data/queries`.

    Args:
        file_name: (str) A file name inside the `QUERIES_DIR` directory. It
                   should be only the file name alone and not the full path.

    Returns:
        Either a Pandas Dataframe the selected data for read queries, or None
        for write queries.
    """
    path = os.path.join(current_app.config['QUERIES_DIR'], file_name)
    with current_app.open_resource(path) as f:
        s = f.read().decode('utf8')
        return execute_sql(s)


@init_db_callback
def init_db():
    import alembic.config
    alembic.config.main(['upgrade', 'head'])

    execute_sql_from_file('define_reach.sql')
    execute_sql_from_file('define_boathouse.sql')
    execute_sql_from_file('define_default_options.sql')

    # Now update the database
    from app.data.processing.core import update_db
    update_db()


def get_current_time() -> pd.Timestamp:
    return (
        pd.Timestamp('now', tz='UTC')
        .tz_convert('US/Eastern')
        .tz_localize(None)
    )
