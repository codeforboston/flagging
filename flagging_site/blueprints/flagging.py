import pandas as pd

from flask import Blueprint
from flask import render_template
from flask import request
from flask import current_app

from ..data.hobolink import get_live_hobolink_data
from ..data.usgs import get_live_usgs_data
from ..data.model import process_data
from ..data.model import latest_model_outputs

bp = Blueprint('flagging', __name__)


def get_data() -> pd.DataFrame:
    """Retrieves the processed data that gets plugged into the the model."""
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

    # remove reach number
    df = df.drop('Reach', 1)

    return df.to_html(index=False, escape=False)


@bp.route('/')
def index() -> str:
    """
    The home page of the website. This page contains a brief description of the
    purpose of the website, and the latest outputs for the flagging model.
    """
    
    df = latest_model_outputs()
    df = df.set_index('reach')
    flags = {
        key: val['safe']
        for key, val
        in df.to_dict(orient='index').items()
    }
    
    homepage = {
        2: {
            'flag': flags[2],
            'boathouses': [
                'Newton Yacht Club',
                'Watertown Yacht Club',
                'Community Rowing, Inc.',
                'Northeastern\'s Henderson Boathouse', 
                'Paddle Boston at Herter Park'
            ]
        },
        3: {
            'flag': flags[3],
            'boathouses': [
                'Harvard\'s Weld Boathouse'
            ]
        },
        4: {
            'flag': flags[4],
            'boathouses': [
                'Riverside Boat Club'
            ]
        },
        5: {
            'flag': flags[5],
            'boathouses': [
                'Charles River Yacht Club', 
                'Union Boat Club', 
                'Community Boating', 
                'Paddle Boston at Kendall Square'
            ]
        }
    }

    model_last_updated_time = df['time'].iloc[0]

    return render_template('index.html', homepage=homepage, model_last_updated_time=model_last_updated_time)


@bp.route('/about')
def about() -> str:
    return render_template('about.html')


@bp.route('/output_model', methods=['GET'])
def output_model() -> str:
    """
    Retrieves data from hobolink and usgs, processes that data, and then
    displays the data as a human-readable, stylized HTML table.

    Returns:
        Rendering of the model outputs via the `output_model.html` template.
    """

    # Parse contents of the query string to get reach and hours parameters.
    # Defaults are hours = 24, and reach = -1.
    # When reach = -1, we utilize all reaches.
    reach = request.args.get('reach', -1, type=int)
    hours = request.args.get('hours', 24, type=int)

    # Look at no more than x_MAX_HOURS
    hours = min(max(hours, 1), current_app.config['API_MAX_HOURS'])

    df = latest_model_outputs(hours)

    # reach_html_tables is a dict where the index is the reach number
    # and the values are HTML code for the table of data to display for
    # that particular reach
    reach_html_tables = {}

    # loop through each reach in df
    #    compare with reach to determine whether to display that reach
    #       extract the subset from the df for that reach
    #       then convert that df subset to HTML code
    #       and then add that HTML subset to reach_html_tables
    for i in df.reach.unique():
        if (reach==-1 or reach==i):
            reach_html_tables[i] = stylize_model_output(  df.loc[df['reach'] == i ]  )
    
    return render_template('output_model.html', tables=reach_html_tables)
