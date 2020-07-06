"""
This file should handle all database connection stuff, namely: writing and
retrieving data.
"""

# using json to pull in credentials from a JSON-formatted text file
import json

import psycopg2 # adapter between Python and postgresql

# import click
# from flask import current_app
from flask import g
from flask.cli import with_appcontext
from flask import Flask
# from flask_sqlalchemy import SQLAlchemy

conn_string = None # store database connection string
app = Flask(__name__)
# db = SQLAlchemy(app)

# this reads the database credentials and constructs the
# string to connect to the database
def db_init_str():
    print('-------------------------------')
    print ("db_init_str has been called!\n") # TEST ONLY

    global conn_string

    if conn_string is not None:
        print("Whoops! The database string was already initialized.  It's shown below:")
        print(conn_string)
        return

    # get database credentials
    with open('db_creds.json', 'r') as f:
        creds = json.load(f)

    # create connection string for database
    conn_string = "host=" + creds['host'] + " port="+ str(creds['port_num']) \
        + " user=" + creds['user'] + " password=" + creds['password'] \
        + " dbname="  + creds['dbname']
        
        # this command could include the db name (below), but then we could't create db
        # + " dbname="  + creds['dbname']   

    # BELOW BLOCK IS  TEST ONLY
    print ('db_init_str connection string is:')
    print(conn_string)
    print()



# this function connects to the database and creates a cursor
def db_get():
    print('-------------------------------')
    print ("db_get has been called!\n") # TEST ONLY

    # only read database credentials if needed
    # note if d.b. credentials were to change in the future,
    # this wouldn't auto-magically detect that change
    if conn_string is None:
        db_init_str()

    with app.app_context():
        if "db" not in g: # set to cursor
            g.db = psycopg2.connect(conn_string).cursor()
            print("cursor created!\n")
        else:
            print("no cursor created\n")
        return g.db


# this function closes the database connection / cursor
def db_close():     # note: Flask sample code adds an unused parameter e
    print('-------------------------------')
    print ("db_close has been called!\n") # TEST ONLY

    with app.app_context():
        db = g.pop("db", None)
        if db is not None:
            db.close()
            print ("the database was closed\n")
        else:
            print ("the database was not closed\n")

# this function intializes the database
# (it connects via db_get and clears/creates the tables)
def db_init():
    print('-------------------------------')
    print ("db_init has been called!\n") # TEST ONLY

    db = db_get()

    sqlfile = open('schema.sql', 'r')
    db.execute(sqlfile.read())



