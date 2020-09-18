# Flask Shell Documentation

The shell is used to access app functions and data, such as Hobolink and USGS
data and access to the database.

The reason why the shell is useful is because there may be cases where you want to play around with the app's functions. For example, maybe you see something that seems fishy in the data, so you want to have direct access to the function the website is running. You may also want to 

The way Flask works makes it impossible to run the website's functions outside the Flask app context, which means importing the functions into a naked shell doesn't work as intended. The `flask shell` provides all the tools needed to let coders access the functions the exact same way the website does, except in a shell environment.

## Run the Shell

1. Open up a terminal at the `flagging` folder.

2. Activate a Python virtual environment:

```shell
python3 -m venv venv
source venv/bin/activate
python3 -m pip install -r requirements.txt
```

3. Set up the `FLASK_ENV` environment variable:

```shell
export FLASK_ENV=development
```

4. Run the shell:

```shell
flask shell
```

And you should be good to go! The functions listed below should be available for use, and the section below contains some example use cases for the shell.

???+ tip
    To exit from the shell, type `exit()` then ++enter++.

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

Additionally, Pandas and Numpy are already pre-imported via `#!python import pandas as pd` and `#!python import numpy as np`.

???+ tip
    To add more functions and variables that pre-load in the Flask shell, simply add another entry to the dictionary returned by the function `#!python make_shell_context()` in `flagging_site/app.py:creat_app()`.
    
???+ tip
    All of the website's functions can be run in the Flask shell, even those that are not pre-loaded in the shell's global context. All you need to do is import it. For example, let's say you want to get the un-parsed request object from USGS.gov. You can import the function we use and run it like this:
    
    ```python
    # (in Flask shell)
    from flagging_site.data.usgs import request_to_usgs
    res = request_to_usgs()
    print(res.json())
    ```

## Example 1: Export Hobolink Data to CSV

Here we assume you have already started the Flask shell.
This example shows how to download the Hobolink data and
save it as a CSV file.

```python
# (in Flask shell)
hobolink_data = get_live_hobolink_data()
hobolink_data.to_csv('path/where/to/save/my-CSV-file.csv')
```

Downloading the data may be useful if you want to see 

## Example 2: Preview Tweet

Let's say you want to preview a Tweet that would be sent out without actually sending it. The `compose_tweet()` function returns a string of this message:

```python
# (in Flask shell)
print(compose_tweet())
```
