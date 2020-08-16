import pandas as pd
from flask import Blueprint
from flask import render_template
from flask import request
from flask import current_app

from ..data.hobolink import get_live_hobolink_data
from ..data.usgs import get_live_usgs_data
from ..data.model import process_data
from ..data.model import reach_2_model
from ..data.model import reach_3_model
from ..data.model import reach_4_model
from ..data.model import reach_5_model

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

    return df.to_html(index=False, escape=False)


@bp.route('/')
def index() -> str:
    """
    The home page of the website. This page contains a brief description of the
    purpose of the website, and the latest outputs for the flagging model.

    Returns:
        The website's home page with the latest flag updates.
    """
    df = get_data()
    
    homepage = {
        2: {
            'flag': reach_2_model(df, rows=1)['safe'].iloc[0],
            'boathouses': [
                'Newton Yacht Club',
                'Watertown Yacht Club',
                'Community Rowing, Inc.',
                'Northeastern\s Henderson Boathouse', 
                'Paddle Boston at Herter Park'
            ]
        },
        3: {
            'flag': reach_3_model(df, rows=1)['safe'].iloc[0],
            'boathouses': [
                'Harvard\'s Weld Boathouse'
            ]
        },
        4: {
            'flag': reach_4_model(df, rows=1)['safe'].iloc[0],
            'boathouses': [
                'Riverside Boat Club'
            ]
        },
        5: {
            'flag': reach_5_model(df, rows=1)['safe'].iloc[0],
            'boathouses': [
                'Charles River Yacht Club', 
                'Union Boat Club', 
                'Community Boating', 
                'Paddle Boston at Kendall Square'
            ]
        }
    }

    model_last_updated_time = reach_5_model(df, rows=1)['time'].iloc[0]

    return render_template('index.html', homepage=homepage, model_last_updated_time=model_last_updated_time)
    # return render_template('index.html', flags=flags)
    


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
