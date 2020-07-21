import pandas as pd
from flask import Blueprint
from flask import render_template
from flagging_site.data.hobolink import get_hobolink_data
from flagging_site.data.usgs import get_usgs_data
from flagging_site.data.model import process_data
from flagging_site.data.model import reach_2_model
from flagging_site.data.model import reach_3_model
from flagging_site.data.model import reach_4_model
from flagging_site.data.model import reach_5_model
from flask_restful import Resource, Api

from flask import request
from flasgger import swag_from

bp = Blueprint('flagging', __name__)
api = Api(bp)

def get_data() -> pd.DataFrame:
    """Retrieves the data that gets plugged into the the model."""
    df_hobolink = get_hobolink_data('code_for_boston_export_21d')
    df_usgs = get_usgs_data()
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
    Retrieves data from hobolink and usgs and processes data, then displays data 
    on `index_model.html`     

    returns: render model on index.html
    """
    df = get_data()
    flags = {
        2: reach_2_model(df, rows=1)['safe'].iloc[0],
        3: reach_3_model(df, rows=1)['safe'].iloc[0],
        4: reach_4_model(df, rows=1)['safe'].iloc[0],
        5: reach_5_model(df, rows=1)['safe'].iloc[0]
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

    df = get_data()

    reach_model_mapping = {
        2: reach_2_model,
        3: reach_3_model,
        4: reach_4_model,
        5: reach_5_model
    }
    
    if reach in reach_model_mapping:
        reach_func = reach_model_mapping[int(reach)]
        reach_html_tables = {
            reach: stylize_model_output(reach_func(df, rows=hours))
        }
    else:
        reach_html_tables = {
            reach: stylize_model_output(reach_func(df, rows=hours))
            for reach, reach_func
            in reach_model_mapping.items()
        }

    return render_template('output_model.html', tables=reach_html_tables)

class ReachApi(Resource):
    def model_api(self) -> dict:
#        """
#        Class method that retrieves data from hobolink and usgs and processes
#        data, then creates json-like dictionary structure for model output.
#
#        returns: json-like dictionary
#        """
        
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

    @swag_from('reachapi.yml')
    def get(self):
        return self.model_api()

api.add_resource(ReachApi, '/api/v1/model')
