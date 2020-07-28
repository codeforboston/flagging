# Database Project In-depth Guide

We will be using PostgreSQL, a free, open-source database management system sucessor to UC Berkeley's Ingres Database but also support SQL language

**On OSX or Linux:**

We need to setup postgres database first thus enter into the bash terminals:

```
brew install postgresql
brew services start postgresql
```
Explanation: We will need to install postgresql in order to create our database. With postgresql installed, we can start up database locally or in our computer. We use `brew` from homebrew to install and start postgresql services. To get homebrew, consult with this link: https://brew.sh/

To  begin initialize a database, enter into the bash terminal: 

```shell script
export POSTGRES_PASSWORD=*enter_password_here*
createdb -U *enter_username_here* flagging
psql -U *enter_username_here* -d flagging -c "DROP USER IF EXISTS flagging; CREATE USER flagging SUPERUSER PASSWORD '${POSTGRES_PASSWORD}'"
```
Explanation: Postgres password can be any password you choose. We exported your chosen postgres password into `POSTGRES_PASSWORD`, an environment variable, which is a variable set outside a program and is independent in each session. Next, we created a database called `flagging` using a username/rolename, which needs to be a Superuser or having all accesses of postgres. By default, the Superuser rolename can be `postgres` or the username for you OS. To find out, you can go into psql terminal, which we will explain below, and enter `\du` to see all usernames. Finally, we add the database `flagging` using the env variable in which we save our password. 

You can see the results using the postgresql terminal which you can open by entering:
```
psql
```

Below are a couple of helpful commands you can use in the postgresql:

```
\q --to quit
\c *database_name* --to connect to database
\d --show what tables in current database
\du --show database users
\dt --show tables of current database
```

To run the website, in the project directory `flagging` enter:

```shell script
sh run_unix_dev.sh
```

Running the bash script `run_unix_dev.sh` found in the `flagging` folder. Inside the scirpt, it defines environment variables `FLASK_APP` and `FLASK_ENV` which we need to find app.py. We also export the user input for offline mode, vault password, and postgres password for validation. Finally we initialize a database with a custom flask command `flask init-db` and finally run the flask application `flask run`.

Regarding in how flask application connects to postgresql, `database.py` creates an object  `db = SQLAlchemy()` which we will refer again in `app.py` to configure the flask application to support postgressql `from .data import db` `db.init_app(app)`. (We can import the `db` object beecause `__init__.py` make the object available as a global variable) 

Flask supports creating custom commands `init-db` for initializing database and `update-db` for updating database. `init-db` command calls `init_db` function from `database.py` and essentially calls `execute_sql()` which executes the sql file `schema.sql` that creates all the tables. Then calls `update_database()` which fills the database with data from usgs, hobolink, etc. `update-db` command primarily just udpates the table thus does not create new tables. Note: currently we are creating and deleting the database everytime the bashscript and program runs. 