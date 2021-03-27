from typing import Any
from typing import Dict
import pandas as pd

from flask import Blueprint
from flask import current_app
from flask import render_template
from flask import flash

from ..data.boathouses import Boathouse
from ..data.database import cache
from ..data.database import get_current_time
from ..data.predictive_models import get_latest_prediction_time
from ..data.predictive_models import latest_model_outputs
from ..data.live_website_options import LiveWebsiteOptions


bp = Blueprint('flagging', __name__)


@bp.before_request
@cache.cached()  # <-- needs to be here. some issues occur if you exclude it.
def before_request():
    last_pred_time = get_latest_prediction_time()
    current_time = get_current_time()

    # Calculate difference between now and latest prediction time
    diff = current_time - last_pred_time

    # If more than 48 hours, flash message.
    if current_app.env == 'demo':
        flash(
            'This website is currently in demo mode. It is not using live data.'
        )
    elif diff >= pd.Timedelta(48, 'hr'):
        flash(
            '<b>Note:</b> The database has not updated in at least 48 hours. '
            'The information displayed on this page may be outdated.'
        )

    # ~ ~ ~

    if not LiveWebsiteOptions.is_boating_season():
        flash(
            '<b>Note:</b> It is currently not boating season. We do not '
            'display flags when it is not boating season. We hope to see you '
            'again in the near future!'
        )


def flag_widget_params(force_display: bool = False) -> Dict[str, Any]:
    """Creates the parameters for the flags widget.

    Pass these parameters into a Jinja template like this:

    >>> **flag_widget_params()
    """
    return dict(
        flags=Boathouse.all_flags(),
        model_last_updated_time=get_latest_prediction_time(),
        boating_season=force_display or LiveWebsiteOptions.is_boating_season(),
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

    # remove reach number
    df = df.drop(columns=['reach'])

    def _apply_flag(x: bool) -> str:
        flag_class = 'blue-flag' if x else 'red-flag'
        return f'<span class="{flag_class}">{x}</span>'

    df['safe'] = df['safe'].apply(_apply_flag)
    df.columns = [i.title().replace('_', ' ') for i in df.columns]

    return df.to_html(index=False, escape=False)


@bp.route('/')
@cache.cached()
def index() -> str:
    """
    The home page of the website. This page contains a brief description of the
    purpose of the website, and the latest outputs for the flagging model.
    """
    return render_template('index.html', **flag_widget_params())


@bp.route('/boathouses')
@cache.cached()
def boathouses() -> str:
    return render_template('boathouses.html', **flag_widget_params(force_display=True))


@bp.route('/about')
@cache.cached()
def about() -> str:
    return render_template('about.html')


@bp.route('/model')
@cache.cached()
def model_outputs() -> str:
    """
    Parses the model outputs in a human readable format. It also gets the
    boathouses by reach, so the user knows what boathouses are associated with
    each reach.

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
@bp.route('/flags/<int:version>')
@cache.cached()
def flags(version: int = None) -> str:
    return render_template('flags.html',
                           **flag_widget_params(),
                           version=version)


@bp.route('/api')
@cache.cached()
def api_index() -> str:
    """Landing page for the API."""
    return render_template('api/index.html')
