# Data

Here is a "TLDR" of the data engineering for this website:

- To get data, we ping two different APIs, combine the responses from those API requests, do some processing and feature engineering of the data, and then run a predictive model on the processed data.

- To store the data and then later retrieve it for the front-end of the website, we use PostgreSQL database.

- To actually run the functionality that gets data, processes it, and stores it. we run a [scheduled job](https://en.wikipedia.org/wiki/Job_scheduler) that runs the command `flask update-db` at a set time intervals.

## Sources

There are two sources of data for our website:

1. An API hosted by the USGS National Water Information System API that's hooked up to a Waltham based stream gauge (herein "USGS" data);
2. An API for a HOBOlink RX3000 Remote Monitoring Station device stationed on the Charles River (herein "HOBOlink").

### USGS 

The code for retrieving and processing the HOBOlink data is in `flagging_site/data/usgs.py`.

The USGS API very is straightforward. It's a very typical REST API that takes "GET" requests and return well-formatted json data. Our preprocessing of the USGS API consists of parsing the JSON into a Pandas dataframe.

The data returned by the USGS API is in 15 minute increments, and it measures the stream flow (cubic feet per second) of the Charles River out in Waltham.

### HOBOlink

The code for retrieving and processing the HOBOlink data is in `flagging_site/data/hobolink.py`.

The HOBOlink device captures various information about the Charles River at the location it's stationed:

- Air temperature
- Water temperature
- Wind speed
- Photosynthetically active radiation (i.e. sunlight)
- Rainfall

The HOBOlink data is accessed through a REST API using some credentials stored in the `vault.zip` file.

The data actually returned by the API is a combination of a yaml file with a CSV below it, and we just use the CSV part. We then do the following to preprocess the CSV:

- We remove all timestamps ending `:05`, `:15`, `:25`, `:35`, `:45`, and `:55`. These only contain battery information, not weather information. The final dataframe returned is ultimately in 10 minute incremenets.
- We make the timestamp consistently report eastern standard times. There is a weird issue in which the HOBOlink API returns slightly different datetime formats that messes with Pandas's timestamp parser. We are able to coerce the timestamp into something consistent and predictable.
- We consolidate duplicative columns. The HOBOlink API has a weird issue where sometimes it splits columns of data with the same name, seemingly at random. This issue causes serious data issues if untreated (at one point, it caused our model to fail to update for a couple days), so our function cleans the data.

As you can see from the above, the HOBOlink API is a bit finicky for whatever reason, but we have a good data processing solution for these problems.

The HOBOlink data is also notoriously slow to retrieve (regardless of whether you ask for 1 hour of data or multiple weeks of data), which is why we belabored building the database portion of the flagging website out in the first place.

???+ tip
    You can manually download the latest raw data from this device [here](https://www.hobolink.com/p/0cdac4a6910cef5a8883deb005d73ae1). If you want some preprocessed data that implements the above modifications to the output, there is a better way to get that data explained in the shell guide.

### Combining the data

Additional information related to combining the data and how the models work is in the [Predictive Models](../predictive_models) page.

## Postgres Database

PostgresSQL is a free, open-source database management system, and it's what our website uses to store data.

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