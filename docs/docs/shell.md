# Flask Shell Documentation

The shell is used to access app functions and data, such as Hobolink and USGS
data and access to the database.

The reason why the shell is useful is because there may be cases where you want to play around with the app's functions. For example, maybe you see something that seems fishy in the data, so you want to have direct access to the function the website is running. You may also want to 

The way Flask works makes it impossible to run the website's functions outside the Flask app context, which means importing the functions into a naked shell doesn't work as intended. The `flask shell` provides all the tools needed to let coders access the functions the exact same way the website does, except in a shell environment.

## Available Shell Functions and Variables

- **`app`** (*flask.Flask*):
  The actual Flask app instance.
- **`db`** (*flask_sqlalchemy.SQLAlchemy*):
  The object used to interact with the Postgres database.
- **`get_live_hobolink_data`** (*(Optional[str]) -> pd.DataFrame*):
  Gets the HOBOlink data table based on the given "export" name.
- **`get_live_usgs_data`** (*() -> pd.DataFrame*):
  Gets the USGS data table.
- **`get_data`** (*() -> pd.DataFrame*):
  Gets the Hobolink and USGS data tables and returns a combined table.
- **`process_data`** (*(pd.DataFrame, pd.DataFrame) -> pd.DataFrame*):
  Combines the Hobolink and USGS tables.
- **`compose_tweet`** (*() -> str*):
  Generates a message for Twitter that represents the current status of the flagging program (note: this function does not actually send the Tweet to Twitter.com). 

Additionally, Pandas and Numpy are already pre-imported via `import pandas as pd` and `import numpy as np`.

???+ tip
    To add more functions and variables that pre-load in the Flask shell, simply add another entry to the dictionary returned by the function `make_shell_context()` in `flagging_site/app.py:creat_app()`.

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

```python
>>> hobolink_data = get_live_hobolink_data()
>>> hobolink_data.to_csv('path/where/to/save/my-CSV-file.csv')
```