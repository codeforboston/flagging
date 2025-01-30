# Flask Shell Documentation

The shell is used to access app functions and data, such as Hobolink and USGS  data and access to the database.

The reason why the shell is useful is because there may be cases where you want to play around with the app's functions. For example, maybe you see something that seems fishy in the data, so you want to have direct access to the function the website is running.

The way Flask works makes it impossible to run the website's functions outside the Flask app context, which means importing the functions into a naked shell doesn't work as intended. The `flask shell` provides all the tools needed to let coders access the functions the exact same way the website does, except in a shell environment.

## Run the Shell

You can run the shell locally, but it is strongly recommended to do it in Docker Compose instead.

If the Docker Compose is not running, you can spin it up and run it like so:

```shell
docker compose run web flask shell
```

If you'd like to leave the website running in the background, or you already have it running in another terminal, use `exec` instead of `run`:

```shell
docker compose up -d
docker compose exec web flask shell
```

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
- **`process_data`** (*(pd.DataFrame, pd.DataFrame, pd.DataFrame) -> pd.DataFrame*):
  Combines the Hobolink and USGS tables.
- **`compose_tweet`** (*() -> str*):
  Generates a message for Twitter that represents the current status of the flagging program (note: this function does not actually send the Tweet to Twitter.com).

Additionally, Pandas and Numpy are already pre-imported via `#!python import pandas as pd` and `#!python import numpy as np`.

???+ tip
    To add more functions and variables that pre-load in the Flask shell, simply add another entry to the dictionary returned by the function `#!python make_shell_context()` in `app/app.py:creat_app()`.

???+ tip
    All of the website's functions can be run in the Flask shell, even those that are not pre-loaded in the shell's global context. All you need to do is import it. For example, let's say you want to get the un-parsed request object from USGS.gov. You can import the function we use and run it like this:

    ```python
    # (in Flask shell)
    from app.data.usgs import request_to_usgs
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

## Example 2: Preview Tweet

Let's say you want to preview a Tweet that would be sent out without actually sending it. The `compose_tweet()` function returns a string of this message:

```python
# (in Flask shell)
print(compose_tweet())
```

## Example 3: Manual load

I had to run this once because we missed the 90 day cutoff. This uses a different API endpoint, but it returns the same data and seems to work fine.

```python
import requests
from app.data.processing.hobolink import get_live_hobolink_data
from app.data.processing.predictive_models import v1
from app.data.processing.usgs import parse_usgs_data

begin_date = "2023-01-02"
end_date = "2023-11-09"

# Usgs request
res_w = requests.get("https://nwis.waterdata.usgs.gov/usa/nwis/uv/", params={"cb_00060": "on", "cb_00065": "on", "format": "rdb", "site_no": "01104500", "legacy": "1", "period": "", "begin_date": begin_date, "end_date": end_date})
res_b = requests.get("https://nwis.waterdata.usgs.gov/usa/nwis/uv/", params={"cb_00045": "off", "cb_00065": "on", "format": "rdb", "site_no": "01104683", "legacy": "1", "period": "", "begin_date": begin_date, "end_date": end_date})

df_hobolink = get_live_hobolink_data("code_for_boston_export_180d")
df_usgs_w = parse_usgs_data(res_w)
df_usgs_b = parse_usgs_data(res_b)
df_combined = v1.process_data(df_hobolink=df_hobolink, df_usgs_w=df_usgs_w, df_usgs_b=df_usgs_b)
df_predictions = v1.all_models(df_combined)

df_hobolink.to_csv(f"{end_date}-hobolink.csv")
df_usgs_w.to_csv(f"{end_date}-usgs_w.csv")
df_usgs_b.to_csv(f"{end_date}-usgs_b.csv")
df_combined.to_csv(f"{end_date}-combined.csv")
df_predictions.to_csv(f"{end_date}-predictions.csv")
```
