import pandas as pd
from flask import Blueprint
from flask import render_template
from flask import request
from flask_restful import Resource, Api

from ..data.hobolink import get_live_hobolink_data
from ..data.usgs import get_live_usgs_data
from ..data.model import process_data
from ..data.model import reach_2_model
from ..data.model import reach_3_model
from ..data.model import reach_4_model
from ..data.model import reach_5_model
from ..data.model import latest_model_outputs


bp = Blueprint('flagging', __name__)
api = Api(bp)


def get_data() -> pd.DataFrame:
    """Retrieves the data that gets plugged into the the model."""
    df_hobolink = get_live_hobolink_data('code_for_boston_export_21d')
    df_usgs = get_live_usgs_data()
    df = process_data(df_hobolink, df_usgs)
    return df


def stylize_model_output(df: pd.DataFrame) -> str:
    """
    This function function stylizes the dataframe that we will output for our
    web page. This function replaces the bools with colorized values, and then
    returns the HTML of the table excluding the index.

    Args:
        df: (pd.DataFrame) Pandas Dataframe containing model outputs.

    Returns:
        HTML table.
    """
    def _apply_flag(x: bool) -> str:
        flag_class = 'blue-flag' if x else 'red-flag'
        return f'<span class="{flag_class}">{x}</span>'

    df['safe'] = df['safe'].apply(_apply_flag)
    df.columns = [i.title().replace('_', ' ') for i in df.columns]

    return df.to_html(index=False, escape=False)


def add_to_dict(models, df, reach) -> None:
    """
    Iterates through dataframe from model output, adds to model dict where
    key equals column name, value equals column values as list type

    args:
        models: dictionary
        df: pd.DataFrame
        reach:int

    returns: None
        """
    # converts time column to type string because of conversion to json error
    df['time'] = df['time'].astype(str)
    models[f'model_{reach}'] = df.to_dict(orient='list')


@bp.route('/')
def index() -> str:
    """
    Retrieves data from database, 
    then displays data on `index_model.html`     

    returns: render model on index.html
    """
    
    df = latest_model_outputs()
    
    print('\n\nlatest_model_outputs:\n\n')
    print( latest_model_outputs(48) )
    print('\n\n')

    df = df.set_index('reach')
    flags = {
        key: val['safe']
        for key, val
        in df.to_dict(orient='index').items()
    }
    return render_template('index.html', flags=flags)


@bp.route('/about')
def about() -> str:
    return render_template('about.html')


@bp.route('/output_model', methods=['GET'])
def output_model() -> str:
    """
    Retrieves data from hobolink and usgs and processes data and then
    displays data on 'output_model.html'

    args: no argument

    returns: render model on output_model.html
    """

    # Parse contents of the query string to get reach and hours parameters.
    # Defaults are hours = 24, and reach = -1.
    # When reach = -1, we utilize all reaches.
    try:
        reach = int(request.args.get('reach'))
    except (TypeError, ValueError):
        reach = -1

    try:
        hours = int(request.args.get('hours'))
    except (TypeError, ValueError):
        hours = 24

    # Look at no more than 72 hours.
    hours = min(max(hours, 1), 72)

    df = latest_model_outputs(hours)

    # reach_html_tables is a dict where the index is the reach number
    # and the values are HTML code for the table of data to display for
    # that particular reach
    reach_html_tables = {}

    # loop through each reach in df
    #    extract the subset from the df for that reach
    #    then convert that df subset to HTML code
    #    and then add that HTML subset to reach_html_tables
    for i in df.reach.unique():
        reach_html_tables[i] = stylize_model_output(  df.loc[df['reach'] == i ]  )
    
    return render_template('output_model.html', tables=reach_html_tables)


class ReachApi(Resource):

    def model_api(self) -> dict:
        """
        Class method that retrieves data from hobolink and usgs and processes
        data, then creates json-like dictionary structure for model output.

        returns: json-like dictionary
        """
        df = get_data()

        dfs = {
            2: reach_2_model(df),
            3: reach_3_model(df),
            4: reach_4_model(df),
            5: reach_5_model(df)
        }

        main = {}
        models = {}

        # adds metadata
        main['version'] = '2020'
        main['time_returned'] = str(pd.to_datetime('today'))

        for reach, df in dfs.items():
            add_to_dict(models, df, reach)

        # adds models dict to main dict
        main['models'] = models

        return main

    def get(self):
        return self.model_api()


api.add_resource(ReachApi, '/api/v1/model')