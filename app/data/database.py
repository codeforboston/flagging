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
from flask import current_app
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import text
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
    with db.session() as conn:
        res = conn.execute(text(query))
        try:
            df = pd.DataFrame(res.fetchall(), columns=res.keys())
            return df
        except ResourceClosedError:
            conn.commit()


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
    path = os.path.join(current_app.config["QUERIES_DIR"], file_name)
    with current_app.open_resource(path) as f:
        s = f.read().decode("utf8")
        return execute_sql(s)
