# Predictive Models

The Flagging Website is basically just a deployed predictive model, so in a sense this document covers the real core of the code base. This page explains the models and the data transformations that occur from the original data. At the bottom, there are some notes on how to change the model coefficients and rerun the website with new coefficients.

The predictive models are stored in the file `/flagging_site/data/models.py`. These models are run as part of the `update-db` command. The input for the models are a combination of the HOBOlink and USGS data with some transformations of the data. The outputs are stored in the SQL table named `model_outputs`.

???+ tip
    There is a fair bit of Pandas in this document and it may be intimidating. However, if you only want to change the model's coefficients and nothing more, you won't need to touch the Pandas directly.

## Data Transformations

The model combines data from the HOBOlink device and USGS. These two data sources are run through the function `process_data()`, in which the data is aggregated to hourly intervals (USGS is every 15 minutes and HOBOlink is every 10 minutes).

Once the data sources are aligned, additional feature transformations are performed such as rolling averages, rolling sums, and a measure of when the last significant rainfall was.

The feature transformations the CRWA uses depends on the year of the model, so by the time you may be reading this, this information may be outdated. Previous versions included rolling average wind speeds and air/water temperatures over 24 hours. The current version of the model (as of 2020) calculates the following:

- Rolling 24 hours of the PAR (photosynthetically active radiation) and the stream flow (cubic feet per second).
- Rolling sum of rainfall over the following intervals: 0-24h, 0-48h, and 24-48h.
- The numbers of days since the last "significant rainfall," where significant rain is defined as when the rolling sum of the last 24 hours of rainfall is at least 0.20 inches.

???+ tip
    If you look at the code, you'll see a lot of stuff like `#!python rolling(24)`. The reason `rolling` works is because the dataframe is sorted already by timestamp at that point by `#!python df = df.sort_values('time')`.

???+ note
    We use 28 days of HOBOlink data to process the model. For most features, we only need the last 48 hours worth of data to calculate the most recent value, however the last significant rainfall feature requires a lot of historic data because it is not technically bounded or transformed otherwise. This means that even when calculating 1 row of output data, i.e. the latest hour of data, we still need 28 days.
    
    In the deployed model, if we do not see any significant rainfall in the last 28 days, we return the difference between the timestamp and the earliest time in the dataframe, `#!python df['time'].min()`. In this scenario, the data will no longer be temporally consistent: a calculation right now will have `28.0` for `'days_since_sig_rain'`, but 12 hours from now it will be 27.5. This is fine though because the model will basically never predict E. coli blooms with 28+ days since significant rain, even when the data is not censored.
    
    Unfortunately there's no pretty way to implement `days_since_sig_rain`, so the Pandas code that does all of this is one of the more inscrutable parts of the codebase. Note that `'last_sig_rain'` is calculating the timestamp of the last significant rain, and `'days_since_sig_rain'` calculates the time delta and translates into days:
    
    ```python
    df['sig_rain'] = df['rain_0_to_24h_sum'] >= SIGNIFICANT_RAIN
    df['last_sig_rain'] = (
        df['time']
        .where(df['sig_rain'])
        .ffill()
        .fillna(df['time'].min())
    )
    df['days_since_sig_rain'] = (
        (df['time'] - df['last_sig_rain']).dt.seconds / 60 / 60 / 24
    )
    ```

## Model Overviews

Each model function defined in `models.py` is formatted like this:

1. Take the last few rows of the input dataframe (I discuss what the input dataframe is later on this page). Each row is an hour of data on the condition of the Charles River and its surrounding environment, so for example, taking the last 24 rows is equivalent to taking the last 24 hours of data.
2. Predict the probability of the water being unsafe using a logistic regression fit, with the coefficients in the log odds form (so the dot product of the parameters and the data returns a predicted log odds of the target variable).
3. To get the probability of a log odds, we run it through a logistic function (`sigmoid()`, defined at the top of `models.py`).
4. We check whether the function is above or below the target threshold for safety, defined by `SAFETY_THRESHOLD`.
5. Lastly, we return a dataframe with 5 columns of data: `'reach'`, `'time'`, `'log_odds'` (step 2), `'probability'` (step 3), and `'safe'` (step 4). Each row in output corresponds to a row of input data.

Here is an example function. It should be pretty easy to track the steps outlined above with the code below.

```python
def reach_3_model(df: pd.DataFrame, rows: int = 48) -> pd.DataFrame:
    """
    a- rainfall sum 0-24 hrs
    b- rainfall sum 24-48 hr
    d- Days since last rain
    0.267*a + 0.1681*b - 0.02855*d  + 0.5157

    Args:
        df: (pd.DataFrame) Input data from `process_data()`
        rows: (int) Number of rows to return.

    Returns:
        Outputs for model as a dataframe.
    """
    df = df.tail(n=rows).copy()

    df['log_odds'] = (
        0.5157
        + 0.267 * df['rain_0_to_24h_sum']
        + 0.1681 * df['rain_24_to_48h_sum']
        - 0.02855 * df['days_since_sig_rain']
    )
    
    df['probability'] = sigmoid(df['log_odds'])
    df['safe'] = df['probability'] <= SAFETY_THRESHOLD
    df['reach'] = 3
    
    return df[['reach', 'time', 'log_odds', 'probability', 'safe']]
```

## Editing the Models

???+ note

    This section covers making changes to the following:
    
    - The coefficients for the models.
    - The safety threshold.
    - The model features.
    
    If you want to do anything more complicated, such as adding a new source of information to the model, that is outside the scope of this document. To accomplish that, you'll need to do more sleuthing into the code to really understand it.

???+ note
    Making any changes covered in this section is relatively easy, but you'll still need to actually deploy the changes to Heroku if you want them to be on the live site. Read the [deployment guide](../../deployment) for more.

### Model coefficients

As covered in the last section, each model's coefficients are represented as log odds ratios. Don't be confused by this statement though: this is how logistic regression is represented in all statistical software packages-- `Logit` in Python's Statsmodels, `logit` in Stata, and `glm` in R-- since that's what's being calculated mathematically when a logistic regression is calculated. I only emphasize this to point out that to get a probability, the final log odds needs to be logistically transformed (which is done via the `sigmoid()` function) after the linear terms are summed up.

The code representing the logistic model prediction was organized for maximum legibility: the first number is the constant term, and the remaining coefficients are aligned next to the column name. Note the final coefficient in this particular example is a negative coefficient and is thus subtracted.

```python
df['log_odds'] = (
    0.5157
    + 0.267 * df['rain_0_to_24h_sum']
    + 0.1681 * df['rain_24_to_48h_sum']
    - 0.02855 * df['days_since_sig_rain']
)
```

Changing the coefficients is as simple as just changing one of those numbers next to its respective column name, inside of its respective model for any particular reach.

### Safety threshold

The safety threshold is defined near the top of the document:

```python
SAFETY_THRESHOLD = 0.65
```

This represents a 65% threshold for whether or not we consider the water safe or not. The `SAFETY_THRESHOLD` value is just used as a placeholder/convenience for whatever the default threshold should be. You can always change this value to be lower or higher, and additionally you can replace `SAFETY_THRESHOLD` inside of a model function

???+ warning
    Hopefully this goes without saying, but if you are going to change the threshold, please have a good, scientifically and statistically justifiable reason for doing so!

### Feature transformations

Feature transformations occur in the `process_data()` function after the data has been aggregated by hour, merged, and sorted by timestamp.

If you want to add some feature transformations, my suggestion is you try to learn from existing examples and copy+paste with the necessary replacements. If you have a feature that can't be built from a copy+paste, that's where you'll possibly need to learn a bit of Pandas.
