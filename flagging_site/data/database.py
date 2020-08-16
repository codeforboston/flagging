"""
This file should handle all database connection stuff, namely: writing and
retrieving data.
"""
import os
import pandas as pd
from typing import Optional
from flask import current_app
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.exc import ResourceClosedError
from psycopg2 import connect

db = SQLAlchemy()


def execute_sql(query: str) -> Optional[pd.DataFrame]:
    """Execute arbitrary SQL in the database. This works for both read and write
    operations. If it is a write operation, it will return None; otherwise it
    returns a Pandas dataframe."""
    with db.engine.connect() as conn:
        res = conn.execute(query)
        try:
            df = pd.DataFrame(res.fetchall())
            df.columns = res.keys()
            return df
        except ResourceClosedError:
            return None


def execute_sql_from_file(file_name: str):
    path = os.path.join(current_app.config['QUERIES_DIR'], file_name)
    with current_app.open_resource(path) as f:
        return execute_sql(f.read().decode('utf8'))


def create_db():
    """If database doesn't exist, create it and a and return True, 
    otherwise leave it alone and return False"""

    # create local variables for database values in the config file:
    db_user = current_app.config['POSTGRES_USER']
    db_pswd = current_app.config['POSTGRES_PASSWORD']
    db_host = current_app.config['POSTGRES_HOST']
    db_port = current_app.config['POSTGRES_PORT']
    db_name = current_app.config['POSTGRES_DBNAME']

    # connect to postgres database, get cursor
    conn = connect(dbname='postgres', user='postgres', host=db_host, password=db_pswd)
    cursor = conn.cursor()

    # get a list of all databases:
    cursor.execute('SELECT datname FROM pg_database;')
    db_list =  cursor.fetchall()      # db_list here is a list of one-element tuples
    db_list = [d[0] for d in db_list] # this converts db_list to a list of db names

    # if that database is already there, exit out of this function
    if db_name in db_list:
        return False
    # since the database isn't already there, proceed ...
    
    # create the database
    cursor.execute('COMMIT;')
    cursor.execute('CREATE DATABASE ' + db_name)
    cursor.execute('COMMIT;')

    # ask the user for the password to use for the flagging user
    # (the user name will be the same as the database name, 
    # which is db_name, which is set in the config as POSTGRES_DBNAME)


    print('\n\n')
    print('original flagging password: ' + current_app.config['POSTGRES_PASSWORD'] )
    print('\n\n')
    print('original sqlalchemy_db_uri: ' + current_app.config['SQLALCHEMY_DATABASE_URI'] )

    # modify the password in the local variable and in the config file:
    db_pswd = 'shush'
    current_app.config['POSTGRES_PASSWORD'] = db_pswd
    current_app.config['SQLALCHEMY_DATABASE_URI'] = f'postgres://{db_user}:{db_pswd}@{db_host}:{db_port}/{db_name}'
    # change this, instead

    print('\n\n')
    print('modified flagging password: ' + current_app.config['POSTGRES_PASSWORD'] )
    print('\n\n')
    print('modified sqlalchemy_db_uri: ' + current_app.config['SQLALCHEMY_DATABASE_URI'] )
    print('\n\n')

    # create flagging user (same as db_name)
    cursor.execute("DROP USER IF EXISTS " + db_name + ";" )
    cursor.execute("COMMIT;")
    cursor.execute("CREATE USER " + db_name + " WITH SUPERUSER PASSWORD '" + db_pswd + "';")
    return True


def init_db():
    """Clear existing data and create new tables."""
    with current_app.app_context():

        # Read the `schema.sql` file, which initializes the database.
        execute_sql_from_file('schema.sql')

        update_database()


def update_database():
    """At the moment this overwrites the entire database. In the future we want
    this to simply update it.
    """

    options = {
        'con': db.engine,
        'index': False,
        'if_exists': 'replace'
    }

    # Populate the `usgs` table.
    from .usgs import get_live_usgs_data
    df_usgs = get_live_usgs_data()
    df_usgs.to_sql('usgs', **options)

    # Populate the `hobolink` table.
    from .hobolink import get_live_hobolink_data
    df_hobolink = get_live_hobolink_data('code_for_boston_export_21d')
    df_hobolink.to_sql('hobolink', **options)

    from .model import process_data
    df = process_data(df_hobolink=df_hobolink, df_usgs=df_usgs)
    df.to_sql('processed_data', **options)

    from .model import all_models
    model_outs = all_models(df)
    model_outs.to_sql('model_outputs', **options)
