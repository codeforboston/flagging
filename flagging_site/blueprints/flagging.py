from typing import Any
from typing import Dict
import pandas as pd

from flask import Blueprint
from flask import render_template
from flask import request
from flask import current_app
from flask import flash

from ..data.boathouses import Boathouse
from ..data.predictive_models import latest_model_outputs
from ..data.boathouses import get_latest_time
from ..data.live_website_options import LiveWebsiteOptions


bp = Blueprint('flagging', __name__)


@bp.before_request
def before_request():
    # Get the latest time shown in the database
    ltime = get_latest_time()

    # Get current time from the computer clock
    ttime = pd.Timestamp.now()

    # Calculate difference between now and d.b. time
    diff = ttime - ltime

    # If more than 48 hours, flash message.
    if diff >= pd.Timedelta(48, 'hr'):
        flash('<b>Note:</b> The database has not updated in at least 48 '
              'hours. The information displayed on this page may be outdated.')

    # ~~~

    if not LiveWebsiteOptions.is_boating_season():
        msg = '<b>Note:</b> It is currently not boating season. '
        if request.path.startswith('/flags'):
            # If the path is the iframe...
            msg += (
                'We do not display flags when it is not boating season. We '
                'hope to see you again this spring!'
            )
        else:
            msg += (
                'We may update our database and (consequently) our predictive '
                'model while it is not boating season, but these model outputs '
                'are not intended to be used to make decisions regarding '
                'recreational activities along the Charles River.'
            )
        flash(msg)


def get_flags(df: pd.DataFrame = None) -> Dict[str, bool]:
    """
    Get a dict of boolean values indicating whether each boathouse is considered
    safe. True means it is considered safe-- otherwise it is false.

    Args:
        df: (pd.DataFrame) Pandas Dataframe containing predictive model outputs.

    Returns:
        Dict of booleans.
    """
    if df is None:
        df = latest_model_outputs()
    # sql equivalent: SELECT * FROM boathouses ORDER BY boathouse
    all_boathouses = (
        Boathouse.query
        .order_by(Boathouse.boathouse)
        .all()
    )

    def _reach_is_safe(r: int) -> bool:
        return df.loc[df['reach'] == r, 'safe'].iloc[0]

    flag_statuses = {}

    for row in all_boathouses:
        # Check to see if the reach is safe AND the row has not been overridden.
        # If both are true, then the boathouse gets a blue flag.
        # Otherwise, give it a red flag.
        flag_statuses[row.boathouse] = \
             _reach_is_safe(row.reach) and (not row.overridden)

    return flag_statuses


def flag_widget_params() -> Dict[str, Any]:
    """Creates the parameters for the flags widget.

    Pass these parameters into a Jinja template like this:

    >>> **flag_widget_params()
    """
    df = latest_model_outputs()
    return dict(
        flags=get_flags(df=df),
        model_last_updated_time=df['time'].iloc[0],
        boating_season=LiveWebsiteOptions.is_boating_season(),
        flagging_message=LiveWebsiteOptions.get_flagging_message()
    )


def stylize_model_output(df: pd.DataFrame) -> str:
    """
    This function function stylizes the dataframe that we will output for our
    web page. This function replaces the bools with colorized values, and then
    returns the HTML of the table excluding the index.

    Args:
        df: (pd.DataFrame) Pandas Dataframe containing predictive model outputs.

    Returns:
        HTML table.
    """
    df = df.copy()

    def _apply_flag(x: bool) -> str:
        flag_class = 'blue-flag' if x else 'red-flag'
        return f'<span class="{flag_class}">{x}</span>'

    df['safe'] = df['safe'].apply(_apply_flag)
    df.columns = [i.title().replace('_', ' ') for i in df.columns]

    # remove reach number
    df = df.drop(columns=['Reach'])

    return df.to_html(index=False, escape=False)


@bp.route('/')
def index() -> str:
    """
    The home page of the website. This page contains a brief description of the
    purpose of the website, and the latest outputs for the flagging model.
    """
    return render_template('index.html', **flag_widget_params())


@bp.route('/boathouses')
def boathouses() -> str: 
    all_boathouses_dict = Boathouse.all_boathouses_dict()

    # Convert list of dicts to list of lists
    #
    # The parent list lists all boathouses.
    # Each element of the parent list is a child list.
    # The elements of the child list are:
    #     element 0:  a decimal value showing the boathouse's latitude
    #     element 1:  a decimal value showing the boathouse's longitude
    #     element 2:  a string showing the boathouse name

    #     Note that latitudes west of the Prime Meridian are positive 
    #         (thus those east of the Prime Meridian are negative)
    #     Longitudes north of the Equator are negative
    #         (thus those south of the Equator are positive)
    flag_statuses = get_flags()

    boathouses_list_of_lists = []
    for boathouse in all_boathouses_dict:
        bh_name = boathouse['boathouse']
        boathouses_list_of_lists.append([
            boathouse['latitude'],
            boathouse['longitude'],
            bh_name,
            'blueFlag' if flag_statuses[bh_name] else 'redFlag'
        ])

    return render_template('boathouses.html',
                           boathouses_list_of_lists=boathouses_list_of_lists)


@bp.route('/about')
def about() -> str:
    return render_template('about.html')


@bp.route('/model_outputs')
def model_outputs() -> str:
    """
    Retrieves data from hobolink and usgs, processes that data, and then
    displays the data as a human-readable, stylized HTML table.

    Returns:
        Rendering of the model outputs via the `model_outputs.html` template.
    """
    df = latest_model_outputs(hours=24)

    reach_html_tables = {
        r: stylize_model_output(df.loc[df['reach'] == r])
        for r
        in df['reach'].unique()
    }

    boathouses_by_reach = Boathouse.boathouse_names_by_reach()

    return render_template('model_outputs.html',
                           tables=reach_html_tables,
                           boathouses_by_reach=boathouses_by_reach)


@bp.route('/flags')
def flags() -> str:
    return render_template('flags.html', **flag_widget_params())


@bp.route('/api')
def api_index() -> str:
    """Landing page for the API."""
    return render_template('api/index.html')
