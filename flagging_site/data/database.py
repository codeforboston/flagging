"""
This file should handle all database connection stuff, namely: writing and
retrieving data.
"""
import os
import pandas as pd
import re
from typing import Optional
from flask import current_app
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.exc import ResourceClosedError
from psycopg2 import connect
from sqlalchemy import Column

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
    """If database doesn't exist, create it and return True, 
    otherwise leave it alone and return False"""

    # connect to postgres database, get cursor
    conn = connect(dbname='postgres', user=current_app.config['POSTGRES_USER'],
        host=current_app.config['POSTGRES_HOST'],
            password=current_app.config['POSTGRES_PASSWORD'])
    cursor = conn.cursor()

    # get a list of all databases:
    cursor.execute('SELECT datname FROM pg_database;')
    db_list =  cursor.fetchall()      # db_list here is a list of one-element tuples
    db_list = [d[0] for d in db_list] # this converts db_list to a list of db names

    # if that database is already there, exit out of this function
    if current_app.config['POSTGRES_DBNAME'] in db_list:
        return False
    # since the database isn't already there, proceed ...
    
    # create the database
    cursor.execute('COMMIT;')
    cursor.execute('CREATE DATABASE ' + current_app.config['POSTGRES_DBNAME'])
    cursor.execute('COMMIT;')

    return True


def init_db():
    """Clear existing data and create new tables."""
    with current_app.app_context():
        # Read the `schema.sql` file, which initializes the database.
        execute_sql_from_file('schema.sql')
        execute_sql_from_file('define_boathouse.sql')
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

class boathouses(db.Model):
    reach = Column(db.Integer, unique=False)
    boathouse = Column(db.String(255), primary_key=True)
    latitude = Column(db.Numeric, unique=False)
    longitude = Column(db.Numeric, unique=False)
    def __repr__(self):
        return '<Boathouse {}>'.format(self.boathouse)

def get_boathouse_dict():
    """
    Return a dict of boathouses
    """
    # return value is an outer dictionary with the reach number as the keys 
    # and the a sub-dict as the values each sub-dict has the string 'boathouses' 
    # as the key, and an array of boathouse names as the value
    boathouse_dict = {}
    
    # outer boathouse loop:  take one reach at a time
    for bh_out in boathouses.query.distinct(boathouses.reach):
        bh_list = []
        # inner boathouse loop:  get all boathouse names within 
        # the reach (the reach that was selected by outer loop)
        for bh_in in boathouses.query.filter(boathouses.reach == bh_out.reach).all():
            bh_list.append( bh_in.boathouse )

        boathouse_dict[ bh_out.reach ] = {'boathouses': bh_list}

    return boathouse_dict
