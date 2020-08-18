# Flask Shell Documentation

The shell is used to access app functions and data, such as Hobolink and USGS
data and access to the database.

## Available Shell Functions and Variables

- `db` (*flask_sqlalchemy.SQLAlchemy*):
  The object used to interact with the Postgres database.
- `get_live_hobolink_data` (*(Optional[str]) -> pd.DataFrame*):
  Gets the Hobolink data table based on the given "export" name.
  See `flagging_site/data/hobolink.py` for details.
- `get_live_usgs_data` (*() -> pd.DataFrame*):
  Gets the USGS data table.
  See `flagging_site/data/usgs.py` for details.
- `get_data` (*() -> pd.DataFrame*):
  Gets the Hobolink and USGS data tables and returns a combined table.
- `process_data` (*(pd.DataFrame, pd.DataFrame) -> pd.DataFrame*):
  Combines the Hobolink and USGS tables.
  See `flagging_site/data/model.py` for details.

To add more functions and variables, simply add an entry to the dictionary
returned by the function `make_shell_context()` in `flagging_site/app.py:creat_app()`.

## Running the Shell

First, open up a terminal at the `flagging` folder.

Make sure you have Python 3 installed. Set up your environment with the following commands:

```shell
python3 -m venv venv
source venv/bin/activate
python3 -m pip install -r requirements.txt
```

Export the following environment variables like so:

```shell
export VAULT_PASSWORD=replace_me_with_pw
export FLASK_APP=flagging_site:create_app
export FLASK_ENV=development
```

Finally, start the Flask shell:

```shell
flask shell
```

And you should be good to go! The functions listed above should be available for use. See below for an example.

## Example: Export Hobolink Data to CSV

Here we assume you have already started the Flask shell.
This example shows how to download the Hobolink data and
save it as a CSV file.

```shell
>>> hobolink_data = get_live_hobolink_data()
>>> hobolink_data.to_csv('path/where/to/save/my-CSV-file.csv')
```